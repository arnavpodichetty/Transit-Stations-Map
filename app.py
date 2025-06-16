import os
from pathlib import Path
import geopandas as gpd
import json
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from pymongo import MongoClient

# -------------------------------
# CONFIGURATION
# -------------------------------
load_dotenv()

CSV_PATH = "data/NTAD_Intermodal_Passenger_Connectivity_Database_3388733903903323304.csv"
GEOJSON_PATH = "data/California_Transit_Routes.geojson"
BOTTLENECK_PATH = "data/Bottlenecks.geojson"
LOWINCOME_PATH = "data/Low_income.geojson"


BOTTLENECK_JSON_OUT = Path("data/bottlenecks.json")
JSON_OUT = Path("data/data.json")
ROUTES_JSON_OUT = Path("data/routes.json")
LOWINCOME_JSON_OUT = Path("data/low_income.json")


MONGO_URI = os.getenv("MONGO_URI")

DB_NAME = "transit_data"
STATIONS_COLL = "stations"
ROUTES_COLL = "routes"
BOTTLE_COLL = "bottlenecks"
LOWINCOME_COLL = "lowincome"

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

df = df[df["state"].str.upper() == "CA"]

for col in ["mode_bus", "mode_air", "mode_rail", "mode_ferry", "mode_bike"]:
    df[col] = df[col].fillna(0).astype(int)

df = df.dropna(subset=["latitude", "longitude"])

JSON_OUT.parent.mkdir(exist_ok=True)
df = df.where(pd.notnull(df), None)  # Replace NaN with None
df.to_json(JSON_OUT, orient="records")  # Now it's valid JSON
print(f"✅ Saved {len(df):,} rows to {JSON_OUT}")

# -------------------------------
# LOAD AND PROCESS GEOJSON DATA (ROUTES)
# -------------------------------
if Path(GEOJSON_PATH).exists():
    # Load GeoJSON using geopandas for better handling
    routes_gdf = gpd.read_file(GEOJSON_PATH)
    
    # Convert to regular dataframe with geometry as text for JSON serialization
    routes_df = pd.DataFrame(routes_gdf.drop(columns='geometry'))
    routes_df['geometry'] = routes_gdf['geometry'].apply(lambda x: x.__geo_interface__)
    
    # Add any additional processing here
    # For example, standardize route_type values
    if 'route_type' in routes_df.columns:
        routes_df['route_type'] = routes_df['route_type'].fillna('unknown')
    
    # Save processed routes as JSON
    routes_data = routes_df.to_dict('records')
    with open(ROUTES_JSON_OUT, 'w') as f:
        json.dump(routes_data, f)
    
    print(f"✅ Saved {len(routes_df):,} route records to {ROUTES_JSON_OUT}")
else:
    print(f"⚠️  GeoJSON file not found at {GEOJSON_PATH}")
    routes_data = []

# -------------------------------
# LOAD AND PROCESS BOTTLENECKS DATA
# -------------------------------
if Path(BOTTLENECK_PATH).exists():
    bottleneck_gdf = gpd.read_file(BOTTLENECK_PATH)
    
    bottleneck_df = pd.DataFrame(bottleneck_gdf.drop(columns='geometry'))
    bottleneck_df['geometry'] = bottleneck_gdf['geometry'].apply(lambda x: x.__geo_interface__)
    
    bottleneck_data = bottleneck_df.to_dict('records')
    with open(BOTTLENECK_JSON_OUT, 'w') as f:
        json.dump(bottleneck_data, f)
    bottleneck_df = bottleneck_df.where(pd.notnull(bottleneck_df), None)
    print(f"✅ Saved {len(routes_df):,} route records to {BOTTLENECK_JSON_OUT}")
else:
    print(f"⚠️  GeoJSON file not found at {BOTTLENECK_PATH}")
    bottleneck_data = []

# -------------------------------
# LOAD AND PROCESS LOW INCOME DATA
# -------------------------------
if Path(LOWINCOME_PATH).exists():
    lowincome_gdf = gpd.read_file(LOWINCOME_PATH)
    
    lowincome_df = pd.DataFrame(lowincome_gdf.drop(columns='geometry'))
    lowincome_df['geometry'] = lowincome_gdf['geometry'].apply(lambda x: x.__geo_interface__)
    
    lowincome_data = lowincome_df.to_dict('records')
    with open(LOWINCOME_JSON_OUT, 'w') as f:
        json.dump(lowincome_data, f)
    lowincome_df = lowincome_df.where(pd.notnull(lowincome_df), None)
    print(f"✅ Saved {len(routes_df):,} route records to {LOWINCOME_JSON_OUT}")
