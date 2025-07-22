# Transit Map App

A web app to explore California transit data with routes, stations, bottlenecks, low-income areas, and an AI chat assistant.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   cd app && npm install
   ```
2. **Add a `.env` file** in the root:
   ```
   VITE_GOOGLE_MAPS_API_KEY=your_google_maps_api_key
   VITE_GOOGLE_MAPS_ID=your_map_id
   ```
3. **Add data files** to `app/public/data/` (see below).

## Running

**Development (live reload):**
- In one terminal:  
  `python app.py`  
- In another:  
  `cd app && npm run dev`
- Visit: [http://localhost:5173](http://localhost:5173)

**Production:**
- Build React:  
  `cd app && npm run dev`
- Start Flask:  
  `python app.py`
- Visit: [http://localhost:5173](http://localhost:5173)

## Data Files
Place these in `app/public/data/`:
- `routes.json` (transit routes)
- `bottlenecks.json` (traffic bottlenecks)
- `low_income.json` (low-income areas)
- `data.json` (stations, optional)

## Features
- Interactive Google Map with transit layers
- Filter by route type, state, and mode
- Toggle bottlenecks and low-income areas
- **AI Assistant:** Ask questions about the map (Gemini-powered)

## AI Assistant
- Click the 🤖 button to chat about routes, bottlenecks, or transit info.
- Example: "What do the route colors mean?" or "Where are the biggest bottlenecks?"

## Data Sources
- [California Transit Routes](https://gis.data.ca.gov/datasets/9509bf8a475f49b4a9c79bac15f8b479_0/explore)
- [Traffic Bottlenecks](https://gisdata-caltrans.opendata.arcgis.com/datasets/dd7cb74665a14859a59b8c31d3bc5a3e_0/about)
- [Intermodal Passenger Connectivity](https://catalog.data.gov/dataset/intermodal-passenger-connectivity-database-ipcd3)
- [Low-Income Communities](https://data.ca.gov/dataset/low-income-or-disadvantaged-communities-designated-by-california)

---
For more details, see comments in the code. Enjoy exploring transit data!