# Imports and dependencies
from flask import Flask, jsonify
from database import get_menu, get_restaurant

app = Flask(__name__)


# este endpoint retorna  los restaurantes
@app.route("/restaurants", methods=["GET"])
def get_restaurants():
    restaurants = get_restaurant()

    if not restaurants:
        return jsonify({"error": "restaurant not found"}), 404

    return jsonify(restaurants), 200


# restorna el menu de un restaurante especifico
@app.route("/restaurants/<int:restaurant_id>/menu", methods=["GET"])
def get_restaurant_menu(restaurant_id):
    
    menu = get_menu(restaurant_id)

    if not menu:
        return jsonify({"error": "menu not found"}), 404

    formatted_menu = []

    for item in menu:
        formatted_menu.append({
            "product_id": item["id_item"],
            "name": item["nombre"],
            "price": item["price"],
            "disponible": item["disponible"]
        })

    return jsonify(formatted_menu), 200


# inicia la app
if __name__ == "__main__":
    app.run(port=5001)
