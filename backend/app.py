import os
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Response, Query, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.config import settings, BASE_DIR
from backend.models.model_service import model_service
from backend.models.trainer import trainer
from backend.services.url_extractor import url_extractor
from backend.services.evidence_verifier import evidence_verifier
from backend.services.pdf_exporter import pdf_exporter
from backend.services.instagram_analyzer import instagram_analyzer
from backend.database import (
    save_analysis_record, get_analyses_history, get_analysis_by_id,
    delete_analysis_by_id, get_dashboard_summary_stats
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Explainable AI Fake News Detection Platform API"
)

# Enable CORS for local dev and frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class AnalyzeTextRequest(BaseModel):
    headline: Optional[str] = Field(default="", description="News headline or title")
    content: Optional[str] = Field(default="", description="Article body text")
    model_name: Optional[str] = Field(default=None, description="Specific ML classifier to use")
    verify_evidence: Optional[bool] = Field(default=True, description="Whether to run Groq claim extraction & evidence verification")

class AnalyzeUrlRequest(BaseModel):
    url: str = Field(..., description="Target article web address")
    model_name: Optional[str] = Field(default=None, description="Specific ML classifier to use")
    verify_evidence: Optional[bool] = Field(default=True, description="Whether to run Groq claim extraction & evidence verification")

class AnalyzeInstagramRequest(BaseModel):
    url: str = Field(..., description="Instagram post or reel URL")
    model_name: Optional[str] = Field(default=None, description="Specific ML classifier to use")
    verify_evidence: Optional[bool] = Field(default=True, description="Whether to run evidence verification")

class SwitchModelRequest(BaseModel):
    model_key: str = Field(..., description="Key of the model to activate")

# Sample Presets for Demonstrations
DEMO_PRESETS = [
    {
        "id": "conspiracy-cure",
        "title": "Sensational Medical Hoax",
        "category": "Misinformation / Conspiratorial Health",
        "headline": "SHOCKING: Secret Government Documents Leaked Proving All Cancer Cures Were Suppressed for Decades!",
        "content": "A heroic whistleblower has just LEAKED explosive classified files that the deep state pharmaceutical mafia NEVER wanted you to see! The mind-blowing documents confirm that a 100% natural herbal remedy discovered in 1952 cures all forms of terminal cancer in just 48 hours, but corrupt billionaire elites buried it to protect their multi-trillion dollar profits! Mainstream media is under complete blackout! You won't believe what happens when you drink this everyday kitchen juice! Share this VIRAL warning before it gets banned and deleted from the internet forever! Wake up sheeple!"
    },
    {
        "id": "genuine-reuters",
        "title": "Mainstream Economic Reporting (Reuters Style)",
        "category": "Credible / Neutral Journalism",
        "headline": "Federal Reserve Holds Interest Rates Steady Amid Cooling Inflation Indicators",
        "content": "The Federal Reserve concluded its two-day Federal Open Market Committee meeting on Wednesday, voting unanimously to maintain the benchmark federal funds rate. In the post-meeting statement, Fed officials cited easing consumer price index data and stable labor market conditions as justification for holding policy steady. Economists surveyed by Reuters noted that core inflation dropped 0.2 percentage points over the past quarter, reflecting tighter credit conditions. Fed Chairman Powell emphasized during the news conference that upcoming policy decisions will remain strictly data-dependent."
    },
    {
        "id": "space-discovery",
        "title": "Peer-Reviewed Scientific Announcement",
        "category": "Credible / Science",
        "headline": "NASA James Webb Space Telescope Identifies Atmospheric Water Vapor in Exoplanet Orbit",
        "content": "Astrophysicists analyzing spectroscopic data from the James Webb Space Telescope have confirmed the presence of atmospheric water vapor on exoplanet WASP-96b, located approximately 1,150 light-years away. The peer-reviewed study, published in the journal Nature Astronomy, utilized near-infrared instruments to measure chemical absorption signatures during planetary transit. Lead researcher Dr. Elena Vance explained that while the high atmospheric temperatures make the planet uninhabitable, the precision measurements provide critical insights into planetary formation models."
    },
    {
        "id": "clickbait-finance",
        "title": "High-Urgency Financial Clickbait",
        "category": "Misinformation / Financial Clickbait",
        "headline": "YOU WON'T BELIEVE THIS: Rogue Whistleblower Exposes One Secret Trick That Instantly Eliminates All Debt!",
        "content": "Banks and Wall Street millionaires are FURIOUS after an anonymous rogue mathematician exposed this one simple secret loop-hole that completely wipes out your mortgage, credit cards, and student loans overnight! Federal authorities are scrambling to shut down this webpage immediately! Doctors and financial advisors hate him for exposing the hidden truth! Click here right now to see the shocking video before corrupt bankers take it down!"
    }
]

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "active_model": model_service.active_model_key,
        "models_available": list(model_service.models.keys())
    }

