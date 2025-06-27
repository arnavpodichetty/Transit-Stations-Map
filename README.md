**Download files from these sources as geojson:** 

- gis.data.ca.gov/datasets/9509bf8a475f49b4a9c79bac15f8b479_0/explore?location=33.498716%2C-117.211321%2C9.24
- https://gisdata-caltrans.opendata.arcgis.com/datasets/dd7cb74665a14859a59b8c31d3bc5a3e_0/about 
- https://catalog.data.gov/dataset/intermodal-passenger-connectivity-database-ipcd3
- https://data.ca.gov/dataset/low-income-or-disadvantaged-communities-designated-by-california

**Run:**

- start by running ca_filter.py (filters the routes file and markers file for california only )
- then run convert_geojson_to_json.py (makes all the json files from geojson)
- then run app.py

For route_type:
- 3 is bus
- 2 is rail
- 4 is ferry
- 1 bart/light rail
- 5 is cable car
- 0 some sort of light rail (vta), sfo transit, sf night bus, LA Metro, 

Running app:
- have npm or install
- npm install
- cd into the app and then npm run dev
