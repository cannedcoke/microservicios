# Imports and dependencies
from flask import Flask, jsonify, request
import requests
from functools import wraps
import jwt
import time
from database import create_delivery

# configuracion y constantes

app = Flask(__name__)

URL_ORDERS = "http://localhost:5002"
KEY = "whatever"

# circuit breaker, evitar errores en cascada
BREAKER = {
    "state": "CLOSED",
    "failures": 0,
    "opened_at": None
}

FAILURE_THRESHOLD = 3
RECOVERY_TIME = 30


# manejo las requests a  travez del circuit breaker
def orders_request(url, headers=None):
    now = time.time()

    if BREAKER["state"] == "OPEN":
        if now - BREAKER["opened_at"] < RECOVERY_TIME:
            raise Exception("circuit open")
        else:
            BREAKER["state"] = "HALF_OPEN"

    try:
        response = requests.get(url, headers=headers, timeout=2)

        if response.status_code >= 500:
            raise Exception("orders service error")

        BREAKER["state"] = "CLOSED"
        BREAKER["failures"] = 0
        BREAKER["opened_at"] = None

        return response

    except Exception:
        if BREAKER["state"] == "HALF_OPEN":
            BREAKER["state"] = "OPEN"
            BREAKER["opened_at"] = now
            BREAKER["failures"] = FAILURE_THRESHOLD
        else:
            BREAKER["failures"] += 1
            if BREAKER["failures"] >= FAILURE_THRESHOLD:
                BREAKER["state"] = "OPEN"
                BREAKER["opened_at"] = now

        raise


# valida jwt
def require_jwt(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"error": "missing token"}), 401

        try:
            jwt.decode(token, KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "invalid token"}), 401

        return f(*args, **kwargs)

    return wrapper


# crea delivery, checkea que este confirmada
@app.route("/delivery", methods=["POST"])
@require_jwt
def create_delivery_route():
    data = request.get_json()

    order_id = data.get("order_id")
    address = data.get("address")

    if not order_id or not address:
        return jsonify({"error": "missing data"}), 400

    token = request.headers.get("Authorization")
    headers = {"Authorization": token} if token else {}

    try:
        response = orders_request(f"{URL_ORDERS}/orders/{order_id}", headers=headers)
    except Exception:
        return jsonify({"error": "orders service unavailable"}), 503

    if response.status_code == 404:
        return jsonify({"error": "order not found"}), 404

    if response.status_code != 200:
        return jsonify({"error": "orders service error"}), 503

    order = response.json()

    if order["status"] != "confirmed":
        return jsonify({"error": "order not ready for delivery"}), 400

    delivery_id = create_delivery(order_id, address)

    return jsonify({
        "delivery_id": delivery_id,
        "order_id": order_id,
        "status": "assigned"
    }), 201


# inicia 
if __name__ == "__main__":
    app.run(port=5003)