@app.get("/api/presets")
def get_presets():
    return {"presets": DEMO_PRESETS}

@app.post("/api/analyze")
async def analyze_text(request: AnalyzeTextRequest):
    headline = (request.headline or "").strip()
    content = (request.content or "").strip()

    if not headline and not content:
        raise HTTPException(status_code=400, detail="Please enter a headline or article content before analyzing.")

    total_len = len(headline) + len(content)
    if total_len > settings.MAX_TEXT_LENGTH:
        raise HTTPException(status_code=400, detail=f"Article exceeds maximum allowed length of {settings.MAX_TEXT_LENGTH} characters.")

    # 1. Run NLP & Multi-Model Inference & XAI
    analysis_result = model_service.analyze(
        headline=headline,
        content=content,
        model_name=request.model_name
    )

    # 2. Run Evidence Verification if requested
    evidence_data = {}
    if request.verify_evidence:
        evidence_data = evidence_verifier.verify_claims(headline, content or headline)
    analysis_result["evidence"] = evidence_data

    # 3. Persist record to SQLite
    record_id = save_analysis_record(
        data=analysis_result,
        headline=headline,
        content=content,
        url=""
    )
    analysis_result["id"] = record_id
    analysis_result["headline"] = headline
    analysis_result["content"] = content

    return analysis_result

@app.post("/api/analyze-url")
async def analyze_url(request: AnalyzeUrlRequest):
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Please provide a valid website URL.")

    # 1. Scrape URL
    extracted = await url_extractor.extract_from_url(url)
    if not extracted["success"]:
        return {
            "success": False,
            "error": extracted["error"],
            "url": url,
            "publisher": extracted.get("publisher", ""),
            "title": extracted.get("title", "")
        }

    headline = extracted.get("title", "")
    content = extracted.get("content", "")

    # 2. Run NLP & Model analysis
    analysis_result = model_service.analyze(
        headline=headline,
        content=content,
        model_name=request.model_name
    )

    # 3. Run Evidence Verification
    evidence_data = {}
    if request.verify_evidence:
        evidence_data = evidence_verifier.verify_claims(headline, content)
    analysis_result["evidence"] = evidence_data

    # 4. Save to Database
    record_id = save_analysis_record(
        data=analysis_result,
        headline=headline,
        content=content,
        url=url
    )

    analysis_result["id"] = record_id
    analysis_result["url"] = url
    analysis_result["headline"] = headline
    analysis_result["content"] = content
    analysis_result["url_metadata"] = {
        "publisher": extracted.get("publisher"),
        "author": extracted.get("author"),
        "published_date": extracted.get("published_date"),
        "is_https": extracted.get("is_https"),
        "domain": extracted.get("domain")
    }
    analysis_result["success"] = True

    return analysis_result

