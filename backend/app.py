# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

@app.route('/api/convert', methods=['POST'])
def convert_file():
    print("Endpoint /api/convert foi chamado!")
    return jsonify({"message": "Olá do servidor Flask!"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)