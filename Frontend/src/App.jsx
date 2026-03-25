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

// Step 2: Helper to extract the confidence score from "POSITIVE (0.95)" format
function parseSentimentScore(sentimentStr) {
  const match = sentimentStr?.match(/\(([0-9.]+)\)/);
  return match ? parseFloat(match[1]) : null;
}

// Step 3: Helper to extract the label from "POSITIVE (0.95)" format
function parseSentimentLabel(sentimentStr) {
  const match = sentimentStr?.match(/^(\w+)/);
  return match ? match[1] : sentimentStr;
}

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

  // Step 20: Simulate progress through loading steps while waiting for the API
  const simulateProgress = () => {
    setLoadingStep(0);
    const totalSteps = LOADING_STEPS.length;
    // Move to the next step every 1.5 seconds
    const interval = setInterval(() => {
      setLoadingStep(prev => {
        if (prev >= totalSteps - 1) { clearInterval(interval); return prev; }
        return prev + 1;
      });
    }, 1500);
    return interval;
  };

  // Step 21: Submit the form — sends text + all images + optional custom topics
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text || images.length === 0) {
      setError('Please provide both text and at least one image.');
      return;
    }

    setError('');
    setIsLoading(true);
    setResults(null);

    // Step 21a: Start the progress indicator
    const progressInterval = simulateProgress();

    const formData = new FormData();
    formData.append('text', text);
    // Step 21b: Append every selected image under the 'images' field name
    images.forEach(img => formData.append('images', img));
    // Step 21c: Append custom topic labels if the user entered any
    if (customTopics.trim()) {
      formData.append('topics', customTopics.trim());
    }

    try {
      const response = await axios.post(`${API_BASE_URL}/analyze`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResults(response.data);
      // Step 21d: Save this analysis to history with a timestamp
      setHistory(prev => [
        { id: Date.now(), timestamp: new Date().toLocaleString(), data: response.data },
        ...prev,
      ]);
    } catch (err) {
      const serverMessage = err.response?.data?.detail;
      setError(serverMessage || 'An error occurred during analysis. Please try again.');
      console.error(err);
    } finally {
      clearInterval(progressInterval);
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

  // Step 25: Parse the confidence score and label for the visual bar
  const sentimentScore = results ? parseSentimentScore(results.text_sentiment) : null;
  const sentimentLabel = results ? parseSentimentLabel(results.text_sentiment) : null;

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