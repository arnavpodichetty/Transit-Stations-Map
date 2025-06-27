# Transit Map Application

A full-stack web application for visualizing California transit data with interactive maps showing routes, stations, bottlenecks, and low-income areas.

## Quick Start

### Prerequisites
- Python 3.7+
- Node.js and npm
- Google Maps API key

### Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file in the root directory:
   ```
   VITE_GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
   VITE_GOOGLE_MAPS_ID=your_map_id_here
   ```

3. **Prepare data files:**
   
   Place your GeoJSON data files in the `app/public/data/` directory:
   - `routes.json` - Transit route data
   - `bottlenecks.json` - Traffic bottleneck data  
   - `low_income.json` - Low-income area data
   - `data.json` - Station data (if using stations)

4. **Run the application:**
   ```bash
   python run_dev.py
   ```

The script will:
- Install npm dependencies automatically
- Start both Flask backend (port 5000) and React frontend (port 5173)
- Open your browser to the application

## Development Modes

When you run `python run_dev.py`, you can choose:

1. **Development mode** (default): Runs both Flask API server and React dev server separately
   - React dev server: http://localhost:5173 (with hot reload)
   - Flask API server: http://localhost:5000

2. **Production mode**: Builds React app and serves it through Flask
   - Single server: http://localhost:5000

## Route Types

- **Type 0**: Light rail (VTA, SFO Transit, SF Night Bus, LA Metro)
- **Type 1**: BART/Light rail
- **Type 2**: Rail
- **Type 3**: Bus
- **Type 4**: Ferry
- **Type 5**: Cable car

## Project Structure

```
├── app/                    # React frontend
│   ├── src/
│   ├── public/
│   │   └── data/          # JSON data files
│   └── package.json
├── app.py                 # Flask backend
├── run_dev.py            # Unified development server
└── requirements.txt      # Python dependencies
```

## Manual Setup (Alternative)

If you prefer to run components separately:

1. **Start Flask backend:**
   ```bash
   python app.py
   ```

2. **Start React frontend (in another terminal):**
   ```bash
   cd app
   npm install
   npm run dev
   ```

## Features

- Interactive Google Maps with California transit data
- Filter by route types, states, and transportation modes
- Toggle layers for routes, bottlenecks, and low-income areas
- Responsive design with modern UI
- Real-time data filtering and visualization

## Data Sources

The application expects JSON data files in the `app/public/data/` directory. You can obtain transit data from:

- [California Transit Routes](https://gis.data.ca.gov/datasets/9509bf8a475f49b4a9c79bac15f8b479_0/explore)
- [Traffic Bottlenecks](https://gisdata-caltrans.opendata.arcgis.com/datasets/dd7cb74665a14859a59b8c31d3bc5a3e_0/about)
- [Intermodal Passenger Connectivity](https://catalog.data.gov/dataset/intermodal-passenger-connectivity-database-ipcd3)
- [Low-Income Communities](https://data.ca.gov/dataset/low-income-or-disadvantaged-communities-designated-by-california)

## Troubleshooting

- **Google Maps not loading**: Check your API key in the `.env` file
- **Data not showing**: Ensure your JSON data files are in `app/public/data/`
- **Port conflicts**: The script will show which ports are being used (5000 for Flask, 5173 for React)
- **npm not found**: Ensure Node.js and npm are installed and in your system PATH

## Environment Variables

Create a `.env` file in the root directory with:

```
VITE_GOOGLE_MAPS_API_KEY=your_actual_api_key_here
VITE_GOOGLE_MAPS_ID=your_map_id_here
```

Replace the placeholder values with your actual Google Maps API credentials.