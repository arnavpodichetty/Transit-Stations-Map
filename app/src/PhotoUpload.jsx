import React, { useState } from 'react';

function PhotoUpload() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    setFile(selected);
    setPreview(URL.createObjectURL(selected));
    setResult(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setLoading(true);
    const formData = new FormData();
    formData.append('photo', file);

    try {
      const response = await fetch('${import.meta.env.VITE_API_URL}/api/match_photo', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Transit Stop Finder</h2>
      <input type="file" accept="image/*" onChange={handleFileChange} />
      
      {preview && (
        <div style={{ margin: '10px 0' }}>
          <img src={preview} alt="Preview" style={{ maxWidth: '300px' }} />
        </div>
      )}
      
      <button onClick={handleUpload} disabled={!file || loading}>
        {loading ? 'Finding Match...' : 'Find Matching Stop'}
      </button>
      
      {result && (
        <div style={{ marginTop: '20px' }}>
          <h3>Match Found</h3>
          <p>Similarity: {(result.similarity_score * 100).toFixed(1)}%</p>
          <p>Reference Image: {result.matched_image}</p>
        </div>
      )}
    </div>
  );
}

export default PhotoUpload;