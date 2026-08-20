import re
import html
from typing import List, Dict, Any
from backend.nlp.linguistic_analyzer import SENSATIONAL_LEXICON, CLICKBAIT_PATTERNS

class TextHighlighter:
    def __init__(self):
        pass

    def annotate_spans(self, raw_text: str, top_xai_terms: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Identifies suspicious phrases, clickbait patterns, and XAI tokens in raw text."""
        if not raw_text:
            return {"spans": [], "highlighted_html": ""}

        spans = []
        lower_text = raw_text.lower()

        # 1. Sensational Lexicon spans
        for term, weight in SENSATIONAL_LEXICON.items():
            pattern = r'\b' + re.escape(term) + r'\b'
            for match in re.finditer(pattern, lower_text):
                start, end = match.span()
                spans.append({
                    "start": start,
                    "end": end,
                    "text": raw_text[start:end],
                    "type": "sensational",
                    "category": "Sensational Language",
                    "severity": "HIGH" if weight >= 0.85 else "MEDIUM",
                    "score": weight,
                    "description": f"Sensational or conspiratorial phrase (weight: {weight})"
                })

        # 2. Clickbait Pattern spans
        for pattern_regex, weight, desc in CLICKBAIT_PATTERNS:
            for match in re.finditer(pattern_regex, raw_text, re.IGNORECASE):
                start, end = match.span()
                spans.append({
                    "start": start,
                    "end": end,
                    "text": raw_text[start:end],
                    "type": "clickbait",
                    "category": "Clickbait Hook",
                    "severity": "HIGH" if weight >= 0.85 else "MEDIUM",
                    "score": weight,
                    "description": desc
                })

        # 3. Punctuation anomalies (e.g. !!! or ???)
        for match in re.finditer(r'[!?]{2,}', raw_text):
            start, end = match.span()
            spans.append({
                "start": start,
                "end": end,
                "text": raw_text[start:end],
                "type": "punctuation",
                "category": "Excessive Punctuation",
                "severity": "HIGH" if (end - start) >= 3 else "MEDIUM",
                "score": 0.7,
                "description": f"Repeated punctuation anomaly ({raw_text[start:end]})"
            })

        # 4. ALL-CAPS shout words (length >= 3, excluding common acronyms)
        standard_acronyms = {"USA", "FBI", "CIA", "NASA", "WHO", "COVID", "NATO", "CDC", "FDA", "CEO", "UN"}
        for match in re.finditer(r'\b[A-Z]{3,}\b', raw_text):
            word = match.group()
            if word not in standard_acronyms:
                start, end = match.span()
                spans.append({
                    "start": start,
                    "end": end,
                    "text": word,
                    "type": "caps",
                    "category": "Uppercase Shouting",
                    "severity": "MEDIUM",
                    "score": 0.6,
                    "description": f"All-caps emphasis word: {word}"
                })

        # 5. Top XAI predictive terms if provided
        if top_xai_terms:
            for item in top_xai_terms:
                term = item.get("term", "")
                if term and len(term) > 2:
                    pattern = r'\b' + re.escape(term) + r'\b'
                    for match in re.finditer(pattern, lower_text):
                        start, end = match.span()
                        spans.append({
                            "start": start,
                            "end": end,
                            "text": raw_text[start:end],
                            "type": "xai_term",
                            "category": "Model Feature Signal",
                            "severity": "HIGH" if item.get("direction") == "MISLEADING" else "LOW",
                            "score": item.get("magnitude", 0.5),
                            "description": f"Model identified '{term}' as a strong {item.get('direction', 'signal').lower()} indicator."
                        })

        # Resolve overlaps by prioritizing longest match and highest severity
        resolved_spans = self._resolve_overlapping_spans(spans)
        
        # Generate clean highlighted HTML
        highlighted_html = self._generate_html(raw_text, resolved_spans)

        return {
            "spans": resolved_spans,
            "highlighted_html": highlighted_html,
            "total_annotations": len(resolved_spans)
        }

    def _resolve_overlapping_spans(self, spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Removes overlapping intervals by keeping longer & higher severity spans."""
        if not spans:
            return []

        # Sort primarily by start asc, length desc
        sorted_spans = sorted(spans, key=lambda s: (s["start"], -(s["end"] - s["start"])))
        resolved = []
        last_end = -1

        for s in sorted_spans:
            if s["start"] >= last_end:
                resolved.append(s)
                last_end = s["end"]
            else:
                # Overlap detected: check if current is strictly longer
                if resolved and (s["end"] - s["start"]) > (resolved[-1]["end"] - resolved[-1]["start"]):
                    resolved[-1] = s
                    last_end = s["end"]

        return resolved

    def _generate_html(self, text: str, spans: List[Dict[str, Any]]) -> str:
        """Constructs an accessible HTML string with colored highlight badges and tooltips."""
        if not spans:
            return html.escape(text)

        result = []
        last_idx = 0

        for span in spans:
            start = span["start"]
            end = span["end"]
            
            # Append preceding plain text
            if start > last_idx:
                result.append(html.escape(text[last_idx:start]))

            span_text = html.escape(text[start:end])
            span_type = span.get("type", "sensational")
            category = span.get("category", "Flagged Phrase")
            desc = html.escape(span.get("description", ""))

            color_class = "highlight-sensational"
            if span_type == "clickbait":
                color_class = "highlight-clickbait"
            elif span_type == "caps" or span_type == "punctuation":
                color_class = "highlight-stylistic"
            elif span_type == "xai_term":
                color_class = "highlight-xai"

            tagged = (
                f'<mark class="truthlens-highlight {color_class}" '
                f'data-category="{category}" '
                f'title="{desc}">{span_text}</mark>'
            )
            result.append(tagged)
            last_idx = end

        # Append remaining text
        if last_idx < len(text):
            result.append(html.escape(text[last_idx:]))

        return "".join(result)

highlighter = TextHighlighter()
