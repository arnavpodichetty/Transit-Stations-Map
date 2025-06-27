import json
from pathlib import Path
import pandas as pd

# -------------------------------
# CONSTANTS
# -------------------------------
CA_BOUNDS = {
    "min_lat": 32.5,
    "max_lat": 42.0,
    "min_lng": -124.5,
    "max_lng": -114.0
}

# File paths
BASE_DIR = Path("app/public/data")
GEOJSON_PATH_ROUTES_RAW = BASE_DIR / "California_Transit_Routes.geojson"
GEOJSON_PATH_MARKERS_RAW = BASE_DIR / "NTAD_Intermodal_Passenger_Connectivity_Database_-3991686045944498549.geojson"
GEOJSON_PATH_ROUTES = BASE_DIR / "California_Only_Strict.geojson"
GEOJSON_PATH_STATIONS = BASE_DIR / "Markers_California_Only_Strict.geojson"
JSON_OUT_STATIONS = BASE_DIR / "data.json"
JSON_OUT_ROUTES = BASE_DIR / "routes.json"
JSON_OUT_BOTTLENECKS = BASE_DIR / "bottlenecks.json"
JSON_OUT_LOWINCOME = BASE_DIR / "low_income.json"
GEOJSON_PATH_BOTTLENECKS = BASE_DIR / "Bottlenecks.geojson"
GEOJSON_PATH_LOWINCOME = BASE_DIR / "Low_Income.geojson"

# -------------------------------
# FILTER FUNCTIONS
# -------------------------------
def all_coords_in_ca(coords):
    return all(CA_BOUNDS["min_lng"] <= lng <= CA_BOUNDS["max_lng"] and
               CA_BOUNDS["min_lat"] <= lat <= CA_BOUNDS["max_lat"]
               for lng, lat in coords)

def feature_strictly_in_ca(feature):
    geom = feature.get("geometry", {})
    coords = geom.get("coordinates", [])
    geom_type = geom.get("type")

    if geom_type == "LineString":
        return all_coords_in_ca(coords)
    elif geom_type == "MultiLineString":
        return all(all_coords_in_ca(segment) for segment in coords)
    return False

def marker_in_california(marker):
    return marker.get("properties", {}).get("STATE") == "CA"

# -------------------------------
# FILTER GEOJSON FILES
# -------------------------------
def filter_and_save_geojson(input_path, output_path, filter_func):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    features = data.get("features", [])
    filtered = [f for f in features if filter_func(f)]
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": filtered}, f, separators=(",", ":"))
    print(f"✅ Filtered {len(filtered)} out of {len(features)} features to {output_path}")
    return filtered

# Filter transit routes and station markers
filter_and_save_geojson(GEOJSON_PATH_ROUTES_RAW, GEOJSON_PATH_ROUTES, feature_strictly_in_ca)
filter_and_save_geojson(GEOJSON_PATH_MARKERS_RAW, GEOJSON_PATH_STATIONS, marker_in_california)

# -------------------------------
# CLEAN STATION DATA
# -------------------------------
with open(GEOJSON_PATH_STATIONS, "r", encoding="utf-8") as f:
    geo = json.load(f)

records = []
for f in geo["features"]:
    props = f.get("properties", {})
    coords = f.get("geometry", {}).get("coordinates", [None, None])
    record = {
        "station_id": props.get("FAC_ID"),
        "fac_name": props.get("FAC_NAME"),
        "address": props.get("ADDRESS"),
        "city": props.get("CITY"),
        "state": props.get("STATE"),
        "zipcode": props.get("ZIPCODE"),
        "longitude": coords[0],
        "latitude": coords[1],
        "mode_type": props.get("FAC_TYPE"),
        "mode_bus": int(props.get("MODE_BUS") or 0),
        "mode_air": int(props.get("MODE_AIR") or 0),
        "mode_rail": int(props.get("MODE_RAIL") or 0),
        "mode_ferry": int(props.get("MODE_FERRY") or 0),
        "mode_bike": int(props.get("MODE_BIKE") or 0),
        "website": props.get("WEBSITE"),
        "notes": props.get("NOTES")
    }
    if record["latitude"] is not None and record["longitude"] is not None:
        records.append(record)

JSON_OUT_STATIONS.parent.mkdir(exist_ok=True)
pd.DataFrame(records).to_json(JSON_OUT_STATIONS, orient="records")
print(f"✅ Saved {len(records):,} station records to {JSON_OUT_STATIONS}")

# -------------------------------
# CLEAN ROUTE DATA
# -------------------------------
with open(GEOJSON_PATH_ROUTES, "r", encoding="utf-8") as f:
    route_geo = json.load(f)

route_records = []
for feat in route_geo["features"]:
    props = feat.get("properties", {})
    geometry = feat.get("geometry", {})
    route_records.append({
        "route_id": props.get("route_id"),
        "route_short_name": props.get("route_short_name"),
        "route_long_name": props.get("route_long_name"),
        "route_type": props.get("route_type"),
        "coordinates": geometry.get("coordinates"),
        "geometry_type": geometry.get("type")
    })

with open(JSON_OUT_ROUTES, "w", encoding="utf-8") as f:
    json.dump(route_records, f, separators=(",", ":"))
print(f"✅ Saved {len(route_records):,} route records to {JSON_OUT_ROUTES}")

# -------------------------------
# CLEAN BOTTLENECK DATA
# -------------------------------
with open(GEOJSON_PATH_BOTTLENECKS, "r", encoding="utf-8") as f:
    bottleneck_geo = json.load(f)

bottleneck_records = []
for feat in bottleneck_geo["features"]:
    props = feat.get("properties", {})
    geometry = feat.get("geometry", {})
    bottleneck_records.append({
        "name": props.get("Name"),
        "rank": props.get("Rank"),
        "county": props.get("County"),
        "direction": props.get("Direction"),
        "delay_hours": props.get("Total_Delay__veh_hrs_"),
        "extent_miles": props.get("Avg_Extent__Miles_"),
        "shape_length": props.get("Shape_Length"),
        "coordinates": geometry.get("coordinates"),
        "geometry_type": geometry.get("type")
    })

with open(JSON_OUT_BOTTLENECKS, "w", encoding="utf-8") as f:
    json.dump(bottleneck_records, f, separators=(",", ":"))
print(f"✅ Saved {len(bottleneck_records):,} bottleneck records to {JSON_OUT_BOTTLENECKS}")

# -------------------------------
# CLEAN LOW-INCOME DATA
# -------------------------------
with open(GEOJSON_PATH_LOWINCOME, "r", encoding="utf-8") as f:
    low_income_geo = json.load(f)

low_income_records = []
for feat in low_income_geo["features"]:
    props = feat.get("properties", {})
    geometry = feat.get("geometry", {})
    low_income_records.append({
        "geoid": props.get("GEOID"),
        "tract": props.get("NAMELSAD"),
        "county": props.get("County"),
        "zip": props.get("ZIP"),
        "population": props.get("Population"),
        "poverty_pct": props.get("Poverty"),
        "ci_score": props.get("CIscore"),
        "dac_status": props.get("DAC_and_or_LIC"),
        "income_group": props.get("Income_Group"),
        "coordinates": geometry.get("coordinates"),
        "geometry_type": geometry.get("type")
    })

with open(JSON_OUT_LOWINCOME, "w", encoding="utf-8") as f:
    json.dump(low_income_records, f, separators=(",", ":"))
print(f"✅ Saved {len(low_income_records):,} low-income tract records to {JSON_OUT_LOWINCOME}")
