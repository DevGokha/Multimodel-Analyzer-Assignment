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
        <div className="result-card">
          <h3>Topic Classification</h3>
          <p style={{ fontWeight: 'bold', fontSize: '18px', color: '#3b82f6', marginBottom: '10px' }}>
            {results.topic_classification}
          </p>
          {results.topic_scores && results.topic_scores.length > 0 && (
            <div className="topic-distribution" style={{ marginTop: '10px' }}>
              {results.topic_scores.map((t, idx) => (
                <div key={idx} style={{ marginBottom: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: '500', color: 'var(--text-secondary, #4b5563)' }}>
                    <span>{t.label}</span>
                    <span>{(t.score * 100).toFixed(0)}%</span>
                  </div>
                  <div style={{ height: '6px', backgroundColor: 'var(--bg-card-border, #e5e7eb)', borderRadius: '3px', overflow: 'hidden', marginTop: '3px' }}>
                    <div style={{ height: '100%', width: `${t.score * 100}%`, backgroundColor: '#3b82f6', borderRadius: '3px', transition: 'width 0.6s ease-in-out' }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        {(() => {
          const renderTags = (tags) => {
            if (!tags || tags.length === 0) return null;
            return (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginTop: '10px' }}>
                {tags.map((tag, tIdx) => {
                  let bg = 'rgba(59, 130, 246, 0.1)';
                  let border = 'rgba(59, 130, 246, 0.2)';
                  let color = '#3b82f6';
                  
                  if (tag.includes('⚠️')) {
                    bg = 'rgba(239, 68, 68, 0.1)';
                    border = 'rgba(239, 68, 68, 0.2)';
                    color = '#ef4444';
                  } else if (tag.includes('🏷️')) {
                    bg = 'rgba(16, 185, 129, 0.1)';
                    border = 'rgba(16, 185, 129, 0.2)';
                    color = '#10b981';
                  }
                  
                  return (
                    <span 
                      key={tIdx} 
                      style={{ 
                        fontSize: '10px', 
                        fontWeight: 'bold', 
                        padding: '2px 8px', 
                        borderRadius: '10px', 
                        backgroundColor: bg, 
                        border: `1px solid ${border}`,
                        color: color,
                        display: 'inline-flex',
                        alignItems: 'center'
                      }}
                    >
                      {tag}
                    </span>
                  );
                })}
              </div>
            );
          };

          return results.image_results && results.image_results.length > 1 ? (
            results.image_results.map((imgRes, idx) => (
              <div className="result-card" key={idx}>
                <h3>Image {idx + 1}: {imgRes.filename}</h3>
                <p><strong>Category:</strong> {imgRes.image_classification}</p>
                <p><strong>OCR:</strong> {imgRes.ocr_text || 'None'}</p>
                {renderTags(imgRes.ocr_tags)}
              </div>
            ))
          ) : (
            <>
              <div className="result-card"><h3>Image Category</h3><p>{results.image_classification}</p></div>
              <div className="result-card">
                <h3>OCR Text</h3>
                <p>{results.ocr_text || 'None'}</p>
                {results.image_results && results.image_results[0] && renderTags(results.image_results[0].ocr_tags)}
              </div>
            </>
          );
        })()}
        <div className="result-card full-width"><h3>Text Summary</h3><p>{results.text_summary}</p></div>
        <div className="result-card toxicity-warning"><h3>Toxicity</h3><p>{results.toxicity_warning}</p></div>
        <div className="result-card automated-response"><h3>Automated Response</h3><p>{results.automated_response}</p></div>
      </div>
    </div>
  );
}
