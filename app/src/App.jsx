import React, { useEffect, useRef, useState } from 'react';

function App() {
  const mapRef = useRef(null); // Reference to the div where the map will be rendered
  const [isMapLoaded, setIsMapLoaded] = useState(false); // Track if the map has loaded
  const googleMap = useRef(null); // Holds the map instance

  // Function to load the Google Maps API dynamically
  const loadGoogleMapsScript = () => {
    // Avoid loading the script multiple times
    if (window.google) return;

    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY; // Get API key from .env
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places&async=true&defer=true`;
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);

    // Once the script is loaded, set the map state to loaded
    script.onload = () => {
      setIsMapLoaded(true); // Update state when the map is loaded
    };
  };

  // Initialize the map after it is loaded
  useEffect(() => {
    loadGoogleMapsScript(); // Load Google Maps API when the component mounts

    return () => {
      // Cleanup: Remove the script when the component is unmounted
      const scriptTags = document.querySelectorAll('script[src^="https://maps.googleapis.com"]');
      scriptTags.forEach(script => script.remove());
    };
  }, []); // Empty dependency array ensures this effect runs only once

  // Create the map once the Google Maps script has been loaded
  useEffect(() => {
    if (isMapLoaded && mapRef.current) {
      googleMap.current = new window.google.maps.Map(mapRef.current, {
        center: { lat: 36.7783, lng: -119.4179 }, // Center map on California
        zoom: 6, // Set initial zoom level
      });
    }
  }, [isMapLoaded]); // Wait for the map to load before initializing it

  return (
    <div className="App">
      <h3 style={{ margin: '10px 20px 0' }}>Transit Stations Map</h3>

      {/* Controls section */}
      <div id="controls" style={{ margin: '10px 20px' }}>
        <label>State:
          <select id="stateFilter">
            <option value="">All</option>
            {/* Add more state options here */}
          </select>
        </label>

        <label>Mode:
          <select id="modeFilter">
            <option value="">All</option>
            <option value="bus">Bus</option>
            <option value="air">Air</option>
            <option value="rail">Rail</option>
            <option value="ferry">Ferry</option>
            <option value="bike">Bike</option>
          </select>
        </label>

        <div id="routeTypeCheckboxes">
          <label>Route Type:</label>
          {/* Example checkbox options for route types */}
          <label><input type="checkbox" className="routeType" value="1" checked /> Type 1</label>
          <label><input type="checkbox" className="routeType" value="2" checked /> Type 2</label>
          <label><input type="checkbox" className="routeType" value="3" checked /> Type 3</label>
          {/* Add more checkboxes as needed */}
        </div>

        <label>Search:
          <input type="text" id="nameSearch" placeholder="Name contains…" />
        </label>
        
        <label><input type="checkbox" id="toggleRoutes" checked /> Show Transit Lines</label>
        <label><input type="checkbox" id="toggleBottlenecks" checked /> Show Bottlenecks</label>
        <label><input type="checkbox" id="toggleLowIncome" checked /> Show Low-Income Areas</label>
      </div>

      {/* Map container */}
      <div
        id="map"
        ref={mapRef}
        style={{ height: '90vh', width: '100%' }} // Make the map container full-height
      ></div>
    </div>
  );
}

export default App;
