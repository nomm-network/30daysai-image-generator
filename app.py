from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import requests
from io import BytesIO
import base64
import os

app = Flask(__name__)
CORS(app)

def create_gradient_background(size, color1=(0,0,0,180), color2=(0,0,0,0)):
    """Create a gradient background for text"""
    background = Image.new('RGBA', size, (0,0,0,0))
    draw = ImageDraw.Draw(background)
    for y in range(size[1]):
        alpha = int((1 - y/size[1]) * color1[3] + (y/size[1]) * color2[3])
        draw.line([(0,y), (size[0],y)], fill=(color1[0], color1[1], color1[2], alpha))
    return background

@app.route('/process-image', methods=['POST'])
def process_image():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        image_url = data.get('image_url')
        business_name = data.get('business_name')
        hashtags = data.get('hashtags', [])

        if not image_url or not business_name:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400

        # Download the image
        response = requests.get(image_url)
        if response.status_code != 200:
            return jsonify({'success': False, 'error': 'Failed to download image'}), 400

        # Open and process the image
        img = Image.open(BytesIO(response.content)).convert('RGBA')
        
        # Create a drawing object
        draw = ImageDraw.Draw(img)

        # Load fonts (adjust paths based on your environment)
        try:
            business_font = ImageFont.truetype("Arial Bold.ttf", 48)
            hashtag_font = ImageFont.truetype("Arial.ttf", 24)
        except:
            # Fallback to default font if custom font not available
            business_font = ImageFont.load_default()
            hashtag_font = ImageFont.load_default()

        # Colors
        business_color = "#9b87f5"  # Purple
        hashtag_color = "#D6BCFA"  # Light purple
        
        # Add business name at the top
        padding = 20
        # Get text size for background
        text_bbox = draw.textbbox((0, 0), business_name, font=business_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Create gradient background for business name
        gradient_height = text_height + padding * 2
        gradient = create_gradient_background(
            (img.width, gradient_height),
            (0, 0, 0, 180),  # Start color (semi-transparent black)
            (0, 0, 0, 0)     # End color (transparent)
        )
        img.paste(gradient, (0, 0), gradient)

        # Add business name with shadow effect
        shadow_offset = 2
        # Draw shadow
        draw.text(
            (padding + shadow_offset, padding + shadow_offset),
            business_name,
            font=business_font,
            fill="black"
        )
        # Draw main text
        draw.text(
            (padding, padding),
            business_name,
            font=business_font,
            fill=business_color
        )

        # Add hashtags at the bottom
        if hashtags:
            # Create gradient background for hashtags
            hashtag_gradient_height = (len(hashtags) * 30) + padding * 2
            bottom_gradient = create_gradient_background(
                (img.width, hashtag_gradient_height),
                (0, 0, 0, 0),     # Start color (transparent)
                (0, 0, 0, 180)    # End color (semi-transparent black)
            )
            img.paste(
                bottom_gradient,
                (0, img.height - hashtag_gradient_height),
                bottom_gradient
            )

            # Add hashtags
            y_position = img.height - hashtag_gradient_height + padding
            for hashtag in hashtags:
                # Add hashtag with shadow
                draw.text(
                    (padding + 1, y_position + 1),
                    f"#{hashtag}",
                    font=hashtag_font,
                    fill="black"
                )
                draw.text(
                    (padding, y_position),
                    f"#{hashtag}",
                    font=hashtag_font,
                    fill=hashtag_color
                )
                y_position += 30

        # Convert to RGB for JPEG saving
        img = img.convert('RGB')
        
        # Save to BytesIO
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=95)
        
        # Convert to base64
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'image': f'data:image/jpeg;base64,{img_str}'
        })

    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