@app.get("/api/models")
def get_available_models():
    models_info = []
    benchmarks = model_service.metrics.get("models", {})
    for key, model in model_service.models.items():
        meta = benchmarks.get(key, {})
        models_info.append({
            "key": key,
            "name": meta.get("name", key),
            "type": meta.get("type", "Machine Learning Model"),
            "description": meta.get("description", ""),
            "is_active": (key == model_service.active_model_key),
            "accuracy": meta.get("accuracy", 0.0),
            "precision": meta.get("precision", 0.0),
            "recall": meta.get("recall", 0.0),
            "f1_score": meta.get("f1_score", 0.0),
            "roc_auc": meta.get("roc_auc", 0.0),
            "confusion_matrix": meta.get("confusion_matrix", {})
        })
    return {
        "active_model": model_service.active_model_key,
        "models": models_info,
        "benchmark_summary": {
            "dataset_name": model_service.metrics.get("dataset_name", "TruthLens Benchmark Dataset"),
            "total_samples": model_service.metrics.get("total_samples", 0),
            "train_samples": model_service.metrics.get("train_samples", 0),
            "test_samples": model_service.metrics.get("test_samples", 0),
            "best_model": model_service.metrics.get("best_model", "linear_svm")
        }
    }

@app.post("/api/models/switch")
def switch_active_model(request: SwitchModelRequest):
    success = model_service.set_active_model(request.model_key)
    if not success:
        raise HTTPException(status_code=400, detail=f"Model '{request.model_key}' is not available.")
    return {
        "success": True,
        "active_model": model_service.active_model_key,
        "message": f"Successfully switched default production model to '{request.model_key}'"
    }

@app.get("/api/model-performance")
def get_model_performance():
    return model_service.metrics

@app.get("/api/history")
def get_history(limit: int = Query(50, ge=1, le=200), search: str = Query("", max_length=100)):
    records = get_analyses_history(limit=limit, search=search)
    return {"history": records}

@app.get("/api/history/{record_id}")
def get_history_detail(record_id: str):
    record = get_analysis_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found.")
    return record

