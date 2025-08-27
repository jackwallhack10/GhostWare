from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "API is running!"

@app.route("/hello")
def hello():
    return jsonify({"message": "Hello Roblox!"})
