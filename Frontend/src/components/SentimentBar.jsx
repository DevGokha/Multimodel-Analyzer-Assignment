import React from 'react';

export default function SentimentBar({ sentimentStr }) {
  const match = sentimentStr?.match(/\(([0-9.]+)\)/);
  const score = match ? parseFloat(match[1]) : null;
  const label = sentimentStr?.match(/^(\w+)/)?.[1] || sentimentStr;
  if (score === null) return null;
  return (
    <div className="confidence-bar-container">
      <div
        className={`confidence-bar-fill ${label === 'POSITIVE' ? 'confidence-positive' : 'confidence-negative'}`}
        style={{ width: `${score * 100}%` }}
      />
      <span className="confidence-label">{(score * 100).toFixed(0)}% confidence</span>
    </div>
  );
}