@app.delete("/api/history/{record_id}")
def delete_history_item(record_id: str):
    deleted = delete_analysis_by_id(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Record not found.")
    return {"success": True, "deleted_id": record_id}

@app.get("/api/dashboard-summary")
def get_dashboard_summary():
    stats = get_dashboard_summary_stats()
    return stats

@app.post("/api/analyze-instagram")
async def analyze_instagram(request: AnalyzeInstagramRequest):
    """Analyze an Instagram post link for misinformation using LLM + web search cross-referencing."""
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Please provide an Instagram post URL.")

    # Step 1: Instagram analysis pipeline (scrape + LLM + search + cross-reference)
    ig_result = await instagram_analyzer.analyze_instagram_link(url)
    if not ig_result.get("success"):
        return {
            "success": False,
            "error": ig_result.get("error", "Could not analyze this Instagram post."),
            "url": url
        }

    headline = ig_result.get("headline", "Instagram Post")
    content = ig_result.get("content", "")

    # Step 2: Run through TruthLens ML pipeline if we have enough text
    analysis_result = {}
    if len(f"{headline} {content}".strip()) >= 15:
        analysis_result = model_service.analyze(
            headline=headline,
            content=content,
            model_name=request.model_name
        )
    else:
        # Minimal result for very short content
        analysis_result = {
            "verdict": "INSUFFICIENT EVIDENCE",
            "verdict_badge_color": "gray",
            "verdict_summary": "Extracted content was too short for full ML classification. See Social Media Analysis below for LLM cross-referencing results.",
            "is_fake": False,
            "fake_percentage": 0,
            "real_percentage": 0,
            "model_confidence": 0,
            "misinformation_risk_score": 0,
            "prob_fake": 0,
            "prob_real": 0,
            "active_model": {"key": "N/A", "name": "N/A", "type": "N/A", "f1_score": 0},
            "linguistic_risk": {
                "composite_risk_score": 0,
                "linguistic_score": 0,
                "model_risk_score": 0,
                "indicators": [],
                "breakdown": {
                    "sensationalism": {"score": 0, "severity": "LOW", "matched_terms": [], "term_count": 0},
                    "clickbait": {"score": 0, "severity": "LOW", "patterns": [], "pattern_count": 0},
                    "emotional_intensity": {"score": 0, "severity": "LOW", "subjectivity": 0, "polarity": 0},
                    "punctuation_caps": {"score": 0, "severity": "LOW", "caps_ratio": 0, "caps_word_count": 0, "caps_examples": []},
                    "claim_density": {"score": 0, "severity": "LOW", "attribution_markers_found": 0, "absolute_assertions_found": 0},
                    "headline_mismatch": {"score": 0, "severity": "LOW", "overlap_ratio": 0, "mismatch_detected": False}
                }
            },
            "xai_explanation": {"top_features": [], "fake_indicators": [], "real_indicators": [], "total_active_features": 0},
            "highlighted_analysis": {"spans": [], "highlighted_html": "", "total_annotations": 0},
            "text_statistics": {"word_count": 0, "char_count": 0, "sentence_count": 0, "caps_words_count": 0, "caps_ratio": 0, "exclamation_count": 0, "question_count": 0, "avg_word_length": 0, "avg_sentence_length": 0},
            "multi_model_comparison": {},
            "explanation_bullets": ["Content extracted from Instagram was brief. Cross-referencing verdict is available."],
            "disclaimer": "Notice: Model confidence represents learned statistical classification probability based on training patterns, not philosophical or factual certainty."
        }

    # Step 3: Evidence verification
    evidence_data = {}
    if request.verify_evidence and content:
        evidence_data = evidence_verifier.verify_claims(headline, content)
    analysis_result["evidence"] = evidence_data

    # Step 4: Save to database
    record_id = save_analysis_record(
        data=analysis_result,
        headline=headline,
        content=content,
        url=url
    )

    # Step 5: Attach social media analysis data
    analysis_result["id"] = record_id
    analysis_result["url"] = url
    analysis_result["headline"] = headline
    analysis_result["content"] = content
    analysis_result["success"] = True
    analysis_result["source_type"] = "instagram"
    analysis_result["social_media_analysis"] = ig_result.get("social_media_analysis", {})
    analysis_result["similar_articles"] = ig_result.get("similar_articles", [])
    analysis_result["scraped_metadata"] = ig_result.get("scraped_metadata", {})

    return analysis_result

@app.post("/api/analyze-image")
async def analyze_image_upload(file: UploadFile = File(...), model_name: Optional[str] = None, verify_evidence: bool = True):
    """Analyze an uploaded image for misinformation using Groq Vision + web search cross-referencing."""
    if not file:
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif", "image/jpg"]
    content_type = file.content_type or ""
    if content_type not in allowed_types and not file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a JPG, PNG, or WebP image.")

    # Read image bytes (limit to 20MB)
    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image file is too large. Maximum size is 20MB.")

    if len(image_bytes) < 100:
        raise HTTPException(status_code=400, detail="The uploaded file appears to be empty or corrupted.")

    # Step 1: Vision model analysis (description + OCR + claim extraction)
    img_result = await instagram_analyzer.analyze_image(image_bytes, file.filename or "image.jpg")
    if not img_result.get("success"):
        return {
            "success": False,
            "error": img_result.get("error", "Could not analyze this image."),
        }

    headline = img_result.get("headline", "Image Analysis")
    content = img_result.get("content", "")
    extracted_text = img_result.get("image_analysis", {}).get("extracted_text", "")

    # Combine content + extracted text for ML analysis
    ml_content = content
    if extracted_text:
        ml_content = f"{content}\n\n{extracted_text}"

    # Step 2: Run through TruthLens ML pipeline if we have enough text
    analysis_result = {}
    if len(f"{headline} {ml_content}".strip()) >= 15:
        analysis_result = model_service.analyze(
            headline=headline,
            content=ml_content,
            model_name=model_name
        )
    else:
        analysis_result = {
            "verdict": "INSUFFICIENT EVIDENCE",
            "verdict_badge_color": "gray",
            "verdict_summary": "Extracted content from the image was too short for full ML classification. See Image & Social Media Analysis below.",
            "is_fake": False,
            "fake_percentage": 0,
            "real_percentage": 0,
            "model_confidence": 0,
            "misinformation_risk_score": 0,
            "prob_fake": 0,
            "prob_real": 0,
            "active_model": {"key": "N/A", "name": "N/A", "type": "N/A", "f1_score": 0},
            "linguistic_risk": {
                "composite_risk_score": 0,
                "linguistic_score": 0,
                "model_risk_score": 0,
                "indicators": [],
                "breakdown": {
                    "sensationalism": {"score": 0, "severity": "LOW", "matched_terms": [], "term_count": 0},
                    "clickbait": {"score": 0, "severity": "LOW", "patterns": [], "pattern_count": 0},
                    "emotional_intensity": {"score": 0, "severity": "LOW", "subjectivity": 0, "polarity": 0},
                    "punctuation_caps": {"score": 0, "severity": "LOW", "caps_ratio": 0, "caps_word_count": 0, "caps_examples": []},
                    "claim_density": {"score": 0, "severity": "LOW", "attribution_markers_found": 0, "absolute_assertions_found": 0},
                    "headline_mismatch": {"score": 0, "severity": "LOW", "overlap_ratio": 0, "mismatch_detected": False}
                }
            },
            "xai_explanation": {"top_features": [], "fake_indicators": [], "real_indicators": [], "total_active_features": 0},
            "highlighted_analysis": {"spans": [], "highlighted_html": "", "total_annotations": 0},
            "text_statistics": {"word_count": 0, "char_count": 0, "sentence_count": 0, "caps_words_count": 0, "caps_ratio": 0, "exclamation_count": 0, "question_count": 0, "avg_word_length": 0, "avg_sentence_length": 0},
            "multi_model_comparison": {},
            "explanation_bullets": ["Image text extraction completed. See Vision AI and Fact-Checking analysis below."],
            "disclaimer": "Notice: Model confidence represents learned statistical classification probability based on training patterns, not philosophical or factual certainty."
        }

    # Step 3: Evidence verification
    evidence_data = {}
    if verify_evidence and ml_content:
        evidence_data = evidence_verifier.verify_claims(headline, ml_content)
    analysis_result["evidence"] = evidence_data

    # Step 4: Save to database
    record_id = save_analysis_record(
        data=analysis_result,
        headline=headline,
        content=ml_content,
        url=""
    )

    # Step 5: Attach image and social media analysis data
    analysis_result["id"] = record_id
    analysis_result["headline"] = headline
    analysis_result["content"] = ml_content
    analysis_result["success"] = True
    analysis_result["source_type"] = "image_upload"
    analysis_result["image_analysis"] = img_result.get("image_analysis", {})
    analysis_result["social_media_analysis"] = img_result.get("social_media_analysis", {})
    analysis_result["similar_articles"] = img_result.get("similar_articles", [])

    return analysis_result

@app.get("/api/export-pdf/{record_id}")
def export_pdf_report(record_id: str):
    record = get_analysis_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found.")
    
    payload = record.get("full_payload", {})
    payload["headline"] = record.get("headline")
    payload["url"] = record.get("url")

    pdf_bytes = pdf_exporter.generate_pdf_bytes(payload)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=truthlens-report-{record_id[:8]}.pdf"
        }
    )

@app.post("/api/dataset/retrain")
def retrain_models(background_tasks: BackgroundTasks):
    """Triggers retraining of all 5 classifiers."""
    def run_training():
        trainer.train_all_models()
        model_service.load_artifacts()

    background_tasks.add_task(run_training)
    return {"success": True, "message": "Model training initiated in background. Artifacts and metrics will refresh once completed."}

# Mount Frontend static build if present
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
