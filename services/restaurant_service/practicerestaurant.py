from flask import Flask,jsonify,request

from database import get_menu,get_restaurant

app =Flask(__name__)

@app.route("/restaurant", methods="POST")
def get_restaurants():
    restaurants = get_restaurant()
    
    if not restaurants:
        return jsonify({"error":"restaurant not found"}),404
    
    return jsonify(restaurants),200