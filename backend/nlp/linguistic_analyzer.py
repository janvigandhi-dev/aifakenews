import re
import math
from typing import Dict, List, Any, Tuple
from textblob import TextBlob

# Sensational Lexicon with weights
SENSATIONAL_LEXICON = {
    # Extreme hyperbole / bombshells
    "shocking": 0.85, "explosive": 0.85, "bombshell": 0.90, "unbelievable": 0.80,
    "mind-blowing": 0.85, "jaw-dropping": 0.85, "insane": 0.75, "devastating": 0.70,
    "miracle": 0.80, "miraculous": 0.80, "catastrophic": 0.75, "apocalyptic": 0.85,
    "shattering": 0.75, "horrifying": 0.80, "terrifying": 0.80, "monstrous": 0.75,
    
    # Conspiracy / Cover-up / Secrecy
    "secret": 0.70, "cover-up": 0.90, "coverup": 0.90, "exposed": 0.85, "unmasked": 0.80,
    "conspiracy": 0.80, "hidden truth": 0.90, "hiding": 0.65, "banned": 0.75, "censored": 0.80,
    "silenced": 0.80, "suppressed": 0.85, "whistleblower leaks": 0.90, "treason": 0.85,
    "deep state": 0.90, "rigged": 0.85, "hoax": 0.85, "propaganda": 0.70,
    "they don't want you to know": 0.95, "what they won't tell you": 0.95,
    "mainstream media won't": 0.90, "media blackout": 0.90,
    
    # Urgency / Call-to-Arms
    "urgent": 0.70, "warning": 0.60, "danger": 0.60, "red alert": 0.85,
    "spread this": 0.90, "share before it's deleted": 0.98, "viral": 0.60,
    "must read": 0.75, "wake up": 0.85, "sheeple": 0.95, "panic": 0.75,
    
    # Absolute False Certainty / Magic cures
    "100% cure": 0.95, "cures everything": 0.98, "instant cure": 0.95,
    "guaranteed": 0.70, "undeniable proof": 0.90, "indisputable fact": 0.85,
    "proves once and for all": 0.90, "scientific breakthrough doctors hate": 0.98
}

# Clickbait Regex Patterns
CLICKBAIT_PATTERNS = [
    (r"\b(?:you\s+won'?t\s+believe|can'?t\s+believe\s+what)\b", 0.95, "Disbelief hook ('You won't believe')"),
    (r"\b(?:this\s+one\s+(?:trick|secret|food|hack|remedy))\b", 0.90, "Single-secret hook ('This one trick')"),
    (r"\b(?:what\s+happened\s+next\s+will|will\s+blow\s+your\s+mind)\b", 0.95, "Emotional suspense hook"),
    (r"\b(?:doctors|scientists|experts|banks|cops)\s+(?:hate\s+(?:this|him|her)|don'?t\s+want\s+you\s+to\s+know)\b", 0.98, "Authority opposition hook"),
    (r"\b(?:here'?s\s+the\s+real\s+reason\s+why|the\s+truth\s+about)\b", 0.65, "Exclusive truth framing"),
    (r"\b(?:number\s+\d+\s+will\s+(?:shock|amaze|stun)\s+you)\b", 0.95, "Listicle curiosity cliffhanger"),
    (r"\b(?:see\s+why\s+everyone\s+is\s+(?:talking\s+about|furious|outraged))\b", 0.85, "Bandwagon outrage hook"),
    (r"\b(?:is\s+this\s+the\s+end\s+of)\b", 0.75, "Alarmist open question"),
    (r"\b(?:break(?:s|ing)?\s+the\s+internet)\b", 0.80, "Hyperbolic virality claim"),
    (r"\b(?:before\s+it(?:'?s|\s+is)\s+(?:banned|taken\s+down|deleted))\b", 0.95, "Artificial scarcity/censorship trigger")
]

