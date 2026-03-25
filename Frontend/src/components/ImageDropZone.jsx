import React from 'react';

export default function ImageDropZone({ imagePreviews, images, isDragging, handleDragOver, handleDragLeave, handleDrop, handleRemoveImage, fileInputRef, handleImageChange }) {
  return (
    <div
      className={`drop-zone ${isDragging ? 'drop-zone-active' : ''} ${imagePreviews.length > 0 ? 'drop-zone-has-image' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
    >
      {imagePreviews.length > 0 ? (
        <div className="image-previews-grid">
          {imagePreviews.map((preview, idx) => (
            <div className="image-preview" key={idx}>
              <img src={preview} alt={`Preview ${idx + 1}`} />
              <button
                type="button"
                className="remove-image-btn"
                onClick={e => { e.stopPropagation(); handleRemoveImage(idx); }}
              >
                ✕
              </button>
              <p className="preview-filename">{images[idx]?.name}</p>
            </div>
          ))}
          <div
            className="add-more-placeholder"
            onClick={e => { e.stopPropagation(); fileInputRef.current?.click(); }}
          >
            <span>+ Add more</span>
          </div>
        </div>
      ) : (
        <div className="drop-zone-placeholder">
          <span className="drop-zone-icon">📁</span>
          <p>Drag & drop images here, or click to browse</p>
        </div>
      )}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        multiple
        onChange={handleImageChange}
        style={{ display: 'none' }}
      />
    </div>
  );
}
