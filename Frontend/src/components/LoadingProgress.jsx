import React from 'react';

export default function LoadingProgress({ loadingStep, steps }) {
  return (
    <div className="loading-indicator">
      <div className="progress-bar-container">
        <div
          className="progress-bar-fill"
          style={{ width: `${((loadingStep + 1) / steps.length) * 100}%` }}
        />
      </div>
      <p className="loading-step-text">{steps[loadingStep]}</p>
      <p className="loading-step-count">Step {loadingStep + 1} of {steps.length}</p>
    </div>
  );
}
