# Multimodal Analyzer

![Build](https://img.shields.io/github/actions/workflow/status/DevGokha/Multimodel-Analyzer-Assignment/ci.yml?branch=main)
![License](https://img.shields.io/github/license/DevGokha/Multimodel-Analyzer-Assignment)

A modern full-stack project for analyzing text and images using state-of-the-art ML models. Instantly get sentiment, summary, topic, image classification, OCR, toxicity detection, and a beautiful PDF report—all in one place.

---

## 🌟 Why Multimodal Analyzer?

- **Unified**: Analyze both text and images in a single workflow.
- **Fast**: Loads only one ML model at a time—runs on modest hardware.
- **User-Friendly**: Drag-and-drop, dark mode, mobile-ready, and PDF export.
- **Customizable**: Bring your own topics, upload multiple images, and get detailed feedback.

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

## 🏗️ Architecture

```
graph TD
  FE[Frontend (React/Vite)] -- REST API --> BE[Backend (FastAPI)]
  BE -- ML Inference --> Models[Transformers, EasyOCR, etc.]
  BE -- PDF --> User
  FE -- PDF Download --> User
```

---

## 🔎 How it Works

1. **User uploads text and images** via the web UI.
2. **Backend sequentially loads each ML model** (sentiment, summary, topic, image, OCR, toxicity) and runs inference.
3. **Results are combined** and returned to the frontend.
4. **User can export a Unicode PDF report** with all results and branding.

---

## ⚡ Quick Start

### With Docker (Recommended)

```bash
docker-compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

### Manual Setup

#### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # or source venv/bin/activate
pip install -r requirements.txt
python main.py
```

#### Frontend

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
- **CI/CD:** GitHub Actions
- **Containerization:** Docker, docker-compose

---

## 🧪 Testing & CI

- **Backend:**
  - Run all tests: `cd backend && pytest`
- **Frontend:**
  - Lint: `cd Frontend && npm run lint`
  - Test: `cd Frontend && npx vitest run`
- **CI:** All tests and linting run automatically on every push via GitHub Actions.

---

## ♿ Accessibility & UX

- Keyboard navigation and focus indicators
- ARIA labels on interactive elements
- Responsive design and dark mode
- Drag-and-drop and progress feedback

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## 🙏 Acknowledgments

- [HuggingFace Transformers](https://huggingface.co/transformers/)
- [EasyOCR](https://github.com/JaidedAI/EasyOCR)
- [fpdf2](https://github.com/PyFPDF/fpdf2)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)

---

## 📬 Contact

For questions or feedback, open an issue or contact [@DevGokha](https://github.com/DevGokha).

## 📁 Project Structure

```
Multimodel-Analyzer-Assignment/
│
├── backend/                        # Backend (FastAPI, ML, PDF, etc.)
│   ├── analyzer.py                 # Core analysis logic (ML, OCR, etc.)
│   ├── main.py                     # FastAPI app entry point
│   ├── pdf_generator.py            # PDF report generation logic
│   ├── requirements.txt            # Python dependencies
│   ├── __pycache__/                # Python bytecode cache (auto-generated)
│   └── tests/                      # Backend tests (pytest, httpx)
│       ├── test_analyzer.py
│       └── test_main.py
│
├── Frontend/                       # Frontend (React, Vite)
│   ├── public/                     # Static assets (favicon, etc.)
│   ├── src/                        # Source code
│   │   ├── App.jsx                 # Main React component
│   │   ├── App.css                 # App-level styles
│   │   ├── index.css               # Global styles
│   │   ├── main.jsx                # React entry point
│   │   └── components/             # Modular UI components
│   │       ├── Header.jsx
│   │       ├── AnalysisForm.jsx
│   │       ├── ImageDropZone.jsx
│   │       ├── LoadingProgress.jsx
│   │       ├── ResultsPanel.jsx
│   │       ├── SentimentBar.jsx
│   │       └── HistoryList.jsx
│   ├── assets/                     # Images, icons, etc.
│   ├── package.json                # Frontend dependencies & scripts
│   ├── vite.config.js              # Vite configuration
│   ├── eslint.config.js            # Linting configuration
│   ├── README.md                   # Frontend-specific docs (optional)
│   └── tests/                      # Frontend tests (Vitest, React Testing Library)
│       ├── App.test.jsx
│       └── components/
│           └── AnalysisForm.test.jsx
│
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions CI/CD workflow
│
├── scripts/
│   └── setup.sh                    # One-command setup script
│
├── Dockerfile                      # Docker build for backend
├── docker-compose.yml              # Multi-service orchestration
├── .env                            # Environment variables (never commit secrets)
├── .gitignore                      # Files/folders to ignore in git
├── README.md                       # Main project documentation
└── LICENSE                         # Project license (MIT, Apache, etc.)
```

Each file and folder is described in comments above for clarity.

---

## 📄 License

MIT
