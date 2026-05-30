import React, { useState, useRef, useCallback, useEffect } from 'react';
import axios from 'axios';
import './App.css'; 
import Header from './components/Header';
import AnalysisForm from './components/AnalysisForm';
import ImageDropZone from './components/ImageDropZone';
import LoadingProgress from './components/LoadingProgress';
import ResultsPanel from './components/ResultsPanel';
import SentimentBar from './components/SentimentBar';
import HistoryList from './components/HistoryList';

// Step 1: Define the loading steps shown during analysis progress
const LOADING_STEPS = [
  'Uploading data...',
  'Analyzing sentiment...',
  'Summarizing text...',
  'Classifying topic...',
  'Checking toxicity...',
  'Classifying images...',
  'Extracting text from images (OCR)...',
  'Generating response...',
];



// Step 4: Load analysis history from localStorage (returns empty array on failure)
function loadHistory() {
  try {
    const saved = localStorage.getItem('analysisHistory');
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
}

// Step 5: Save analysis history to localStorage (fails silently if full)
function saveHistory(history) {
  try {
    localStorage.setItem('analysisHistory', JSON.stringify(history));
  } catch {
    // localStorage full or unavailable — ignore silently
  }
}

function App() {
  const [text, setText] = useState('');
  // Step 6: Support multiple images — store as an array of File objects
  const [images, setImages] = useState([]);
  // Step 7: Array of preview URLs corresponding to each selected image
  const [imagePreviews, setImagePreviews] = useState([]);
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  // Step 8: Track which loading step we're on (index into LOADING_STEPS)
  const [loadingStep, setLoadingStep] = useState(0);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState('');
  // Step 9: Load saved history from localStorage on first render
  const [history, setHistory] = useState(loadHistory);
  // Step 10: Track whether the user is dragging a file over the drop zone
  const [isDragging, setIsDragging] = useState(false);
  // Step 11: Custom topic labels entered by the user (comma-separated string)
  const [customTopics, setCustomTopics] = useState('');
  // Step 12: Dark mode toggle state, persisted in localStorage
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem('darkMode') === 'true';
  });
  // Step 13: Ref to the hidden file input so we can trigger it from the drop zone
  const fileInputRef = useRef(null);

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Step 14: Apply dark mode attribute to the HTML element whenever darkMode changes
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light');
    localStorage.setItem('darkMode', darkMode);
  }, [darkMode]);

  // Step 15: Persist history to localStorage whenever it changes
  useEffect(() => {
    saveHistory(history);
  }, [history]);

  // Step 16: Add files to the images array and generate preview URLs for each
  const addImages = useCallback((files) => {
    const newFiles = Array.from(files).filter(f => f.type.startsWith('image/'));
    if (newFiles.length === 0) return;
    setImages(prev => [...prev, ...newFiles]);
    const newPreviews = newFiles.map(f => URL.createObjectURL(f));
    setImagePreviews(prev => [...prev, ...newPreviews]);
  }, []);

  // Step 17: Handle file input changes (classic file picker, supports multiple)
  const handleImageChange = (e) => {
    addImages(e.target.files);
  };

  // Step 18: Remove a specific image by its index in the array
  const handleRemoveImage = (index) => {
    URL.revokeObjectURL(imagePreviews[index]);
    setImages(prev => prev.filter((_, i) => i !== index));
    setImagePreviews(prev => prev.filter((_, i) => i !== index));
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Step 19: Drag-and-drop event handlers for the drop zone
  const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = (e) => { e.preventDefault(); setIsDragging(false); };
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
    if (files.length > 0) {
      addImages(files);
    } else {
      setError('Please drop valid image files (JPEG, PNG, GIF, etc.).');
    }
  };


  // Step 21: Submit the form — sends text + all images + optional custom topics
  // Step 21: Submit the form — sends text + all images + optional custom topics with real-time SSE updates
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text || images.length === 0) {
      setError('Please provide both text and at least one image.');
      return;
    }

    setError('');
    setIsLoading(true);
    setResults(null);
    setLoadingStep(0);

    const formData = new FormData();
    formData.append('text', text);
    // Step 21a: Append every selected image under the 'images' field name
    images.forEach(img => formData.append('images', img));
    // Step 21b: Append custom topic labels if the user entered any
    if (customTopics.trim()) {
      formData.append('topics', customTopics.trim());
    }

    try {
      const response = await fetch(`${API_BASE_URL}/analyze-stream`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorJson = await response.json().catch(() => ({}));
        throw new Error(errorJson.detail || 'An error occurred during analysis. Please try again.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Store partial line back in buffer

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data:')) {
            const dataStr = trimmed.slice(5).trim();
            const event = JSON.parse(dataStr);

            if (event.status === 'processing') {
              setLoadingStep(event.step);
            } else if (event.status === 'completed') {
              setResults(event.results);
              // Step 21c: Save this analysis to history with a timestamp
              setHistory(prev => [
                { id: Date.now(), timestamp: new Date().toLocaleString(), data: event.results },
                ...prev,
              ]);
            } else if (event.status === 'error') {
              throw new Error(event.detail || 'Analysis task failed on the server.');
            }
          }
        }
      }
    } catch (err) {
      setError(err.message || 'An error occurred during analysis. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
      setLoadingStep(0);
    }
  };

  // Step 22: Export results as a PDF report
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
      const serverMessage = err.response?.data?.detail;
      setError(serverMessage || "Could not generate the PDF report. Please try again.");
    } finally {
      setIsExporting(false);
    }
  };

  // Step 23: Load a past result from history back into the results view
  const handleLoadHistory = (entry) => setResults(entry.data);

  // Step 24: Clear all saved analysis history from both state and localStorage
  const handleClearHistory = () => {
    setHistory([]);
    localStorage.removeItem('analysisHistory');
  };


  return (
    <div className="App">
      <Header darkMode={darkMode} setDarkMode={setDarkMode} />
      <main>
        <div className="form-container">
          <AnalysisForm
            text={text}
            setText={setText}
            customTopics={customTopics}
            setCustomTopics={setCustomTopics}
            images={images}
            setImages={setImages}
            imagePreviews={imagePreviews}
            setImagePreviews={setImagePreviews}
            isDragging={isDragging}
            setIsDragging={setIsDragging}
            fileInputRef={fileInputRef}
            handleImageChange={handleImageChange}
            handleRemoveImage={handleRemoveImage}
            handleDragOver={handleDragOver}
            handleDragLeave={handleDragLeave}
            handleDrop={handleDrop}
            handleSubmit={handleSubmit}
            isLoading={isLoading}
          />
          {isLoading && (
            <LoadingProgress loadingStep={loadingStep} steps={LOADING_STEPS} />
          )}
          {error && <p className="error">{error}</p>}
        </div>
        <ResultsPanel results={results} handleExport={handleExport} isExporting={isExporting} />
        <HistoryList history={history} handleLoadHistory={handleLoadHistory} handleClearHistory={handleClearHistory} />
      </main>
    </div>
  );
}

export default App;