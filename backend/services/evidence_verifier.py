import json
import re
from typing import Dict, List, Any, Optional
from groq import Groq
from backend.config import settings

class EvidenceVerifier:
    def __init__(self):
        self.client = None
        if settings.GROQ_API_KEY:
            try:
                self.client = Groq(api_key=settings.GROQ_API_KEY)
            except Exception as e:
                print(f"[EvidenceVerifier] Groq initialization warning: {e}")

    def verify_claims(self, headline: str, content: str) -> Dict[str, Any]:
        """
        Extracts key atomic claims from article text and analyzes evidence status:
        - SUPPORTED
        - CONTRADICTED
        - REQUIRES VERIFICATION / UNCLEAR
        """
        combined = f"Headline: {headline}\n\nContent:\n{content[:3500]}"

        if self.client:
            try:
                prompt = f"""You are the Evidence Verification Engine of TruthLens, an Explainable AI Fake News Detection Platform.
Analyze the following news text, extract 2 to 3 central factual claims, assess each claim's credibility against established factual knowledge, and identify authoritative source domains.

TEXT TO ANALYZE:
{combined}

Return a valid JSON object with this exact schema:
{{
  "overall_evidence_verdict": "SUPPORTED" | "CONTRADICTED" | "MIXED / REQUIRES VERIFICATION",
  "confidence_score": 85,
  "summary_reasoning": "Concise 1-2 sentence evidence synthesis.",
  "claims": [
    {{
      "claim": "Extracted atomic factual claim",
      "stance": "SUPPORTED" | "CONTRADICTED" | "UNVERIFIED",
      "evidence_assessment": "Explanation of why this claim is supported or contradicted.",
      "plausibility": "HIGH" | "LOW" | "UNKNOWN",
      "suggested_sources": ["Reuters", "Associated Press", "Nature", "CDC"]
    }}
  ],
  "source_references": [
    {{
      "title": "Authoritative Reference Body or Database",
      "domain": "reuters.com / cdc.gov / nasa.gov / who.int",
      "relationship": "Confirms / Refutes / Clarifies"
    }}
  ]
}}
Respond with JSON only."""

                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional fact-checking analysis engine. Respond with raw JSON only."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model=settings.GROQ_MODEL,
                    temperature=0.1,
                    max_tokens=1000
                )

                raw_resp = chat_completion.choices[0].message.content.strip()
                # Clean possible markdown fences
                cleaned_json = re.sub(r'^```(?:json)?\s*', '', raw_resp, flags=re.MULTILINE)
                cleaned_json = re.sub(r'\s*```$', '', cleaned_json, flags=re.MULTILINE)
                
                # Find JSON bounds
                json_match = re.search(r'(\{[\s\S]*\})', cleaned_json)
                if json_match:
                    result = json.loads(json_match.group(1))
                    result["engine"] = f"Groq AI Evidence Engine ({settings.GROQ_MODEL})"
                    return result
                else:
                    return self._fallback_evidence_verification(headline, content)

            except Exception as e:
                print(f"[EvidenceVerifier] Groq API fallback triggered: {e}")
                return self._fallback_evidence_verification(headline, content)
        else:
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
            "engine": "TruthLens Heuristic Evidence Analyzer (Local Fallback)"
        }

evidence_verifier = EvidenceVerifier()
