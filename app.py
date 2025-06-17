import os
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv
import json

# -------------------------------
# CONFIGURATION
# -------------------------------
load_dotenv()
app = Flask(__name__)
STATION_JSON_PATH = "data/data.json"

@app.route("/api/stations")
def get_stations():
    with open(STATION_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    filters = {}

    if request.args.get("state"):
        filters["state"] = request.args["state"].upper()

    if request.args.get("mode"):
        mode_field = f"mode_{request.args['mode'].lower()}"
        filters[mode_field] = 1

    filtered = []
    for station in data:
        if filters.get("state") and station.get("state") != filters["state"]:
            continue
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

@app.route("/api/maps")
def get_maps_script():
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    return (
        f'''
        const script = document.createElement("script");
        script.src = "https://maps.googleapis.com/maps/api/js?key={key}&callback=initMap";
        script.async = true;
        document.body.appendChild(script);
        ''',
        200,
        {'Content-Type': 'application/javascript'}
    )

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)

if __name__ == "__main__":
    app.run()