# Credibility Markers (Words associated with journalistic neutrality)
CREDIBILITY_MARKERS = [
    "according to", "spokesperson", "statement", "reuters", "associated press", "ap news", 
    "official said", "study published in", "peer-reviewed", "department of", "investigation", 
    "cited data", "statistics indicate", "preliminary findings", "confirmed by", "disclosed"
]

class LinguisticAnalyzer:
    def __init__(self):
        pass

    def analyze_sensationalism(self, text: str) -> Dict[str, Any]:
        """Scans for sensational, hyperbolic, and conspiratorial terms."""
        lower_text = text.lower()
        found_terms = []
        total_weight = 0.0

        for term, weight in SENSATIONAL_LEXICON.items():
            # Check whole word or phrase match
            pattern = r'\b' + re.escape(term) + r'\b'
            matches = list(re.finditer(pattern, lower_text))
            if matches:
                count = len(matches)
                total_weight += weight * count
                found_terms.append({
                    "term": term,
                    "count": count,
                    "weight": weight,
                    "severity": "HIGH" if weight >= 0.85 else "MEDIUM"
                })

        words_count = max(len(re.findall(r'\b\w+\b', text)), 1)
        normalized_score = min(round((total_weight / math.sqrt(words_count)) * 25, 2), 100.0)

        severity = "LOW"
        if normalized_score >= 50 or total_weight >= 2.5:
            severity = "HIGH"
        elif normalized_score >= 20 or total_weight >= 1.0:
            severity = "MEDIUM"

        return {
            "score": normalized_score,
            "severity": severity,
            "matched_terms": found_terms,
            "term_count": len(found_terms)
        }

    def analyze_clickbait(self, text: str, headline: str = "") -> Dict[str, Any]:
        """Evaluates text and headline for common clickbait framing patterns."""
        combined = f"{headline} {text}".strip()
        matched_patterns = []
        total_weight = 0.0

        for pattern_regex, weight, desc in CLICKBAIT_PATTERNS:
            if re.search(pattern_regex, combined, re.IGNORECASE):
                matched_patterns.append({
                    "description": desc,
                    "weight": weight
                })
                total_weight += weight

        score = min(round(total_weight * 30, 2), 100.0)
        severity = "LOW"
        if score >= 60:
            severity = "HIGH"
        elif score >= 25:
            severity = "MEDIUM"

        return {
            "score": score,
            "severity": severity,
            "patterns": matched_patterns,
            "pattern_count": len(matched_patterns)
        }

    def analyze_emotional_intensity(self, text: str) -> Dict[str, Any]:
        """Calculates emotional intensity and sentiment subjectivity using TextBlob."""
        if not text.strip():
            return {"score": 0.0, "severity": "LOW", "subjectivity": 0.0, "polarity": 0.0}

        blob = TextBlob(text)
        sentiment = blob.sentiment
        subjectivity = sentiment.subjectivity  # 0.0 (objective) to 1.0 (highly subjective)
        polarity = sentiment.polarity          # -1.0 (negative) to 1.0 (positive)

        # Emotional intensity is higher when text is highly subjective and highly polarized
        intensity = subjectivity * 60 + abs(polarity) * 40
        intensity_score = min(round(intensity, 2), 100.0)

        severity = "LOW"
        if intensity_score >= 65:
            severity = "HIGH"
        elif intensity_score >= 35:
            severity = "MEDIUM"

        return {
            "score": intensity_score,
            "severity": severity,
            "subjectivity": round(subjectivity, 3),
            "polarity": round(polarity, 3)
        }

    def analyze_punctuation_and_caps(self, text: str, headline: str = "") -> Dict[str, Any]:
        """Detects anomalies in capitalization (ALL CAPS shouting) and repeated punctuation (!?, !!!)."""
        words = re.findall(r'\b[A-Za-z0-9]+\b', text)
        headline_words = re.findall(r'\b[A-Za-z0-9]+\b', headline)
        
        all_words = words + headline_words
        total_words = max(len(all_words), 1)

        # Multi-character caps words (>1 char, exclude common acronyms like US, UK, UN, NASA, FBI, CIA, AI, COVID)
        standard_acronyms = {"US", "UK", "UN", "EU", "NASA", "FBI", "CIA", "AI", "COVID", "WHO", "NATO", "CDC", "FDA", "CEO", "PM", "USA"}
        caps_words = [w for w in all_words if len(w) > 1 and w.isupper() and w not in standard_acronyms]
        caps_ratio = len(caps_words) / total_words

        # Punctuation anomalies
        combined = f"{headline} {text}"
        multi_exclamation = len(re.findall(r'!{2,}', combined))
        multi_question = len(re.findall(r'\?{2,}', combined))
        mixed_punctuation = len(re.findall(r'[!?]{2,}', combined))
        single_exclamation = combined.count('!')

        # Penalty score
        penalty = 0.0
        if caps_ratio > 0.15:
            penalty += 40.0
        elif caps_ratio > 0.06:
            penalty += 20.0

        penalty += min(multi_exclamation * 20.0 + multi_question * 15.0 + mixed_punctuation * 15.0 + single_exclamation * 3.0, 50.0)
        score = min(round(penalty, 2), 100.0)

        severity = "LOW"
        if score >= 50 or caps_ratio > 0.20:
            severity = "HIGH"
        elif score >= 20:
            severity = "MEDIUM"

        return {
            "score": score,
            "severity": severity,
            "caps_ratio": round(caps_ratio, 3),
            "caps_word_count": len(caps_words),
            "caps_examples": caps_words[:6],
            "multi_exclamation_count": multi_exclamation,
            "multi_question_count": multi_question
        }

    def analyze_claim_density(self, text: str) -> Dict[str, Any]:
        """Estimates assertion density vs neutral attribution."""
        lower_text = text.lower()
        words_count = max(len(re.findall(r'\b\w+\b', text)), 1)
        
        # Count credibility/attribution markers
        cred_matches = 0
        for marker in CREDIBILITY_MARKERS:
            if marker in lower_text:
                cred_matches += 1

        # Count unhedged absolute assertions
        absolutes = ["proves", "undoubtedly", "absolutely", "guaranteed", "unquestionably", "incontestable", "100%", "everyone knows"]
        abs_matches = sum(1 for a in absolutes if a in lower_text)

        # High claim density with low attribution increases risk
        ratio = (abs_matches * 2) - (cred_matches * 0.8)
        raw_score = 30.0 + (ratio * 12.0)
        score = max(0.0, min(round(raw_score, 2), 100.0))

        severity = "LOW"
        if score >= 60:
            severity = "HIGH"
        elif score >= 40:
            severity = "MEDIUM"

        return {
            "score": score,
            "severity": severity,
            "attribution_markers_found": cred_matches,
            "absolute_assertions_found": abs_matches
        }

    def check_headline_body_mismatch(self, headline: str, body: str) -> Dict[str, Any]:
        """Checks lexical overlap between headline and body to detect bait-and-switch mismatch."""
        if not headline.strip() or not body.strip():
            return {"score": 0.0, "severity": "LOW", "overlap_ratio": 1.0, "mismatch_detected": False}

        h_words = set(re.findall(r'\b[a-z]{3,}\b', headline.lower()))
        b_words = set(re.findall(r'\b[a-z]{3,}\b', body.lower()))

        if not h_words:
            return {"score": 0.0, "severity": "LOW", "overlap_ratio": 1.0, "mismatch_detected": False}

        intersection = h_words.intersection(b_words)
        overlap_ratio = len(intersection) / len(h_words)

        score = 0.0
        severity = "LOW"
        mismatch = False

        # If less than 25% of headline keywords appear in body of reasonable length
        if len(b_words) > 30 and overlap_ratio < 0.25:
            score = 65.0
            severity = "HIGH"
            mismatch = True
        elif len(b_words) > 30 and overlap_ratio < 0.45:
            score = 35.0
            severity = "MEDIUM"

        return {
            "score": score,
            "severity": severity,
            "overlap_ratio": round(overlap_ratio, 2),
            "mismatch_detected": mismatch
        }

    def compute_composite_risk_score(self, text: str, headline: str = "", model_prob_fake: float = 0.5) -> Dict[str, Any]:
        """Computes comprehensive 6-dimensional linguistic risk profile and composite risk score (0-100)."""
        sensational = self.analyze_sensationalism(f"{headline} {text}")
        clickbait = self.analyze_clickbait(text, headline)
        emotion = self.analyze_emotional_intensity(f"{headline} {text}")
        punct_caps = self.analyze_punctuation_and_caps(text, headline)
        claims = self.analyze_claim_density(text)
        mismatch = self.check_headline_body_mismatch(headline, text)

        # Weighted combination of linguistic factors (60%) and Model probability (40%)
        linguistic_weighted = (
            sensational["score"] * 0.28 +
            clickbait["score"] * 0.24 +
            emotion["score"] * 0.18 +
            punct_caps["score"] * 0.14 +
            claims["score"] * 0.10 +
            mismatch["score"] * 0.06
        )

        model_score = model_prob_fake * 100.0
        composite_risk = (linguistic_weighted * 0.55) + (model_score * 0.45)
        composite_risk = max(0.0, min(round(composite_risk, 1), 100.0))

        # Generate summary risk indicators list for UI
        active_indicators = []
        if sensational["severity"] in ["HIGH", "MEDIUM"]:
            active_indicators.append({
                "name": "Sensational Language",
                "severity": sensational["severity"],
                "score": sensational["score"],
                "description": f"Found {sensational['term_count']} sensational/hyperbolic phrases."
            })
        if clickbait["severity"] in ["HIGH", "MEDIUM"]:
            active_indicators.append({
                "name": "Clickbait Patterns",
                "severity": clickbait["severity"],
                "score": clickbait["score"],
                "description": f"Identified {clickbait['pattern_count']} curiosity-gap or emotional clickbait hooks."
            })
        if emotion["severity"] in ["HIGH", "MEDIUM"]:
            active_indicators.append({
                "name": "High Emotional Intensity",
                "severity": emotion["severity"],
                "score": emotion["score"],
                "description": f"Text exhibits elevated subjectivity ({emotion['subjectivity']}) and emotional valence."
            })
        if punct_caps["severity"] in ["HIGH", "MEDIUM"]:
            active_indicators.append({
                "name": "Excessive Punctuation/Capitalization",
                "severity": punct_caps["severity"],
                "score": punct_caps["score"],
                "description": f"Contains uppercase emphasis words ({punct_caps['caps_word_count']}) or repeated punctuation."
            })
        if mismatch["mismatch_detected"]:
            active_indicators.append({
                "name": "Headline-Body Mismatch",
                "severity": mismatch["severity"],
                "score": mismatch["score"],
                "description": "Low semantic keyword overlap between headline and article body."
            })
        if claims["severity"] == "HIGH":
            active_indicators.append({
                "name": "Unsubstantiated Assertions",
                "severity": claims["severity"],
                "score": claims["score"],
                "description": "High frequency of absolute assertion terms with minimal neutral attribution."
            })

        return {
            "composite_risk_score": composite_risk,
            "linguistic_score": round(linguistic_weighted, 1),
            "model_risk_score": round(model_score, 1),
            "indicators": active_indicators,
            "breakdown": {
                "sensationalism": sensational,
                "clickbait": clickbait,
                "emotional_intensity": emotion,
                "punctuation_caps": punct_caps,
                "claim_density": claims,
                "headline_mismatch": mismatch
            }
        }

linguistic_analyzer = LinguisticAnalyzer()
