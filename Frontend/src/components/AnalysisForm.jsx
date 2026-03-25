import React from 'react';
import ImageDropZone from './ImageDropZone';

export default function AnalysisForm({
  text, setText, customTopics, setCustomTopics, images, setImages, imagePreviews, setImagePreviews,
  isDragging, setIsDragging, fileInputRef, handleImageChange, handleRemoveImage, handleDragOver, handleDragLeave, handleDrop, handleSubmit, isLoading
}) {
  return (
    <form onSubmit={handleSubmit}>
      <textarea
        value={text}
        onChange={e => setText(e.target.value)}
        placeholder="Enter text here... (e.g., 'I hate how messy this restaurant is.')"
        rows="4"
      />
      <input
        type="text"
        value={customTopics}
        onChange={e => setCustomTopics(e.target.value)}
        placeholder="Custom topics (optional, comma-separated: e.g. sports, politics, tech)"
        className="topics-input"
      />
      <ImageDropZone
        imagePreviews={imagePreviews}
        images={images}
        isDragging={isDragging}
        handleDragOver={handleDragOver}
        handleDragLeave={handleDragLeave}
        handleDrop={handleDrop}
        handleRemoveImage={handleRemoveImage}
        fileInputRef={fileInputRef}
        handleImageChange={handleImageChange}
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Analyzing...' : 'Analyze'}
      </button>
    </form>
  );
}
