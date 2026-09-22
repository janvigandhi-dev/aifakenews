import json
import re
from typing import Dict, List, Any, Optional
from groq import Groq
from backend.config import settings

class EvidenceVerifier:
    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self):
        key = settings.GROQ_API_KEY
        if key:
            try:
                self.client = Groq(api_key=key)
            except Exception as e:
                print(f"[EvidenceVerifier] Groq initialization warning: {e}")

    def deep_analyze_with_groq(self, headline: str, content: str) -> Optional[Dict[str, Any]]:
        """
        Comprehensive AI Analysis using Groq LLM:
        - Factual validation & Fake News Boolean (is_fake = True/False)
        - Probability distribution (fake_percentage vs real_percentage)
        - Linguistic manipulation, clickbait & emotional intensity
        - Atomic claim extraction & stance checking
        - Key highlighted phrases
        """
        if not self.client and settings.GROQ_API_KEY:
            self._init_client()

        if not self.client:
            return None

        combined = f"Headline: {headline}\n\nContent:\n{content[:4000]}"

        prompt = f"""You are TruthLens, the world's most accurate Explainable AI News & Misinformation Analysis Engine.
Analyze the following news text for factual veracity, misinformation patterns, sensationalism, clickbait hooks, and source credibility.

NEWS TEXT:
{combined}

Return a STRICT JSON response adhering to this schema:
{{
  "is_fake": true | false,
  "verdict": "LIKELY MISLEADING" | "SUSPICIOUS / REVIEW" | "REAL / LOW RISK",
  "fake_percentage": 85.0,
  "real_percentage": 15.0,
  "misinformation_risk_score": 85.0,
  "confidence": 92.0,
  "verdict_summary": "Concise 1-2 sentence overall verdict explaining the decision.",
  "explanation_bullets": [
    "Specific reason 1 explaining why this is fake or real",
    "Specific reason 2 citing missing attribution, conspiracy, or confirmed sources",
    "Specific reason 3 analyzing emotional/clickbait tone"
  ],
  "claims": [
    {{
      "claim": "Extracted atomic factual claim",
      "stance": "SUPPORTED" | "CONTRADICTED" | "UNVERIFIED",
      "evidence_assessment": "Explanation of why this claim is supported, refuted, or unverified.",
      "plausibility": "HIGH" | "LOW" | "UNKNOWN",
      "suggested_sources": ["Reuters", "Associated Press", "Nature", "WHO", "Official Archives"]
    }}
  ],
  "flagged_phrases": [
    {{
      "text": "exact phrase from text",
      "category": "Sensational Language" | "Clickbait Hook" | "False Claim" | "Exaggerated Assertion",
      "severity": "HIGH" | "MEDIUM",
      "reason": "Why this specific phrase was flagged"
    }}
  ],
  "linguistic_metrics": {{
    "sensationalism_severity": "HIGH" | "MEDIUM" | "LOW",
    "sensationalism_score": 80.0,
    "clickbait_severity": "HIGH" | "MEDIUM" | "LOW",
    "clickbait_score": 75.0,
    "emotional_intensity_severity": "HIGH" | "MEDIUM" | "LOW",
    "emotional_score": 70.0,
    "formatting_severity": "HIGH" | "MEDIUM" | "LOW",
    "formatting_score": 50.0
  }}
}}

Respond with raw JSON only. Do not include markdown code fences or conversational text."""

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a neutral, highly rigorous explainable AI fake-news fact-checking engine. You MUST output a single valid JSON object strictly matching the required schema."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=settings.GROQ_MODEL,
                temperature=0.1,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )

            raw_resp = chat_completion.choices[0].message.content.strip()
            result = json.loads(raw_resp)
            result["engine"] = f"Groq AI Intelligence Engine ({settings.GROQ_MODEL})"
            return result

        except Exception as e:
            print(f"[EvidenceVerifier] Groq API call error: {e}")
            try:
                # Fallback lenient regex match
                cleaned_json = re.sub(r'^```(?:json)?\s*', '', raw_resp, flags=re.MULTILINE)
                cleaned_json = re.sub(r'\s*```$', '', cleaned_json, flags=re.MULTILINE)
                json_match = re.search(r'(\{[\s\S]*\})', cleaned_json)
                if json_match:
                    res = json.loads(json_match.group(1))
                    res["engine"] = f"Groq AI Intelligence Engine ({settings.GROQ_MODEL})"
                    return res
            except Exception:
                pass

        return None

    def verify_claims(self, headline: str, content: str) -> Dict[str, Any]:
        """Legacy compatibility method returning claims format."""
        groq_res = self.deep_analyze_with_groq(headline, content)
        if groq_res:
            return {
                "overall_evidence_verdict": "CONTRADICTED" if groq_res.get("is_fake") else "SUPPORTED",
                "confidence_score": groq_res.get("confidence", 85),
                "summary_reasoning": groq_res.get("verdict_summary", ""),
                "claims": groq_res.get("claims", []),
                "engine": groq_res.get("engine", "Groq AI Engine")
            }
        
        return self._fallback_evidence_verification(headline, content)

    def _fallback_evidence_verification(self, headline: str, content: str) -> Dict[str, Any]:
        """Heuristic rule-based evidence verification fallback."""
        text_lower = f"{headline} {content}".lower()
        claims = []
        overall_stance = "MIXED / REQUIRES VERIFICATION"
        
        if any(w in text_lower for w in ["secret cancer cure", "100% cure", "mind control", "alien city", "banned by oil", "whistleblower"]):
            overall_stance = "CONTRADICTED"
            claims.append({
                "claim": headline or "Sensational secret medical or scientific breakthrough",
                "stance": "CONTRADICTED",
                "evidence_assessment": "Scientific and peer-reviewed consensus contradicts claims of secret universal panaceas or hidden technological suppression.",
                "plausibility": "LOW",
                "suggested_sources": ["World Health Organization", "National Institutes of Health", "PubMed"]
            })
        elif any(w in text_lower for w in ["according to", "reuters", "associated press", "study published", "federal reserve", "nasa"]):
            overall_stance = "SUPPORTED"
            claims.append({
                "claim": headline or "Institutional or regulatory policy announcement",
                "stance": "SUPPORTED",
                "evidence_assessment": "Attributes verifiable reporting patterns and aligned official agency disclosures.",
                "plausibility": "HIGH",
                "suggested_sources": ["Reuters", "Associated Press", "Official Agency Archives"]
            })
        else:
            claims.append({
                "claim": headline or "General assertion requiring primary source validation",
                "stance": "UNVERIFIED",
                "evidence_assessment": "Claim lacks immediate verifiable citations or corroborated secondary wire reporting.",
                "plausibility": "UNKNOWN",
                "suggested_sources": ["International Fact-Checking Network", "Official Statistical Repositories"]
            })

        return {
            "overall_evidence_verdict": overall_stance,
            "confidence_score": 75,
            "summary_reasoning": "Heuristic claim analysis completed. Verify key assertions with accredited primary sources.",
            "claims": claims,
            "source_references": [
                {
                    "title": "International Fact-Checking Network (IFCN)",
                    "domain": "poynter.org",
                    "relationship": "Standards & Code of Principles"
                },
                {
                    "title": "Reuters Fact Check & AP Verification",
                    "domain": "reuters.com/fact-check",
                    "relationship": "Independent Wire Verification"
                }
            ],
            "engine": "TruthLens Heuristic Analyzer (Local Fallback)"
        }

evidence_verifier = EvidenceVerifier()
