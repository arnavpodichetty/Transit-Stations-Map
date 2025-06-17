import json
from pathlib import Path

# Define California bounds
CA_BOUNDS = {
    "min_lat": 32.5,
    "max_lat": 42.0,
    "min_lng": -124.5,
    "max_lng": -114.0
}

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

# File paths
input_path = Path("data/California_Transit_Routes.geojson")
output_path = Path("data/California_Only_Strict.geojson")

# Load and filter
with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

features = data.get("features", [])
filtered = [f for f in features if feature_strictly_in_ca(f)]

# Write output
output_path.parent.mkdir(exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump({
        "type": "FeatureCollection",
        "features": filtered
    }, f, separators=(",", ":"))

print(f"✅ Filtered {len(filtered)} out of {len(features)} features to {output_path}")
