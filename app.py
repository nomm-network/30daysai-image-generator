from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "Image generator service is running"})

@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    try:
        # Basic endpoint structure - we'll add image generation logic later
        return jsonify({"status": "success", "message": "Endpoint ready for image generation"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

