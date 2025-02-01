from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from PIL import Image, ImageDraw
from io import BytesIO
import requests
import base64

app = Flask(__name__)
CORS(app)

@app.route('/process-image', methods=['POST'])
def process_image():
    try:
        # Get image URL from request
        data = request.get_json()
        if not data or 'imageUrl' not in data:
            return jsonify({'success': False, 'error': 'No image URL provided'}), 400

        image_url = data['imageUrl']

        # Download the image
        response = requests.get(image_url)
        if response.status_code != 200:
            return jsonify({'success': False, 'error': 'Failed to download image'}), 400

        # Open image with PIL
        img = Image.open(BytesIO(response.content))

        # Add text
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Hello", fill="black")

        # Save to BytesIO
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        
        # Convert to base64
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return jsonify({
            'success': True,
            'image': img_str
        })

    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
