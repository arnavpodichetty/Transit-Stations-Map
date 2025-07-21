import os
import numpy as np
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv
import json
from flask_cors import CORS
import requests
import torch
import clip
from PIL import Image
import io

# -------------------------------
# CONFIGURATION
# -------------------------------
load_dotenv()
app = Flask(__name__, static_folder='app/dist', static_url_path='/')

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://localhost:5001"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

STATION_JSON_PATH = "app/public/data/data.json" 
GEMINI_API_KEY = "AIzaSyD5I4gvumrOMtea6kUMh49zIO35A4EBYSM"

UPLOAD_FOLDER = 'transit_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# CLIP Model Setup
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

class EmbeddingStore:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingStore, cls).__new__(cls)
            cls._instance.embeddings = np.zeros((0, 512))  # Initialize empty array
            cls._instance.image_info = []  # Stores filenames
        return cls._instance

# Initialize the store
embedding_store = EmbeddingStore()

@app.route('/api/upload_transit_image', methods=['POST'])
def upload_transit_image():
    """Admin endpoint to upload transit images"""
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    try:
        # Save image
        filename = f"transit_{len(embedding_store.image_info)}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Generate and store embedding
        image = preprocess(Image.open(filepath)).unsqueeze(0).to(device)
        with torch.no_grad():
            embedding = model.encode_image(image).cpu().numpy()
        
        # Update storage
        embedding_store.embeddings = np.vstack([embedding_store.embeddings, embedding])
        embedding_store.image_info.append({"filename": filename})
        
        return jsonify({
            "status": "success",
            "filename": filename,
            "embedding_shape": embedding.shape
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai-chat", methods=['POST'])
def ai_chat():
    """
    Proxy endpoint for Gemini AI chat to avoid CORS issues.
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        map_context = data.get('mapContext', {})
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        # Prepare the prompt with map context
        prompt = f"""You are an AI assistant for a transit stations map. The map shows:
- Transit routes with different types (0-5) in different colors
- Bottlenecks in the transit system
- Low-income areas

Current map state:
- Routes visible: {map_context.get('showRoutes', False)}
- Bottlenecks visible: {map_context.get('showBottlenecks', False)}
- Low-income areas visible: {map_context.get('showLowIncome', False)}
- Active route types: {map_context.get('activeRouteTypes', '')}

User question: {user_message}

Please provide helpful, informative answers about the transit map, routes, bottlenecks, low-income areas, or general transit information. Keep responses concise and relevant to the map data."""

        # Make request to Gemini API
        gemini_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro-002:generateContent?key={GEMINI_API_KEY}"
        
        response = requests.post(gemini_url, json={
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('candidates') and data['candidates'][0].get('content'):
                ai_response = data['candidates'][0]['content']['parts'][0]['text']
                return jsonify({"response": ai_response})
            else:
                return jsonify({"error": "Invalid response from Gemini API"}), 500
        else:
            return jsonify({"error": f"Gemini API error: {response.status_code}"}), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timeout"}), 408
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/stations")
def get_stations():
    """
    API endpoint to return filtered station data.
    Filters by state, mode, and name if provided in query parameters.
    """
    try:
        with open(STATION_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return jsonify({"error": "Station data file not found."}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Error decoding station data JSON."}), 500

    filters = {}

    # Extract filters from query parameters
    if request.args.get("state"):
        filters["state"] = request.args["state"].upper()

    if request.args.get("mode"):
        mode_field = f"mode_{request.args['mode'].lower()}"
        filters[mode_field] = 1  # Assuming 1 means "has this mode"

    filtered = []
    for station in data:
        # Apply state filter
        if filters.get("state") and station.get("state") != filters["state"]:
            continue

        # Apply mode filters
        if "mode_bus" in filters and station.get("mode_bus") != 1:
            continue
        if "mode_air" in filters and station.get("mode_air") != 1:
            continue
        if "mode_rail" in filters and station.get("mode_rail") != 1:
            continue
        if "mode_ferry" in filters and station.get("mode_ferry") != 1:
            continue
        if "mode_bike" in filters and station.get("mode_bike") != 1:
            continue

        filtered.append(station)

    return jsonify(filtered)

# Serve the React app's index.html for the root route
@app.route('/')
def serve_react_app():
    """Serves the main index.html file from the React build."""
    return send_from_directory(app.static_folder, 'index.html')

# Serve all other static files (JS, CSS, images, and data files copied by Vite)
@app.route('/<path:filename>')
def serve_static_files(filename):
    """Serves static files like JS, CSS, images, and data from the React build."""
    return send_from_directory(app.static_folder, filename)

@app.route("/api/match_photo", methods=["POST"])
def match_photo():
    try:
        if 'photo' not in request.files:
            return jsonify({"error": "No photo uploaded"}), 400
        
        # Secure filename handling
        file = request.files['photo']
        if file.filename == '':
            return jsonify({"error": "Empty filename"}), 400
        
        try:
            # Verify image before processing
            image = Image.open(io.BytesIO(file.read()))
            if image.format not in ('JPEG', 'PNG'):
                return jsonify({"error": "Invalid image format"}), 400
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
            # Process image
            image_tensor = preprocess(image).unsqueeze(0).to(device)
            with torch.no_grad():
                query_embedding = clip_model.encode_image(image_tensor).cpu().numpy()
            
            if not embeddings.size:
                return jsonify({"error": "No reference images available"}), 404
                
            # Calculate similarities
            query_embedding_norm = query_embedding / np.linalg.norm(query_embedding)
            embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            similarities = np.dot(embeddings_norm, query_embedding_norm.T).flatten()
            
            best_idx = np.argmax(similarities)
            
            return jsonify({
                "matched_image": image_info[best_idx]["filename"],
                "similarity_score": float(similarities[best_idx])
            })
            
        except IOError:
            return jsonify({"error": "Invalid image file"}), 400
        except Exception as e:
            print(f"Image processing error: {str(e)}")
            return jsonify({"error": "Image processing failed"}), 500
            
    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({"error": "Server error"}), 500


if __name__ == "__main__":
    print(f"Serving React app from: {app.static_folder}")
    print(f"Looking for station data at: {STATION_JSON_PATH}")
    app.run(debug=True, port=5001, host='0.0.0.0')