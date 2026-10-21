# YouTube Authenticity Analyzer

Premium full-stack application for detecting suspicious content using TF-IDF + LinearSVC, with rule-based explainability indicators.

## Stack

- **Frontend:** React, Tailwind CSS, Framer Motion, Recharts, Lucide Icons
- **Backend:** FastAPI, SQLite, Session Authentication
- **ML:** Existing `model.pkl` + `vectorizer.pkl` (unchanged)

## Setup

### Backend

```bash
cd Dataset
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd Dataset/frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

## Features

- Login / Register / Logout (session auth)
- Premium dashboard with overview, analytics, and system status
- Text Analysis with rule-based indicators
- YouTube Analysis (transcript fetch + detection)
- Interactive history with filters and detail modal
- Suspicious content reports (print / PDF download)
- Analytics charts and statistics
- SQLite Analysis History

## Notes

- Do not modify `model.pkl` or `vectorizer.pkl`
- ML pipeline: `vectorizer.transform([text])` → `model.predict()` → 1 = Credible, else Suspicious
- No confidence scores displayed — indicators are rule-based only
