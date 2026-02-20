from flask import Flask, jsonify, request
from functools import wraps
import requests
import jwt
import time
from datetime import datetime, timedelta
from database import (
    create_order,
    add_order_item,
    get_order_by_id,
    update_order_status
)

# configuracion de la aplicacion y constantes
app = Flask(__name__)
KEY = "whatever"
URL_RESTAURANT = "http://localhost:5001"

# Circuit breaker 
BREAKER = {
    "state": "CLOSED",
    "failures": 0,
    "opened_at": None
}

FAILURE_THRESHOLD = 3
RECOVERY_TIME = 30


# est afuncion maneja las requests a travez del circuit breaker
def restaurant_request(url):
    now = time.time()

    if BREAKER["state"] == "OPEN":
        if now - BREAKER["opened_at"] < RECOVERY_TIME:
            raise Exception("circuit open")
        else:
            BREAKER["state"] = "HALF_OPEN"

    try:
        r = requests.get(url, timeout=2)
        if r.status_code != 200:
            raise Exception("bad response")

        BREAKER["state"] = "CLOSED"
        BREAKER["failures"] = 0
        BREAKER["opened_at"] = None
        return r

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


# validacion de tokens jwt
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


# este ednpoint es para crear las ordenes
@app.route("/orders", methods=["POST"])
def create_order_route():
    data = request.get_json()
    restaurant_id = data.get("restaurant_id")
    items = data.get("items")

    if not restaurant_id or not items:
        return jsonify({"error": "invalid order data"}), 400

    token = jwt.encode(
        {"exp": datetime.utcnow() + timedelta(hours=1)},
        KEY,
        algorithm="HS256"
    )

    try:
        restaurant_request(f"{URL_RESTAURANT}/restaurants")
    except Exception:
        return jsonify({"error": "restaurant service unavailable"}), 503

    try:
        m = restaurant_request(
            f"{URL_RESTAURANT}/restaurants/{restaurant_id}/menu"
        )
    except Exception:
        return jsonify({"error": "menu unavailable"}), 503

    menu = {}

    data = m.json()

    for item in data:
        product_id = item["product_id"]
        menu[product_id] = item

    total = 0
    order_items = []
    for i in items:
        product_id = i["product_id"]
        quantity = i["quantity"]
        if product_id not in menu or not menu[product_id]["disponible"]:
            return jsonify({"error": f"product {product_id} not available"}), 400

        price = float(menu[product_id]["price"])
        total += price * quantity
        order_items.append((product_id, quantity, price))

    order_id = create_order(restaurant_id, total)

    for product_id, quantity, price in order_items:
        add_order_item(order_id, product_id, quantity, price)

    return jsonify({
        "order_id": order_id,
        "total": total,
        "status": "created",
        "token": token
    }), 201


# esto obtiene la orden por id
@app.route("/orders/<int:order_id>", methods=["GET"])
@require_jwt 
def get_order_route(order_id):
    order = get_order_by_id(order_id)
    if not order:
        return jsonify({"error": "order not found"}), 404

    return jsonify(order), 200


# actualiza el estado de las ordenes
@app.route("/orders/<int:order_id>", methods=["PUT"])
@require_jwt
def update_order_route(order_id):
    data = request.get_json()
    status = data.get("status")

    if status not in ["created", "confirmed", "cancelled"]:
        return jsonify({"error": "invalid status"}), 400

    updated = update_order_status(order_id, status)
    if not updated:
        return jsonify({"error": "order not found"}), 404

    return jsonify({
        "order_id": order_id,
        "status": status
    }), 200


# inicializa en el puert0 5002
if __name__ == "__main__":
    app.run(port=5002)
