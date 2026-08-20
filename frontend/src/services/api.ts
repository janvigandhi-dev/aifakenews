const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export interface AnalysisResponse {
  id?: string;
  verdict: 'REAL / LOW RISK' | 'SUSPICIOUS / REVIEW' | 'LIKELY MISLEADING' | 'INSUFFICIENT EVIDENCE';
  verdict_badge_color: string;
  verdict_summary: string;
  is_fake?: boolean;
  fake_percentage?: number;
  real_percentage?: number;
  model_confidence: number;
  misinformation_risk_score: number;
  prob_fake: number;
  prob_real: number;
  headline?: string;
  content?: string;
  url?: string;
  url_metadata?: {
    publisher?: string;
    author?: string;
    published_date?: string;
    is_https?: boolean;
    domain?: string;
  };
  active_model: {
    key: string;
    name: string;
    type: string;
    accuracy?: number;
    f1_score: number;
  };
  linguistic_risk: {
    composite_risk_score: number;
    linguistic_score: number;
    model_risk_score: number;
    indicators: Array<{
      name: string;
      severity: 'HIGH' | 'MEDIUM' | 'LOW';
      score: number;
      description: string;
    }>;
    breakdown: {
      sensationalism: { score: number; severity: string; matched_terms: any[]; term_count: number };
      clickbait: { score: number; severity: string; patterns: any[]; pattern_count: number };
      emotional_intensity: { score: number; severity: string; subjectivity: number; polarity: number };
      punctuation_caps: { score: number; severity: string; caps_ratio: number; caps_word_count: number; caps_examples: string[] };
      claim_density: { score: number; severity: string; attribution_markers_found: number; absolute_assertions_found: number };
      headline_mismatch: { score: number; severity: string; overlap_ratio: number; mismatch_detected: boolean };
    };
  };
  xai_explanation: {
    top_features: Array<{
      term: string;
      weight: number;
      direction: 'MISLEADING' | 'CREDIBLE';
      magnitude: number;
    }>;
    fake_indicators: Array<{ term: string; weight: number; impact: string }>;
    real_indicators: Array<{ term: string; weight: number; impact: string }>;
    total_active_features: number;
  };
  highlighted_analysis: {
    spans: Array<{
      start: number;
      end: number;
      text: string;
      type: string;
      category: string;
      severity: string;
      description: string;
    }>;
    highlighted_html: string;
    total_annotations: number;
  };
  text_statistics: {
    word_count: number;
    char_count: number;
    sentence_count: number;
    caps_words_count: number;
    caps_ratio: number;
    exclamation_count: number;
    question_count: number;
    avg_word_length: number;
    avg_sentence_length: number;
  };
  multi_model_comparison: Record<string, {
    model_name: string;
    model_type: string;
    prediction: 'MISLEADING' | 'CREDIBLE';
    prob_fake: number;
    prob_real: number;
    confidence: number;
    f1_score: number;
  }>;
  explanation_bullets: string[];
  evidence?: {
    overall_evidence_verdict?: string;
    confidence_score?: number;
    summary_reasoning?: string;
    claims?: Array<{
      claim: string;
      stance: string;
      evidence_assessment: string;
      plausibility: string;
      suggested_sources: string[];
    }>;
    source_references?: Array<{
      title: string;
      domain: string;
      relationship: string;
    }>;
    engine?: string;
  };
  disclaimer: string;
}

export const api = {
  async checkHealth() {
    const res = await fetch(`${API_BASE_URL}/api/health`);
    return res.json();
  },

  async getPresets() {
    const res = await fetch(`${API_BASE_URL}/api/presets`);
    return res.json();
  },

  async analyzeText(payload: { headline?: string; content?: string; model_name?: string; verify_evidence?: boolean }): Promise<AnalysisResponse> {
    const res = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Analysis request failed');
    }
    return res.json();
  },

  async analyzeUrl(payload: { url: string; model_name?: string; verify_evidence?: boolean }): Promise<AnalysisResponse> {
    const res = await fetch(`${API_BASE_URL}/api/analyze-url`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'URL analysis request failed');
    }
    const data = await res.json();
    if (data.success === false) {
      throw new Error(data.error || 'Failed to extract content from URL');
    }
    return data;
  },

  async getModels() {
    const res = await fetch(`${API_BASE_URL}/api/models`);
    return res.json();
  },

  async switchModel(modelKey: string) {
    const res = await fetch(`${API_BASE_URL}/api/models/switch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model_key: modelKey })
    });
    return res.json();
  },

  async getModelPerformance() {
    const res = await fetch(`${API_BASE_URL}/api/model-performance`);
    return res.json();
  },

  async getHistory(search = '', limit = 50) {
    const params = new URLSearchParams({ search, limit: limit.toString() });
    const res = await fetch(`${API_BASE_URL}/api/history?${params}`);
    return res.json();
  },

  async getHistoryDetail(id: string) {
    const res = await fetch(`${API_BASE_URL}/api/history/${id}`);
    return res.json();
  },

  async deleteHistoryItem(id: string) {
    const res = await fetch(`${API_BASE_URL}/api/history/${id}`, { method: 'DELETE' });
    return res.json();
  },

  async getDashboardSummary() {
    const res = await fetch(`${API_BASE_URL}/api/dashboard-summary`);
    return res.json();
  },

  async retrainModels() {
    const res = await fetch(`${API_BASE_URL}/api/dataset/retrain`, { method: 'POST' });
    return res.json();
  },

  getPdfExportUrl(id: string) {
    return `${API_BASE_URL}/api/export-pdf/${id}`;
  }
};
