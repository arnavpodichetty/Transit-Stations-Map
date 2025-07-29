import os
from flask import Blueprint, Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv
import google.generativeai as genai
import json
from dotenv import load_dotenv
from flask_cors import CORS  # Add this line to handle CORS
import requests  # Add this for making HTTP requests to Gemini API

# -------------------------------
# CONFIGURATION
# -------------------------------
load_dotenv()
app = Flask(__name__, static_folder='app/dist', static_url_path='/')

CORS(app)

STATION_JSON_PATH = "app/public/data/data.json" 

routes_bp = Blueprint('routes', __name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@routes_bp.route('/suggest-routes', methods=['POST'])
def suggest_routes():
    # Load geo data
    data = request.get_json()
    map_context = data.get('mapContext', {})

    prompt = f"""
You are a transit planner AI. Your job is to suggest up to 3 new transit corridors to address:

- Bottlenecks (high vehicle delay)
- Low-income areas (with no transit coverage)
- Better equity and mobility

Only suggest routes that:
- Connect areas with bottlenecks to improve traffic flow
- Serve underserved low-income zones that currently have no transit
- Avoid areas that already have transit

- Routes: {map_context.get('showRoutes', False)}
- Bottlenecks: {map_context.get('showBottlenecks', False)}
- Low-income areas: {map_context.get('showLowIncome', False)}

Please respond with valid raw JSON only (do not use markdown or backticks). 
Provide 2-3 new suggestions. For each write it in a json format as below. Keep summaries 1 sentence. 
[
    "name": "Equity Express",
    "summary": "Connects Riverwood to Downtown to improve access and reduce congestion.",
    "start": [34.031, -118.195],
    "end": [34.052, -118.243]
]
"""

    model = genai.GenerativeModel("gemini-2.5-pro")
    models = genai.list_models()
    for m in models:
        print(m.name)
    
    response = model.generate_content(prompt)

    return jsonify({"suggestions": response.text})

app.register_blueprint(routes_bp, url_prefix='/api')

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

if __name__ == "__main__":
    print(f"Serving React app from: {app.static_folder}")
    print(f"Looking for station data at: {STATION_JSON_PATH}")
    app.run(debug=True, port=5001, host='0.0.0.0')