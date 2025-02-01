from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import os

app = Flask(__name__)
CORS(app)

@app.route('/process-image', methods=['POST'])
def process_image():
    try:
        data = request.json
        image_url = data.get('image_url')
        
        # Download image
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        
        # Add text
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Hello", fill="black")
        
        # Save to BytesIO
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format=img.format)
        img_byte_arr.seek(0)
        
        return jsonify({
            "success": True,
            "message": "Image processed successfully",
            "data": img_byte_arr.getvalue()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
