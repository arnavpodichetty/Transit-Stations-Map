import pandas as pd
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from pymongo import MongoClient
from pathlib import Path

# -------------------------------
# CONFIGURATION
# -------------------------------
load_dotenv()
CSV_PATH = "data/NTAD_Intermodal_Passenger_Connectivity_Database_3388733903903323304.csv"
JSON_OUT = Path("data/data.json")
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "transit_data"
COLL_NAME = "stations"

# -------------------------------
# LOAD AND CLEAN CSV DATA
# -------------------------------
df = pd.read_csv(CSV_PATH)
df.columns = df.columns.str.lower()

keep_cols = [
    "fac_id", "fac_name", "address", "city", "state", "zipcode",
    "x", "y", "fac_type",
    "mode_bus", "mode_air", "mode_rail", "mode_ferry", "mode_bike",
    "website", "notes"
]

missing = [col for col in keep_cols if col not in df.columns]
if missing:
    raise ValueError(f"Missing expected columns: {missing}")

df = df[keep_cols].rename(columns={
    "fac_id": "station_id",
    "x": "longitude",
    "y": "latitude",
    "fac_type": "mode_type"
})

for col in ["mode_bus", "mode_air", "mode_rail", "mode_ferry", "mode_bike"]:
    df[col] = df[col].fillna(0).astype(int)

df = df.dropna(subset=["latitude", "longitude"])

JSON_OUT.parent.mkdir(exist_ok=True)
df.to_json(JSON_OUT, orient="records")
print(f"✅ Saved {len(df):,} rows to {JSON_OUT}")

# -------------------------------
# MONGODB LOAD
# -------------------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
coll = db[COLL_NAME]

# Drop + reload (for development convenience)
coll.delete_many({})
coll.insert_many(df.to_dict("records"))
print(f"✅ Inserted {coll.count_documents({}):,} stations into MongoDB")

# -------------------------------
# FLASK API SETUP
# -------------------------------
app = Flask(__name__)

@app.route("/api/stations")
def get_stations():
    filters = {}

    if request.args.get("state"):
        filters["state"] = request.args["state"].upper()

    if request.args.get("mode"):
        mode_field = f"mode_{request.args['mode'].lower()}"
        filters[mode_field] = 1

    results = list(coll.find(filters, {"_id": 0}))
    return jsonify(results)

@app.route("/api/maps")
def get_maps_script():
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    return f'''
      const script = document.createElement("script");
      script.src = "https://maps.googleapis.com/maps/api/js?key={key}&callback=initMap";
      script.async = true;
      document.body.appendChild(script);
    ''', 200, {'Content-Type': 'application/javascript'}

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)

# -------------------------------
# Run server
# -------------------------------
if __name__ == "__main__":
    app.run()
