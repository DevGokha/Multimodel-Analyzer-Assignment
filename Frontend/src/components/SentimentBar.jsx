import React from 'react';

export default function SentimentBar({ sentimentStr }) {
  const match = sentimentStr?.match(/\(([0-9.]+)\)/);
  const score = match ? parseFloat(match[1]) : null;
  const label = sentimentStr?.match(/^(\w+)/)?.[1] || sentimentStr;
  if (score === null) return null;

  const percentage = score * 100;
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  let textAccentColor = '#3b82f6';
  if (label === 'POSITIVE') {
    textAccentColor = '#10b981'; // Emerald Green
  } else if (label === 'NEGATIVE') {
    textAccentColor = '#ef4444'; // Rose Red
  }

  return (
    <div className="sentiment-radial-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', margin: '15px 0' }}>
      <div style={{ position: 'relative', width: '100px', height: '100px' }}>
        <svg style={{ transform: 'rotate(-90deg)', width: '100px', height: '100px' }}>
          {/* Background circle */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="transparent"
            stroke="var(--bg-card-border, #e5e7eb)"
            strokeWidth="8"
          />
          {/* Animated active circle */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="transparent"
            stroke={textAccentColor}
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.8s ease-in-out' }}
          />
        </svg>
        {/* Label inside */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center'
        }}>
          <span style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--text-primary, #1f2937)' }}>
            {percentage.toFixed(0)}%
          </span>
          <span style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em', color: textAccentColor, fontWeight: 'bold' }}>
            {label}
          </span>
        </div>
      </div>
      <span style={{ fontSize: '12px', color: 'var(--text-secondary, #6b7280)', marginTop: '8px', fontWeight: '500' }}>
        Sentiment Analysis Confidence
      </span>
    </div>
  );
}
