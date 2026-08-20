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
