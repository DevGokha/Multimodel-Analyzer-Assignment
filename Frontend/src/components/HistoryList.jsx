import React from 'react';

function truncateText(text, maxLen = 40) {
  if (!text) return '';
  return text.length > maxLen ? text.slice(0, maxLen) + '…' : text;
}

export default function HistoryList({ history, handleLoadHistory, handleClearHistory }) {
  if (!history.length) return null;
  return (
    <div className="history-container">
      <div className="history-header">
        <h2>Analysis History</h2>
        <button className="clear-history-btn" onClick={handleClearHistory}>Clear All</button>
      </div>
      <div className="history-list">
        {history.map((entry) => (
          <div key={entry.id} className="history-item">
            <div className="history-info">
              <span className="history-time">{entry.timestamp}</span>
              <span className="history-sentiment">{entry.data.text_sentiment}</span>
              <span className="history-snippet">{truncateText(entry.data.text_summary || entry.data.text_sentiment || '')}</span>
            </div>
            <button className="history-load-btn" onClick={() => handleLoadHistory(entry)}>
              View
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
