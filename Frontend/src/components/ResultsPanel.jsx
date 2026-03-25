import React from 'react';
import SentimentBar from './SentimentBar';

export default function ResultsPanel({ results, handleExport, isExporting }) {
  if (!results) return null;
  const sentimentScore = results ? results.text_sentiment : null;
  return (
    <div className="results-container">
      <div className="export-section">
        <h2>Analysis Results</h2>
        <button onClick={handleExport} disabled={isExporting}>
          {isExporting ? 'Generating...' : 'Export as PDF'}
        </button>
      </div>
      <div className="results-grid">
        <div className="result-card">
          <h3>Text Sentiment</h3>
          <p>{results.text_sentiment}</p>
          <SentimentBar sentimentStr={sentimentScore} />
        </div>
        <div className="result-card"><h3>Topic</h3><p>{results.topic_classification}</p></div>
        {results.image_results && results.image_results.length > 1 ? (
          results.image_results.map((imgRes, idx) => (
            <div className="result-card" key={idx}>
              <h3>Image {idx + 1}: {imgRes.filename}</h3>
              <p><strong>Category:</strong> {imgRes.image_classification}</p>
              <p><strong>OCR:</strong> {imgRes.ocr_text || 'None'}</p>
            </div>
          ))
        ) : (
          <>
            <div className="result-card"><h3>Image Category</h3><p>{results.image_classification}</p></div>
            <div className="result-card"><h3>OCR Text</h3><p>{results.ocr_text || 'None'}</p></div>
          </>
        )}
        <div className="result-card full-width"><h3>Text Summary</h3><p>{results.text_summary}</p></div>
        <div className="result-card toxicity-warning"><h3>Toxicity</h3><p>{results.toxicity_warning}</p></div>
        <div className="result-card automated-response"><h3>Automated Response</h3><p>{results.automated_response}</p></div>
      </div>
    </div>
  );
}
