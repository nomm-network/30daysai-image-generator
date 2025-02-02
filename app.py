from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import requests
from io import BytesIO
import base64
import os
import uuid

app = Flask(__name__)
CORS(app)

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(SCRIPT_DIR, 'fonts')

# Ensure the fonts directory exists
os.makedirs(FONT_DIR, exist_ok=True)

def resize_logo(logo_img, main_image_width):
    """Resize logo to be 15% of the main image width"""
    target_width = int(main_image_width * 0.15)  # 15% of main image width
    aspect_ratio = logo_img.width / logo_img.height
    target_height = int(target_width / aspect_ratio)
    return logo_img.resize((target_width, target_height), Image.LANCZOS)

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
        business_logo_url = data.get('business_logo_url')
        hashtags = data.get('hashtags', [])
        supabase_url = data.get('supabase_url')
        supabase_key = data.get('supabase_key')

        if not image_url or not business_name or not supabase_url or not supabase_key:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400

        print(f"Processing request with image_url: {image_url}")
        print(f"Business name: {business_name}")
        print(f"Logo URL: {business_logo_url}")
        print(f"Hashtags: {hashtags}")

        # Download and process the main image
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content)).convert('RGBA')
        except Exception as e:
            print(f"Error processing main image: {str(e)}")
            return jsonify({'success': False, 'error': f'Failed to process image: {str(e)}'}), 400

        # Load fonts - Updated font URLs
        try:
            business_font = ImageFont.truetype(os.path.join(FONT_DIR, 'Roboto-Bold.ttf'), 48)
            hashtag_font = ImageFont.truetype(os.path.join(FONT_DIR, 'Roboto-Regular.ttf'), 32)
        except:
            print("Font loading error - downloading fonts...")
            font_urls = {
                'Roboto-Bold.ttf': 'https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Bold.ttf',
                'Roboto-Regular.ttf': 'https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Regular.ttf'
            }
            
            for font_name, font_url in font_urls.items():
                font_path = os.path.join(FONT_DIR, font_name)
                if not os.path.exists(font_path):
                    try:
                        font_response = requests.get(font_url, timeout=10)
                        font_response.raise_for_status()
                        with open(font_path, 'wb') as f:
                            f.write(font_response.content)
                    except Exception as e:
                        print(f"Error downloading font {font_name}: {str(e)}")
                        return jsonify({'success': False, 'error': f'Failed to download font {font_name}: {str(e)}'}), 500
            
            business_font = ImageFont.truetype(os.path.join(FONT_DIR, 'Roboto-Bold.ttf'), 48)
            hashtag_font = ImageFont.truetype(os.path.join(FONT_DIR, 'Roboto-Regular.ttf'), 32)

        draw = ImageDraw.Draw(img)
        padding = 20
        logo_height = 0

        # Process logo if provided
        if business_logo_url:
            try:
                logo_response = requests.get(business_logo_url, timeout=10)
                logo_response.raise_for_status()
                logo = Image.open(BytesIO(logo_response.content)).convert('RGBA')
                logo = resize_logo(logo, img.width)
                img.paste(logo, (padding, padding), logo)
                logo_height = logo.height
            except Exception as e:
                print(f"Error processing logo: {str(e)}")

        # Add business name and hashtags
        text_y = padding + logo_height + (padding if logo_height > 0 else 0)
        text_bbox = draw.textbbox((0, 0), business_name, font=business_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Create gradient backgrounds and add text
        gradient_height = text_height + padding * 2
        gradient = create_gradient_background(
            (img.width, gradient_height + text_y),
            (0, 0, 0, 180),
            (0, 0, 0, 0)
        )
        img.paste(gradient, (0, 0), gradient)

        # Add business name with shadow
        draw.text(
            (padding + 3, text_y + 3),
            business_name,
            font=business_font,
            fill=(0, 0, 0, 160)
        )
        draw.text(
            (padding, text_y),
            business_name,
            font=business_font,
            fill="#000205"
        )

        # Add hashtags
        if hashtags:
            hashtag_gradient_height = 80
            bottom_gradient = create_gradient_background(
                (img.width, hashtag_gradient_height),
                (0, 0, 0, 0),
                (0, 0, 0, 180)
            )
            img.paste(
                bottom_gradient,
                (0, img.height - hashtag_gradient_height),
                bottom_gradient
            )

            hashtag_texts = [f"#{tag}" for tag in hashtags]
            total_width = sum(draw.textlength(text, font=hashtag_font) for text in hashtag_texts)
            spacing = (img.width - 2 * padding - total_width) / (len(hashtags) - 1) if len(hashtags) > 1 else 0
            
            x_position = padding
            y_position = img.height - hashtag_gradient_height + padding
            
            for hashtag in hashtag_texts:
                draw.text(
                    (x_position + 2, y_position + 2),
                    hashtag,
                    font=hashtag_font,
                    fill=(0, 0, 0, 140)
                )
                draw.text(
                    (x_position, y_position),
                    hashtag,
                    font=hashtag_font,
                    fill="#000205"
                )
                x_position += draw.textlength(hashtag, font=hashtag_font) + spacing

        # Convert to RGB and save
        img = img.convert('RGB')
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=95)
        
        # Upload to Supabase storage
        headers = {
            'Authorization': f'Bearer {supabase_key}',
            'apikey': supabase_key
        }
        
        filename = f"{uuid.uuid4()}.jpg"
        upload_url = f"{supabase_url}/storage/v1/object/media-sets-images/{filename}"
        
        files = {
            'file': ('image.jpg', buffered.getvalue(), 'image/jpeg')
        }
        
        upload_response = requests.post(upload_url, headers=headers, files=files)
        if upload_response.status_code != 200:
            print(f"Upload error: {upload_response.text}")
            return jsonify({'success': False, 'error': 'Failed to upload to storage'}), 500

        # Get the public URL
        public_url = f"{supabase_url}/storage/v1/object/public/media-sets-images/{filename}"
        
        return jsonify({
            'success': True,
            'url': public_url
        })

    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
