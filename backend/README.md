# Multimodal Analyzer — Backend

A FastAPI-based backend that performs multimodal analysis on text and images using several ML models.

## Features

- **Sentiment Analysis** — DistilBERT (distilbert-base-uncased-finetuned-sst-2-english)
- **Text Summarization** — DistilBART (sshleifer/distilbart-cnn-6-6)
- **Topic Classification** — Zero-shot with BART-large-MNLI (supports custom topics)
- **Image Classification** — ViT (google/vit-base-patch16-224)
- **OCR** — EasyOCR for text extraction from images
- **Toxicity Detection** — profanity-check on both input text and OCR output
- **PDF Report Generation** — Branded reports with Unicode support (DejaVu fonts)

## Setup

### 1. Create a virtual environment

```bash
python -m venv venv
```

### 2. Activate the virtual environment

**Windows:**

```bash
venv\Scripts\activate
```

**macOS / Linux:**

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables (optional)

Copy the example file and edit as needed:

```bash
cp .env.example .env
```

Available variables:
| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Server port |

### 5. Start the server

```bash
python main.py
```

The API will be available at `http://localhost:8000` (or your configured port).

## API Endpoints

### `GET /`

Health check — returns a status message.

### `POST /analyze`

Analyzes text and images. Accepts `multipart/form-data`:

| Field    | Type    | Required | Description                                                              |
| -------- | ------- | -------- | ------------------------------------------------------------------------ |
| `text`   | string  | Yes      | Text to analyze (max 10,000 chars)                                       |
| `images` | file(s) | Yes      | One or more image files (JPEG, PNG, GIF, WebP, BMP, TIFF; max 10MB each) |
| `topics` | string  | No       | Comma-separated custom topic labels for classification                   |

### `POST /generate-report`

Generates a branded PDF report from analysis results. Accepts JSON matching the analysis response schema.

## Architecture

**Load-use-unload models** — Only one ML model is loaded in memory at a time, using a thread-safe lock and immediate unloading after each inference. This prevents memory crashes on limited systems.
**Sequential execution** — All model calls run one-by-one (not in parallel) to avoid out-of-memory errors.
**Thread-safe** — Model loading/unloading is protected by a threading lock.