else:
    print(f"⚠️  GeoJSON file not found at {LOWINCOME_PATH}")
    lowincome_data = []

# -------------------------------
# MONGODB LOAD
# -------------------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Load stations
stations_coll = db[STATIONS_COLL]
stations_coll.delete_many({})
stations_coll.insert_many(df.to_dict("records"))
print(f"✅ Inserted {stations_coll.count_documents({}):,} stations into MongoDB")

# Load routes
if routes_data:
    routes_coll = db[ROUTES_COLL]
    routes_coll.delete_many({})
    routes_coll.insert_many(routes_data)
    print(f"✅ Inserted {routes_coll.count_documents({}):,} routes into MongoDB")

# Load bottlenecks
if bottleneck_data:
    bottleneck_coll = db[BOTTLE_COLL]
    bottleneck_coll.delete_many({})
    bottleneck_coll.insert_many(bottleneck_data)
    print(f"✅ Inserted {bottleneck_coll.count_documents({}):,} bottlenecks into MongoDB")

if lowincome_data:
    lowincome_coll = db[LOWINCOME_COLL]
    lowincome_coll.delete_many({})
    lowincome_coll.insert_many(lowincome_data)
    print(f"✅ Inserted {lowincome_coll.count_documents({}):,} lowincome into MongoDB")

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

    results = list(stations_coll.find(filters, {"_id": 0}))
    return jsonify(results)

@app.route("/api/routes")
def get_routes():
    filters = {}
    
    # Filter by route type
    if request.args.get("route_type"):
        filters["route_type"] = request.args["route_type"]
    
    # Filter by state (if route data has state info)
    if request.args.get("state"):
        filters["state"] = request.args["state"].upper()
    
    # Filter by agency or operator
    if request.args.get("agency"):
        filters["agency_name"] = {"$regex": request.args["agency"], "$options": "i"}
    
    results = list(routes_coll.find(filters, {"_id": 0}))
    return jsonify(results)

@app.route("/api/routes/geojson")
def get_routes_geojson():
    """Return routes in GeoJSON format for direct map consumption"""
    filters = {}
    
    if request.args.get("route_type"):
        filters["route_type"] = request.args["route_type"]
    
    if request.args.get("state"):
        filters["state"] = request.args["state"].upper()
    
    routes = list(routes_coll.find(filters, {"_id": 0}))
    
    # Convert back to GeoJSON format
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": route["geometry"],
                "properties": {k: v for k, v in route.items() if k != "geometry"}
            }
            for route in routes
        ]
    }
    
    return jsonify(geojson)

@app.route("/api/bottle")
def get_bottle():
    results = list(bottleneck_coll.find({}, {"_id": 0}))
    return jsonify(results)

@app.route("/api/bottle/geojson")
def get_bottle_geojson():
    bottlenecks = list(bottleneck_coll.find({}, {"_id": 0}))
    
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": b["geometry"],
                "properties": {k: v for k, v in b.items() if k != "geometry"}
            }
            for b in bottlenecks
        ]
    }
    
    return jsonify(geojson)

@app.route("/api/lowincome")
def get_lowincome():
    results = list(lowincome_coll.find({}, {"_id": 0}))
    return jsonify(results)

@app.route("/api/lowincome/geojson")
def get_lowincome_geojson():
    lowincome = list(lowincome_coll.find({}, {"_id": 0}))
    
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": b["geometry"],
                "properties": {k: v for k, v in b.items() if k != "geometry"}
            }
            for b in lowincome
        ]
    }
    
    return jsonify(geojson)

@app.route("/api/combined")
def get_combined_data():
    """Get stations and nearby routes in one call"""
    station_filters = {}
    route_filters = {}
    
    # Apply common filters
    if request.args.get("state"):
        state = request.args["state"].upper()
        station_filters["state"] = state
        route_filters["state"] = state
    
    stations = list(stations_coll.find(station_filters, {"_id": 0}))
    routes = list(routes_coll.find(route_filters, {"_id": 0}))
    bottlenecks = list(bottleneck_coll.find(route_filters, {"_id": 0}))
    lowincome = list(lowincome_coll.find(route_filters, {"_id": 0}))
    
    return jsonify({
        "stations": stations,
        "routes": routes,
        "bottlenecks": bottlenecks,
        "lowincome": lowincome
    })

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

# -------------------------------
# Run server
# -------------------------------
if __name__ == "__main__":
    app.run()
