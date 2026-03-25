# Multimodal Analyzer

A full-stack project for analyzing text and images using state-of-the-art ML models. Features sentiment analysis, summarization, topic classification, image classification, OCR, toxicity detection, and PDF report generation.

---

## 🚀 Features

- **Text Sentiment Analysis** (DistilBERT)
- **Text Summarization** (DistilBART)
- **Topic Classification** (Zero-shot, custom topics)
- **Image Classification** (ViT)
- **OCR** (EasyOCR)
- **Toxicity Detection** (profanity-check)
- **PDF Report Generation** (Unicode, branding)
- **Multi-image upload**
- **Custom topic labels**
- **Dark mode, responsive UI**
- **Local history, drag-and-drop**

---

## 🖼️ Demo

![Demo Screenshot](./Frontend/public/demo.png)

---

## 🏗️ Architecture

```
graph TD
  FE[Frontend (React/Vite)] -- REST API --> BE[Backend (FastAPI)]
  BE -- ML Inference --> Models[Transformers, EasyOCR, etc.]
  BE -- PDF --> User
  FE -- PDF Download --> User
```

---

## ⚡ Quick Start

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # or source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Frontend

```bash
cd Frontend
npm install
npm run dev
```

---

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, Transformers, Torch, EasyOCR, fpdf2
- **Frontend:** React 19, Vite, Axios
- **Testing:** Pytest, httpx, Vitest, @testing-library/react

---

## 📁 Project Structure

```
Multimodel-Analyzer-Assignment/
  backend/
    analyzer.py
    main.py
    pdf_generator.py
    requirements.txt
    tests/
  Frontend/
    src/
      components/
      App.jsx
      ...
    public/
    package.json
```

---

## 📄 License

MIT
