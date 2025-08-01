import React, { useEffect, useRef, useState } from 'react';
import './App.css';

function TransitMap() {
  const mapRef = useRef(null);
  const googleMap = useRef(null);
  
  // Map data refs - MUST be declared first
  const polylines = useRef([]);
  const bottleneckLines = useRef([]);
  const lowIncomePolygons = useRef([]);
  const allRoutes = useRef([]);
  const routeLayerLoaded = useRef(false);
  
  // State management
  const [isMapLoaded, setIsMapLoaded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filters state
  const [stateFilter, setStateFilter] = useState('');
  const [modeFilter, setModeFilter] = useState('');
  const [routeTypes, setRouteTypes] = useState({
    '0': true, '1': true, '2': true, '3': true, '4': true, '5': true
  });
  
  // Dropdown state
  const [isRouteDropdownOpen, setIsRouteDropdownOpen] = useState(false);
  
  // Layer toggles
  const [showRoutes, setShowRoutes] = useState(true);
  const [showBottlenecks, setShowBottlenecks] = useState(false);
  const [showLowIncome, setShowLowIncome] = useState(false);

  const [suggestedRoutesText, setSuggestedRoutesText] = useState('');
  const [isLoadingSuggestion, setIsLoadingSuggestion] = useState(false);
  const [aiSuggestedRoutes, setAiSuggestedRoutes] = useState([]);
  const aiRouteLines = useRef([]);
  const aiStartMarkers = useRef([]);



  const MAP_ID = import.meta.env.VITE_GOOGLE_MAPS_ID;
  const GEMINI_API_KEY = import.meta.env.GEMINI_API_KEY;

  // Load Google Maps Script
  const loadGoogleMapsScript = () => {
    if (window.google) {
      console.log("Google Maps already loaded");
      setIsMapLoaded(true);
      return;
    }

    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
    console.log("API Key from env:", apiKey ? 'Found' : 'NOT FOUND');
    
    if (!apiKey) {
      setError('Google Maps API key not found. Check your .env file.');
      setLoading(false);
      return;
    }

    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places`;
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);

    script.onload = () => {
      console.log("Google Maps script loaded successfully");
      setIsMapLoaded(true);
      setLoading(false);
    };

    script.onerror = () => {
      console.error("Failed to load Google Maps script");
      setError('Failed to load Google Maps API');
      setLoading(false);
    };
  };

  // Clear polylines
  const clearPolylines = () => {
    polylines.current.forEach(p => p.setMap(null));
    polylines.current = [];
  };

  // Draw routes
  const drawRoutes = (routesToDraw) => {
    const colorMap = {
      "0": "#a65628", "1": "#e41a1c", "2": "#377eb8", 
      "3": "#4daf4a", "4": "#984ea3", "5": "#ff7f00"
    };

    routesToDraw.forEach(route => {
      const coords = route.coordinates;
      if (!coords || coords.length === 0) return;

      const paths = [];

      if (route.geometry_type === "LineString") {
        paths.push(coords.map(c => ({ lat: c[1], lng: c[0] })));
      } else if (route.geometry_type === "MultiLineString") {
        coords.forEach(seg => paths.push(seg.map(c => ({ lat: c[1], lng: c[0] }))));
      }

      paths.forEach(path => {
        const polyline = new window.google.maps.Polyline({
          path,
          map: googleMap.current,
          strokeColor: colorMap[route.route_type] || "#888",
          strokeOpacity: 1.0,
          strokeWeight: 2
        });
        polylines.current.push(polyline);
      });
    });
  };

  // Filter and draw routes
  const filterAndDrawRoutes = () => {
    clearPolylines();

    const checkedRouteTypes = Object.keys(routeTypes).filter(key => routeTypes[key]);

    if (checkedRouteTypes.length === 0 || !allRoutes.current || allRoutes.current.length === 0) {
      return;
    }

    const filteredRoutes = allRoutes.current.filter(route => {
      return checkedRouteTypes.includes(String(route.route_type));
    });

    drawRoutes(filteredRoutes);
  };

  // Load routes from JSON
  const loadRoutesLayer = async () => {
    try {
      const response = await fetch('/data/routes.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}: Routes data not found`);
      const routes = await response.json();
      allRoutes.current = routes;
      routeLayerLoaded.current = true;
      filterAndDrawRoutes();
      console.log("Routes loaded successfully");
    } catch (err) {
      console.warn('Could not load routes data:', err.message);
    }
  };

  // Draw bottlenecks
  const drawBottlenecks = async () => {
    try {
      const response = await fetch('/data/bottlenecks.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}: Bottlenecks data not found`);
      const bottlenecks = await response.json();

      bottlenecks.forEach(bn => {
        const color = "#ff7f00";
        const paths = [];

        if (bn.geometry_type === "LineString") {
          paths.push(bn.coordinates.map(c => ({ lat: c[1], lng: c[0] })));
        } else if (bn.geometry_type === "MultiLineString") {
          bn.coordinates.forEach(seg => paths.push(seg.map(c => ({ lat: c[1], lng: c[0] }))));
        }

        paths.forEach(path => {
          const polyline = new window.google.maps.Polyline({
            path,
            map: googleMap.current,
            strokeColor: color,
            strokeOpacity: 0.9,
            strokeWeight: 4,
            zIndex: 1
          });

          polyline.set("info", {
            name: bn.name,
            county: bn.county,
            rank: bn.rank,
            delay: bn.delay_hours
          });

          polyline.addListener("click", (e) => {
            const info = polyline.get("info");
            new window.google.maps.InfoWindow({
              content: `<b>${info.name}</b><br>County: ${info.county}<br>Rank: ${info.rank}<br>Total Delay: ${info.delay} veh-hrs`,
              position: e.latLng
            }).open(googleMap.current);
          });

          bottleneckLines.current.push(polyline);
        });
      });
      console.log("Bottlenecks loaded successfully");
    } catch (err) {
      console.warn('Could not load bottlenecks data:', err.message);
    }
  };

  // Draw low income areas
  const drawLowIncomeAreas = async () => {
    try {
      const response = await fetch('/data/low_income.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}: Low income data not found`);
      const tracts = await response.json();

      tracts.forEach(area => {
        const paths = [];

        if (area.geometry_type === "Polygon") {
          paths.push(area.coordinates[0].map(c => ({ lat: c[1], lng: c[0] })));
        } else if (area.geometry_type === "MultiPolygon") {
          area.coordinates.forEach(polygon => {
            paths.push(polygon[0].map(c => ({ lat: c[1], lng: c[0] })));
          });
        }

        paths.forEach(path => {
          const polygon = new window.google.maps.Polygon({
            paths: path,
            strokeColor: "#8e44ad",
            strokeOpacity: 0.8,
            strokeWeight: 1.5,
            fillColor: "#8e44ad",
            fillOpacity: 0.2,
            map: googleMap.current
          });

          polygon.set("info", {
            geoid: area.geoid,
            county: area.county,
            tract: area.name,
            poverty: area.poverty_pct,
            ci_score: area.ci_score
          });

          polygon.addListener("click", (e) => {
            const info = polygon.get("info");
            new window.google.maps.InfoWindow({
              content: `<b>${info.tract}</b><br>County: ${info.county}<br>Poverty: ${info.poverty}%<br>CI Score: ${info.ci_score}`,
              position: e.latLng
            }).open(googleMap.current);
          });

          lowIncomePolygons.current.push(polygon);
        });
      });
      console.log("Low income areas loaded successfully");
    } catch (err) {
      console.warn('Could not load low income data:', err.message);
    }
  };

  // Initialize map
  const initializeMap = async () => {
    console.log("=== MAP INITIALIZATION DEBUG ===");
    console.log("1. mapRef.current exists:", !!mapRef.current);
    console.log("2. window.google exists:", !!window.google);
    
    if (!googleMap.current && mapRef.current && window.google) {
      try {
        console.log("3. Creating Google Map...");
        
        googleMap.current = new window.google.maps.Map(mapRef.current, {
          center: { lat: 36.7783, lng: -119.4179 },
          zoom: 6,
        });
        
        console.log("4. Map created successfully");

        // Force a resize event to make sure map renders
        setTimeout(() => {
          console.log("5. Triggering map resize...");
          window.google.maps.event.trigger(googleMap.current, 'resize');
        }, 100);

        // Load only routes initially
        if (showRoutes) {
          loadRoutesLayer();
        }
        
        console.log("6. Map initialization completed");
      } catch (error) {
        console.error("ERROR creating map:", error);
        setError("Failed to create map: " + error.message);
      }
    }
  };

  // Handle route type checkbox changes
  const handleRouteTypeChange = (routeType) => {
    setRouteTypes(prev => ({
      ...prev,
      [routeType]: !prev[routeType]
    }));
  };

  // Get selected route types text for display
  const getSelectedRouteTypesText = () => {
    const selected = Object.keys(routeTypes).filter(key => routeTypes[key]);
    const total = Object.keys(routeTypes).length;
    
    if (selected.length === total) {
      return 'All Route Types';
    } else if (selected.length === 0) {
      return 'No Route Types';
    } else if (selected.length <= 3) {
      return `Type ${selected.join(', ')}`;
    } else {
      return `${selected.length} Route Types`;
    }
  };

  // Toggle all route types
  const toggleAllRouteTypes = () => {
    const allSelected = Object.values(routeTypes).every(Boolean);
    const newState = {};
    Object.keys(routeTypes).forEach(key => {
      newState[key] = !allSelected;
    });
    setRouteTypes(newState);
  };

  const fetchSuggestedRoutes = async () => {
    setIsLoadingSuggestion(true);
    setSuggestedRoutesText("Fetching suggested routes...");


    try {
      const response = await fetch('/api/suggest-routes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          mapContext: {
            showRoutes: true,
            showBottlenecks: true,
            showLowIncome: true
          }
        })
      });

      const contentType = response.headers.get('content-type');

      if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        setSuggestedRoutesText(data.suggestions || "No suggestions returned.");

        try {
          // 🧽 Clean AI response of markdown ticks (```json ... ```)
          const cleaned = data.suggestions
            .replace(/```json/g, '')
            .replace(/```/g, '')
            .trim();

          const routeJson = JSON.parse(cleaned);
          setAiSuggestedRoutes(routeJson);
        } catch (e) {
          console.warn("Failed to parse AI route JSON:", e);
        }
      }
    } catch (error) {
      console.error("Error fetching suggestions:", error);
      setSuggestedRoutesText("❌ Error fetching suggestions: " + error.message);
    } finally {
      setIsLoadingSuggestion(false);
    }
  };



  // Effects
  useEffect(() => {
    loadGoogleMapsScript();
  }, []);

  useEffect(() => {
    if (isMapLoaded) {
      initializeMap();
    }
  }, [isMapLoaded]);

  useEffect(() => {
    if (googleMap.current) {
      if (showRoutes) {
        if (polylines.current.length === 0 && !routeLayerLoaded.current) {
          loadRoutesLayer();
        } else {
          filterAndDrawRoutes();
        }
      } else {
        clearPolylines();
      }
    }
  }, [showRoutes]);

  useEffect(() => {
    if (googleMap.current && showRoutes) {
      filterAndDrawRoutes();
    }
  }, [routeTypes]);

  useEffect(() => {
    if (googleMap.current) {
      if (showBottlenecks) {
        // If no bottleneck data loaded yet, load it
        if (bottleneckLines.current.length === 0) {
          drawBottlenecks();
        } else {
          // Data already loaded, just show it
          bottleneckLines.current.forEach(line => line.setMap(googleMap.current));
        }
      } else {
        // Hide all bottleneck lines
        bottleneckLines.current.forEach(line => line.setMap(null));
      }
    }
  }, [showBottlenecks]);

  useEffect(() => {
    if (googleMap.current) {
      if (showLowIncome) {
        // If no low income data loaded yet, load it
        if (lowIncomePolygons.current.length === 0) {
          drawLowIncomeAreas();
        } else {
          // Data already loaded, just show it
          lowIncomePolygons.current.forEach(polygon => polygon.setMap(googleMap.current));
        }
      } else {
        // Hide all low income polygons
        lowIncomePolygons.current.forEach(polygon => polygon.setMap(null));
      }
    }
  }, [showLowIncome]);

 useEffect(() => {
    if (!googleMap.current) return;

    // Clear any existing markers
    aiStartMarkers.current.forEach(m => m.setMap(null));
    aiStartMarkers.current = [];

    if (aiSuggestedRoutes.length === 0) return;

    aiSuggestedRoutes.forEach(route => {
      if (!route.start || route.start.length !== 2 || !route.end || route.end.length !== 2) return;

      console.log("Rendering AI Suggested Routes:", aiSuggestedRoutes);

      const markerStart = new window.google.maps.Marker({
        position: {
          lat: route.start[0],
          lng: route.start[1]
        },
        map: googleMap.current,
        title: route.name || "AI Suggested Route Start",
        icon: {
          path: window.google.maps.SymbolPath.CIRCLE,
          scale: 5,
          fillColor: "#1e88e5",
          fillOpacity: 1,
          strokeColor: "#ffffff",
          strokeWeight: 2
        }
      });

      const markerEnd = new window.google.maps.Marker({
        position: {
          lat: route.end[0],
          lng: route.end[1]
        },
        map: googleMap.current,
        title: route.name || "AI Suggested Route End",
        icon: {
          path: window.google.maps.SymbolPath.CIRCLE,
          scale: 5,
          fillColor: "#bc2788ff",
          fillOpacity: 1,
          strokeColor: "#ffffff",
          strokeWeight: 2
        }
      });

      const infoWindow = new window.google.maps.InfoWindow({
        content: `<b>${route.name}</b><br>${route.summary}`
      });

      markerStart.addListener("click", () => {
        infoWindow.open(googleMap.current, markerStart);
      });

      markerEnd.addListener("click", () => {
        infoWindow.open(googleMap.current, markerEnd);
      });

      aiStartMarkers.current.push(markerStart);
      aiStartMarkers.current.push(markerEnd);
    });
  }, [aiSuggestedRoutes]);



  useEffect(() => {
    if (!googleMap.current) return;

    // Clear existing AI lines first
    aiRouteLines.current.forEach(p => p.setMap(null));
    aiRouteLines.current = [];

    if (aiSuggestedRoutes.length === 0) return;

    aiSuggestedRoutes.forEach(route => {
      const path = [
        { lat: route.start[0], lng: route.start[1] },
        { lat: route.end[0], lng: route.end[1] }
      ];

      const polyline = new window.google.maps.Polyline({
        path,
        map: googleMap.current,
        strokeColor: "#0000ff",
        strokeOpacity: 0.9,
        strokeWeight: 3
      });

      polyline.set("info", {
        name: route.name,
        summary: route.summary
      });

      polyline.addListener("click", (e) => {
        const info = polyline.get("info");
        new window.google.maps.InfoWindow({
          content: `<b>${info.name}</b><br>${info.summary}`,
          position: e.latLng
        }).open(googleMap.current);
      });

      aiRouteLines.current.push(polyline);
    });
  }, [aiSuggestedRoutes]);


  if (loading) {
    return (
      <div className="loading-container">
        <h3>Loading Transit Map...</h3>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h3>Error Loading Map</h3>
        <div className="error-box">
          <p><strong>Error:</strong> {error}</p>
          <p>Make sure your .env file contains: VITE_GOOGLE_MAPS_API_KEY=your_key_here</p>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <h3 className="map-title">Transit Stations Map</h3>

      <div id="controls">
        <label className="control-label">
          State:
          <select 
            id="stateFilter"
            value={stateFilter} 
            onChange={(e) => setStateFilter(e.target.value)}
            className="control-input"
          >
            <option value="">All</option>
          </select>
        </label>

        <label className="control-label">
          Mode:
          <select 
            id="modeFilter"
            value={modeFilter} 
            onChange={(e) => setModeFilter(e.target.value)}
            className="control-input"
          >
            <option value="">All</option>
            <option value="bus">Bus</option>
            <option value="air">Air</option>
            <option value="rail">Rail</option>
            <option value="ferry">Ferry</option>
            <option value="bike">Bike</option>
          </select>
        </label>

        <div className="route-type-dropdown">
          <button 
            className="dropdown-toggle"
            onClick={() => setIsRouteDropdownOpen(!isRouteDropdownOpen)}
            type="button"
          >
            Route Types: {getSelectedRouteTypesText()}
            <span className={`dropdown-arrow ${isRouteDropdownOpen ? 'open' : ''}`}>
              ▼
            </span>
          </button>
          
          {isRouteDropdownOpen && (
            <div className="dropdown-menu">
              <div className="dropdown-header">
                <button 
                  className="select-all-btn"
                  onClick={toggleAllRouteTypes}
                  type="button"
                >
                  {Object.values(routeTypes).every(Boolean) ? 'Deselect All' : 'Select All'}
                </button>
              </div>
              
              {Object.keys(routeTypes).map(type => (
                <label key={type} className="dropdown-item">
                  <input 
                    type="checkbox" 
                    className="checkbox-input"
                    value={type}
                    checked={routeTypes[type]}
                    onChange={() => handleRouteTypeChange(type)}
                  />
                  <span className="route-type-label">
                    Route Type {type}
                    <span className="route-type-color" style={{
                      backgroundColor: {
                        "0": "#a65628", "1": "#e41a1c", "2": "#377eb8", 
                        "3": "#4daf4a", "4": "#984ea3", "5": "#ff7f00"
                      }[type]
                    }}></span>
                  </span>
                </label>
              ))}
            </div>
          )}
        </div>

        <label className="control-label">
          <input 
            type="checkbox" 
            id="toggleRoutes"
            className="checkbox-input"
            checked={showRoutes}
            onChange={(e) => setShowRoutes(e.target.checked)}
          />
          Show Transit Lines
        </label>

        <label className="control-label">
          <input 
            type="checkbox" 
            id="toggleBottlenecks"
            className="checkbox-input"
            checked={showBottlenecks}
            onChange={(e) => setShowBottlenecks(e.target.checked)}
          />
          Show Bottlenecks
        </label>

        <label className="control-label">
          <input 
            type="checkbox" 
            id="toggleLowIncome"
            className="checkbox-input"
            checked={showLowIncome}
            onChange={(e) => setShowLowIncome(e.target.checked)}
          />
          Show Low-Income Areas
        </label>

        <button 
          className="suggest-button"
          onClick={fetchSuggestedRoutes}
          type="button"
          disabled={isLoadingSuggestion}
        >
          {isLoadingSuggestion ? 'Loading...' : 'Suggest New Routes'}
        </button>

      </div>

      
      <div id="map" ref={mapRef} />

      {suggestedRoutesText && (
  <div className="suggested-routes-box">
    <h4>AI-Suggested Routes</h4>
    
    {aiSuggestedRoutes.length > 0 ? (
          <ul className="routes-list">
            {aiSuggestedRoutes.map((route, idx) => (
              <li key={idx} className="route-item">
                <div className="route-name">{route.name}</div>
                <div className="route-summary">{route.summary}</div>
                <div className="route-coords">
                  <span><strong>Start:</strong> {route.start.join(', ')}</span><br />
                  <span><strong>End:</strong> {route.end.join(', ')}</span>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="raw-text">{suggestedRoutesText}</div>
        )}
      </div>
    )}


    </div>
  );
}

export default TransitMap;