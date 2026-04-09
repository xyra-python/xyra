from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "Hello, World!"})

@app.route("/text")
def text_endpoint():
    return "Hello, World!", 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route("/html")
def html_endpoint():
    return "<h1>Hello, World!</h1>", 200, {'Content-Type': 'text/html; charset=utf-8'}
