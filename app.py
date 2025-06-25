import os
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv
import json

# -------------------------------
# CONFIGURATION
# -------------------------------
load_dotenv()
app = Flask(__name__, static_folder='my-map-app/dist', static_url_path='/')

# Path to your original station data JSON file (Flask will read this)
# Make sure this path is correct relative to where you run app.py
STATION_JSON_PATH = "app/public/data/data.json" # Assuming 'data' folder is next to app.py

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
        # Map modes to their respective numeric flags (assuming this is how your data is structured)
        # Note: Your JS uses 'bus', 'air', etc. directly, not 'mode_bus'.
        # We'll need to adapt the React frontend to send correct API params if needed,
        # or simplify this backend logic if filters are applied client-side anyway.
        # For now, let's keep it as per your original app.py logic.
        mode_field = f"mode_{request.args['mode'].lower()}"
        filters[mode_field] = 1 # Assuming 1 means "has this mode"

    # Client-side search for 'name' will be handled in React's `updateStationMarkers` logic
    # as the backend is designed for specific `mode_field` filters.

    filtered = []
    for station in data:
        # Apply state filter
        if filters.get("state") and station.get("state") != filters["state"]:
            continue

        # Apply mode filters (these are mutually exclusive in the filter logic provided)
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

# --- Removed @app.route("/api/maps") as it's handled directly by React's index.html ---

# Serve the React app's index.html for the root route
@app.route('/')
def serve_react_app():
    """Serves the main index.html file from the React build."""
    # This route will primarily be used in production after `npm run build`
    # In development, Vite's dev server handles '/'
    return send_from_directory(app.static_folder, 'index.html')

# Serve all other static files (JS, CSS, assets, and data files copied by Vite)
@app.route('/<path:filename>')
def serve_static_files(filename):
    """Serves static files like JS, CSS, images, and data from the React build."""
    # This catches all other files that Vite has placed in the dist folder,
    # including your data files (routes.json, bottlenecks.json, low_income.json)
    # if they are copied from public/data during the Vite build.
    return send_from_directory(app.static_folder, filename)

if __name__ == "__main__":
    # Ensure the 'data' folder with data.json is next to app.py
    # or adjust STATION_JSON_PATH accordingly.
    print(f"Serving React app from: {app.static_folder}")
    print(f"Looking for station data at: {STATION_JSON_PATH}")
    app.run(debug=True, port=5000) # Using port 5000 for Flask by default