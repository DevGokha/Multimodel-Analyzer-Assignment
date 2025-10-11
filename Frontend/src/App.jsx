import React, { useState } from 'react';
import axios from 'axios';
import './App.css'; 

function App() {
  const [text, setText] = useState('');
  const [image, setImage] = useState(null);
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState('');

  
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleImageChange = (e) => {
    setImage(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text || !image) {
      setError('Please provide both text and an image.');
      return;
    }
    
    setError('');
    setIsLoading(true);
    setResults(null);

    const formData = new FormData();
    formData.append('text', text);
    formData.append('image', image);

    try {
      const response = await axios.post(`${API_BASE_URL}/analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResults(response.data);
    } catch (err) {
      setError('An error occurred during analysis. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = async () => {
    if (!results) return;

    setIsExporting(true);
    setError('');
    try {
      const response = await axios.post(
        `${API_BASE_URL}/generate-report`, 
        results, 
        { responseType: 'blob' } 
      );

      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'analysis_report.pdf');
      document.body.appendChild(link);
      link.click();
      
      
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (err) {
      console.error("Failed to export PDF", err);
      setError("Could not generate the PDF report. Please try again.");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Multimodal Analyzer</h1>
        <p>Submit text and an image to get combined insights.</p>
      </header>
      <main>
        <div className="form-container">
          <form onSubmit={handleSubmit}>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Enter text here... (e.g., 'I hate how messy this restaurant is.')"
              rows="4"
            />
            <input type="file" accept="image/*" onChange={handleImageChange} />
            <button type="submit" disabled={isLoading}>
              {isLoading ? 'Analyzing...' : 'Analyze'}
            </button>
          </form>
          {error && <p className="error">{error}</p>}
        </div>

        {results && (
          <div className="results-container">
            <div className="export-section">
              <h2>Analysis Results</h2>
              <button onClick={handleExport} disabled={isExporting}>
                {isExporting ? 'Generating...' : 'Export as PDF'}
              </button>
            </div>
            <div className="results-grid">
              <div className="result-card"><h3>Text Sentiment</h3><p>{results.text_sentiment}</p></div>
              <div className="result-card"><h3>Topic</h3><p>{results.topic_classification}</p></div>
              <div className="result-card"><h3>Image Category</h3><p>{results.image_classification}</p></div>
              <div className="result-card"><h3>OCR Text</h3><p>{results.ocr_text || 'None'}</p></div>
              <div className="result-card full-width"><h3>Text Summary</h3><p>{results.text_summary}</p></div>
              <div className="result-card toxicity-warning"><h3>Toxicity</h3><p>{results.toxicity_warning}</p></div>
              <div className="result-card automated-response"><h3>Automated Response</h3><p>{results.automated_response}</p></div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;