# TruthLens — Explainable AI Fake News Detection System

> *“Don’t just detect misinformation. Understand why.”*

TruthLens is an Explainable AI (XAI) and Natural Language Processing (NLP) web platform that analyzes news articles, headlines, and claims to identify linguistic and statistical patterns associated with potentially misleading or unreliable information.

---

## 🌟 Key Capabilities & Architectural Highlights

1. **4-Tier Interpretative Classification Framework**:
   - `REAL / LOW RISK`: Neutral attribution, standard reporting structures.
   - `SUSPICIOUS / REVIEW`: Ambiguous framing or uncorroborated claims requiring secondary review.
   - `LIKELY MISLEADING`: Strong lexical, stylistic, and model alignment with fabricated content.
   - `INSUFFICIENT EVIDENCE`: Content too short for statistical reliability.

2. **Dual-Score Architecture**:
   - **Model Confidence Score** (0-100%): Learned statistical class certainty based on TF-IDF training distributions.
   - **Misinformation Risk Score** (0-100%): 6-dimensional composite score across sensationalism, clickbait, emotion, shouting, and assertion density.
   - *Clear Ethical Distinction: "Model confidence ≠ factual certainty."*

3. **5 Machine Learning Classifiers Benchmark**:
   - **Linear Support Vector Machine (LinearSVM)** (Calibrated)
   - **XGBoost Classifier** (Gradient Boosted Trees)
   - **Logistic Regression** (L2 Regularized Baseline)
   - **Multinomial Naive Bayes** (Bayesian Baseline)
   - **Random Forest** (Decision Forest Ensemble)

4. **Explainable AI (XAI) & In-Text Span Highlighting**:
   - Local feature attribution assigning directional impact weights (Misleading vs Credible) to individual tokens.
   - Interactive article visualizer with color-coded tags for Sensational phrases, Clickbait hooks, and Stylistic anomalies.

5. **Advanced Evidence Verification Layer (Groq LLM Powered)**:
   - Uses Groq's high-speed inference to extract atomic claims and evaluate their plausibility against verified consensus with suggested primary sources.

6. **Executive PDF Fact-Check Reports**:
   - One-click downloadable PDF reports containing the full verdict, gauge charts, linguistic breakdown, extracted claims, and methodology notices.

---

## 🚀 Quick Start

### 1. Launch Platform
```bash
python run.py
```
This boots the FastAPI backend and serves the compiled React Single-Page Application on `http://127.0.0.1:8000`.

### 2. Run in Development Mode (Optional)
To run backend with hot reload and frontend dev server:
- **Backend**:
  ```bash
  uvicorn backend.app:app --reload --port 8000
  ```
- **Frontend**:
  ```bash
  cd frontend
  npm run dev
  ```

---

## 📁 System Architecture

```
├── backend/
│   ├── app.py                     # FastAPI REST API & Static File Server
│   ├── config.py                  # Settings, Groq API key & Paths
│   ├── database.py                # SQLite History & Persistence (truthlens.db)
│   ├── nlp/
│   │   ├── preprocessor.py        # Tokenization, Lemmatization & Normalization
│   │   ├── feature_extractor.py   # TF-IDF Vectorizer
│   │   └── linguistic_analyzer.py # 6D Risk Indicators & Lexicons
│   ├── models/
│   │   ├── dataset_builder.py     # Balanced Multi-Category Dataset Generator
│   │   ├── trainer.py             # 5-Model Benchmark Training Engine
│   │   ├── model_service.py       # Inference & 4-Tier Verdict Synthesis
│   │   └── saved_models/          # Serialized Classifiers & metrics.json
│   ├── explainability/
│   │   ├── xai_engine.py          # Token-level Local Feature Attribution
│   │   └── highlighter.py         # Character Span Highlighting & HTML Markup
│   └── services/
│       ├── url_extractor.py       # SSRF-Safe Web Scraper & Metadata Extractor
│       ├── evidence_verifier.py   # Groq-powered Atomic Claim Verification
│       └── pdf_exporter.py        # ReportLab PDF Report Generator
├── frontend/                      # Modern React + Vite + Tailwind Client
│   ├── src/
│   │   ├── components/            # Analyzer, Results, Benchmark, History, Learn, Studio
│   │   └── services/api.ts        # REST Client
│   └── dist/                      # Production Build Bundle
└── run.py                         # Single-command Platform Runner
```
