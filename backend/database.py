import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.config import BASE_DIR

DB_PATH = BASE_DIR / "truthlens.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analyses (
        id TEXT PRIMARY KEY,
        headline TEXT,
        content_preview TEXT,
        url TEXT,
        verdict TEXT,
        verdict_badge_color TEXT,
        confidence REAL,
        risk_score REAL,
        model_used TEXT,
        full_payload TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id TEXT PRIMARY KEY,
        analysis_id TEXT,
        user_rating TEXT,
        comments TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (analysis_id) REFERENCES analyses (id)
    );
    """)

    conn.commit()
    conn.close()

def save_analysis_record(data: Dict[str, Any], headline: str = "", content: str = "", url: str = "") -> str:
    record_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()

    content_preview = content[:250] + "..." if len(content) > 250 else content
    
    cursor.execute("""
    INSERT INTO analyses (
        id, headline, content_preview, url, verdict, verdict_badge_color,
        confidence, risk_score, model_used, full_payload, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record_id,
        headline or (url if url else "Untitled Submission"),
        content_preview,
        url,
        data.get("verdict", "REVIEW"),
        data.get("verdict_badge_color", "amber"),
        data.get("model_confidence", 0.0),
        data.get("misinformation_risk_score", 0.0),
        data.get("active_model", {}).get("name", "Linear SVM"),
        json.dumps(data),
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()
    return record_id

def get_analyses_history(limit: int = 50, search: str = "") -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()

    if search.strip():
        query = "%" + search.strip().lower() + "%"
        cursor.execute("""
        SELECT id, headline, content_preview, url, verdict, verdict_badge_color,
               confidence, risk_score, model_used, created_at
        FROM analyses
        WHERE LOWER(headline) LIKE ? OR LOWER(content_preview) LIKE ? OR LOWER(url) LIKE ?
        ORDER BY created_at DESC LIMIT ?
        """, (query, query, query, limit))
    else:
        cursor.execute("""
        SELECT id, headline, content_preview, url, verdict, verdict_badge_color,
               confidence, risk_score, model_used, created_at
        FROM analyses
        ORDER BY created_at DESC LIMIT ?
        """, (limit,))

    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results

def get_analysis_by_id(record_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analyses WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    
    item = dict(row)
    if item.get("full_payload"):
        try:
            item["full_payload"] = json.loads(item["full_payload"])
        except Exception:
            pass
    return item

def delete_analysis_by_id(record_id: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM analyses WHERE id = ?", (record_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_dashboard_summary_stats() -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM analyses")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM analyses WHERE verdict = 'LIKELY MISLEADING'")
    misleading = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM analyses WHERE verdict = 'REAL / LOW RISK'")
    real = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM analyses WHERE verdict LIKE 'SUSPICIOUS%' OR verdict = 'INSUFFICIENT EVIDENCE'")
    review = cursor.fetchone()[0]

    conn.close()
    return {
        "total_analyzed": total,
        "likely_misleading": misleading,
        "low_risk": real,
        "needs_review": review
    }

# Initialize on module load
init_db()
