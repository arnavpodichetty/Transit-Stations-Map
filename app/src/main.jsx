import React from 'react';
import ReactDOM from 'react-dom/client';
import PhotoUpload from './PhotoUpload';  // Use your PhotoUpload component here
import App from './App'; // Your main Google Maps app


function Root() {
  const [matchedLocation, setMatchedLocation] = useState(null);

  // This function can be passed to PhotoUpload to receive lat/lng of matched location
  const handleMatch = (lat, lng) => {
    setMatchedLocation({ lat, lng });
  };

  return (
    <>
      <PhotoUpload onMatch={handleMatch} />
      <TransitMap matchedLocation={matchedLocation} />
    </>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);
