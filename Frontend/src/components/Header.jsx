import React from 'react';

export default function Header({ darkMode, setDarkMode }) {
  return (
    <header className="App-header">
      <div className="header-row">
        <h1>Multimodal Analyzer</h1>
        <button
          className="theme-toggle"
          onClick={() => setDarkMode(prev => !prev)}
          title="Toggle dark mode"
        >
          {darkMode ? '☀️' : '🌙'}
        </button>
      </div>
      <p>Submit text and images to get combined insights.</p>
    </header>
  );
}
