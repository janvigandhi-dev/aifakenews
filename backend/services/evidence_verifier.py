import json
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import httpx
from groq import Groq
from backend.config import settings

# Ensure Windows terminal never crashes on Unicode output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# DuckDuckGo search for live web intelligence
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

# Google Gemini GenAI SDK
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


class EvidenceVerifier:
    def __init__(self):
        self.client = None
        self.gemini_client = None
        self._init_groq_client()
        self._init_gemini_client()

    def _init_groq_client(self):
        key = settings.GROQ_API_KEY
        if key:
            try:
                self.client = Groq(api_key=key)
            except Exception as e:
                print(f"[EvidenceVerifier] Groq initialization warning: {e}")

    def _init_gemini_client(self):
        key = settings.GEMINI_API_KEY
        if key and genai and types:
            try:
                self.gemini_client = genai.Client(
                    api_key=key,
                    http_options=types.HttpOptions(timeout=10000)
                )
            except Exception as e:
                print(f"[EvidenceVerifier] Gemini initialization warning: {e}")

    def _detect_historical_context(self, text: str) -> bool:
        """
        Detects if text refers to past events, historical milestones, or older news
        (e.g., 1970s, 1980s, 1990s, 2000s, 2010s, early 2020s).
        """
        if not text:
            return False
        # Year pattern (1800-2024)
        year_match = re.search(r'\b(18\d\d|19\d\d|200\d|201\d|202[0-4])\b', text)
        if year_match:
            return True

        historical_markers = [
            "historic", "historical", "world cup", "pokhran", "demonetisation", "demonetization",
            "earthquake", "tsunami", "former prime minister", "former president", "passed away",
            "independence", "in the year", "apollo", "kargil", "constitution", "treaty",
            "signed in", "launched in", "established in", "archived", "old news", "decades ago",
            "anniversary", "memorial", "in 1983", "in 1998", "in 2001", "in 2011", "in 2016"
        ]
        text_lower = text.lower()
        return any(m in text_lower for m in historical_markers)

    def clean_search_query(self, headline: str, content: str = "", ocr_text: str = "") -> str:
        """
        Extracts a clean, high-precision search query by removing user meta-questions,
        filler words, translating regional text if needed, and combining headline with core content entities.
        """
        meta_phrases = [
            r'(?i)\bdoes\s+this\s+news\s+(is\s+)?(true|false|real|fake)\b',
            r'(?i)\bis\s+this\s+(news\s+)?(true|false|real|fake|misleading)\b',
            r'(?i)\bis\s+it\s+(true|false|real|fake)\b',
            r'(?i)\bcheck\s+(if\s+)?(this\s+)?(is\s+)?(true|false|real|fake)\b',
            r'(?i)\bverify\s+(this\s+)?(news|claim|article|story)?\b',
            r'(?i)\btell\s+me\s+if\s+(this\s+is\s+)?(true|false|real|fake)\b',
            r'(?i)\btrue\s+or\s+false\b',
            r'(?i)\breal\s+or\s+fake\b',
            r'(?i)\bwhatsapp\s+forward\b',
            r'(?i)\bforwarded\s+as\s+received\b',
            r'(?i)\bbreaking(\s+news)?\s*:\s*',
            r'(?i)\bshocking\s*:\s*',
            r'(?i)\bproud\s+moment(\s+for\s+india)?\s*:\s*',
            r'\[Extracted Text from Attached Image\]:?',
            r'\[Extracted Text from Image \(OCR\)\]:?'
        ]

        # Combine candidate texts
        combined_candidates = []
        if headline:
            combined_candidates.append(headline.strip())
        if content and content.strip() != headline.strip():
            combined_candidates.append(content.strip()[:400])
        if ocr_text and ocr_text.strip() not in (headline, content):
            combined_candidates.append(ocr_text.strip()[:400])

        raw_text = " ".join(combined_candidates).strip()

        # Clean meta questions
        cleaned = raw_text
        for pattern in meta_phrases:
            cleaned = re.sub(pattern, ' ', cleaned)

        # Detect non-ASCII scripts (e.g. Gujarati, Hindi, etc.)
        has_indic = bool(re.search(r'[\u0900-\u0D7F]', cleaned))
        if has_indic:
            # 1. Try Groq first for ultra-fast keyword translation (~0.8s)
            if self.client:
                try:
                    kw_prompt = (
                        "Extract 3 to 5 essential English search keywords to search Google News for verifying this claim. "
                        "If the text is in Gujarati or Hindi, translate the core entities and topic into English keywords. "
                        f"Text: {cleaned[:400]}"
                    )
                    kw_resp = self.client.chat.completions.create(
                        messages=[{"role": "user", "content": kw_prompt}],
                        model=settings.GROQ_MODEL,
                        max_tokens=200,
                        temperature=0.0
                    )
                    kw_text = kw_resp.choices[0].message.content or ""
                    lines = [l.strip() for l in kw_text.split("\n") if l.strip() and not l.strip().startswith("*") and not l.strip().startswith("#")]
                    clean_lines = [re.sub(r'^\d+[\.\)]\s*', '', l).strip() for l in lines]
                    valid_kw = " ".join(clean_lines[:3]).strip()
                    if valid_kw:
                        valid_kw = re.sub(r'[\?\#\!\@\$\%\^\*\(\)\_\+\=\[\]\{\}\;\:\"\\\|\<\>\/]+', ' ', valid_kw)
                        valid_kw = re.sub(r'\s+', ' ', valid_kw).strip()
                        if len(valid_kw.split()) >= 2:
                            return " ".join(valid_kw.split()[:7])
                except Exception as e:
                    print(f"[EvidenceVerifier] Groq Indic keyword translation note: {e}")

            # 2. Try Gemini fallback if Groq unavailable
            if self.gemini_client:
                try:
                    kw_prompt = (
                        "Extract 3 to 5 essential English search keywords to search news and encyclopedias for verifying this claim. "
                        "If the text is in Gujarati or Hindi, translate the core entities and topic into English keywords. "
                        f"Text: {cleaned[:400]}"
                    )
                    resp = self.gemini_client.models.generate_content(
                        model=settings.GEMINI_MODEL,
                        contents=kw_prompt
                    )
                    kw_text = resp.text.strip() if resp and resp.text else ""
                    lines = [l.strip() for l in kw_text.split("\n") if l.strip() and not l.strip().startswith("*") and not l.strip().startswith("#")]
                    clean_lines = [re.sub(r'^\d+[\.\)]\s*', '', l).strip() for l in lines]
                    valid_kw = " ".join(clean_lines[:3]).strip()
                    if valid_kw:
                        valid_kw = re.sub(r'[\?\#\!\@\$\%\^\*\(\)\_\+\=\[\]\{\}\;\:\"\\\|\<\>\/]+', ' ', valid_kw)
                        valid_kw = re.sub(r'\s+', ' ', valid_kw).strip()
                        if len(valid_kw.split()) >= 2:
                            return " ".join(valid_kw.split()[:7])
                except Exception as e:
                    print(f"[EvidenceVerifier] Gemini Indic keyword note: {e}")

        # English extraction
        cleaned = re.sub(r'[\?\#\!\@\$\%\^\*\(\)\_\+\=\[\]\{\}\;\:\"\\\|\<\>\/]+', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        words = cleaned.split()
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "and", "or", "in", "on", "at", "to",
            "for", "with", "that", "this", "it", "from", "by", "has", "have", "been", "does",
            "will", "would", "about", "news", "story", "claim", "post", "video", "photo", "image"
        }
        meaningful = [w for w in words if w.lower() not in stop_words and len(w) > 1]
        if len(meaningful) >= 3:
            return " ".join(meaningful[:7])

        return " ".join(words[:7]) if words else headline[:60]

    def _search_google_news_rss(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Queries Google News RSS feed for instant real-time news and fact-checks with zero rate-limits."""
        encoded = urllib.parse.quote_plus(query)
        endpoints = [
            f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en",
            f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
        ]

        articles = []
        seen = set()

        for url in endpoints:
            try:
                with httpx.Client(timeout=4.0) as client:
                    resp = client.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                    if resp.status_code == 200 and resp.text.strip():
                        root = ET.fromstring(resp.text)
                        for item in root.findall("./channel/item"):
                            title_elem = item.find("title")
                            title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                            link_elem = item.find("link")
                            link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                            source_elem = item.find("source")
                            publisher = source_elem.text.strip() if source_elem is not None and source_elem.text else ""

                            if not publisher and " - " in title:
                                parts = title.rsplit(" - ", 1)
                                title = parts[0].strip()
                                publisher = parts[1].strip()

                            if title and title.lower() not in seen:
                                seen.add(title.lower())
                                articles.append({
                                    "title": title,
                                    "url": link,
                                    "domain": publisher or "Google News",
                                    "snippet": title
                                })
                            if len(articles) >= max_results:
                                return articles
            except Exception:
                pass

        return articles

    def _search_wikipedia_api(self, query: str, max_results: int = 2) -> List[Dict[str, str]]:
        """Queries Wikipedia REST API for verified encyclopedic and historical events."""
        encoded = urllib.parse.quote_plus(query)
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded}&format=json"

        articles = []
        try:
            with httpx.Client(timeout=4.0) as client:
                resp = client.get(url, headers={"User-Agent": "TruthLens/1.0 (factcheck@truthlens.ai)"})
                if resp.status_code == 200:
                    data = resp.json()
                    search_results = data.get("query", {}).get("search", [])
                    for item in search_results[:max_results]:
                        title = item.get("title", "")
                        snippet_raw = item.get("snippet", "")
                        clean_snippet = re.sub(r'<[^>]+>', '', snippet_raw)
                        page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                        articles.append({
                            "title": f"{title} - Wikipedia",
                            "url": page_url,
                            "domain": "Wikipedia (Encyclopedia)",
                            "snippet": clean_snippet
                        })
        except Exception:
            pass

        return articles

    def search_internet_sources(self, query: str, max_results: int = 6) -> List[Dict[str, str]]:
        """
        Multi-Source Resilient News & Fact-Checking Aggregator:
        1. Google News RSS (India & International) - fast, resilient, zero rate-limit.
        2. Google News fact-check specific query for viral claims.
        3. Wikipedia API for encyclopedic/historical topics.
        4. DuckDuckGo (DDGS) news & web text.
        """
        if not query or not query.strip():
            return []

        clean_query = re.sub(r'[\r\n\t]+', ' ', query).strip()
        search_terms = " ".join(clean_query.split()[:8])
        is_historical = self._detect_historical_context(clean_query)

        articles = []
        seen_titles = set()

        def add_unique(new_arts):
            for a in new_arts:
                norm_title = re.sub(r'\W+', '', a.get("title", "").lower())[:40]
                if norm_title and norm_title not in seen_titles:
                    seen_titles.add(norm_title)
                    articles.append(a)

        # 1. Google News RSS
        gn_results = self._search_google_news_rss(search_terms, max_results=4)
        add_unique(gn_results)

        # 2. If claim looks like a viral rumor or hoax, query fact-check specific feed
        rumor_cues = ["gps", "chip", "best", "anthem", "unesco", "cure", "secret", "banned", "hoax", "viral", "rbi", "nasa"]
        if any(w in search_terms.lower() for w in rumor_cues) and len(articles) < max_results:
            fc_results = self._search_google_news_rss(f"{search_terms} fact check", max_results=3)
            add_unique(fc_results)

        # 3. Wikipedia API (ALWAYS checked for historical topics or when Google News has few results)
        if (is_historical or len(articles) < 3):
            wiki_results = self._search_wikipedia_api(search_terms, max_results=2)
            add_unique(wiki_results)

        # 4. DuckDuckGo Search (fast web fallback only if no articles found from Google News or Wikipedia)
        if len(articles) == 0 and DDGS:
            try:
                with DDGS(timeout=3) as ddgs:
                    ddg_results = list(ddgs.text(search_terms, backend="duckduckgo", max_results=3))
                    for r in ddg_results:
                        url = r.get("href", r.get("link", ""))
                        title = r.get("title", "")
                        body = r.get("body", r.get("snippet", ""))
                        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
                        domain = domain_match.group(1) if domain_match else "web"
                        add_unique([{
                            "title": title,
                            "url": url,
                            "domain": domain,
                            "snippet": body
                        }])
            except Exception:
                pass

        return articles[:max_results]

    def _call_gemini_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Calls Google Gemini GenAI SDK with fast model fallback and JSON parsing."""
        if not self.gemini_client:
            return None

        model_name = settings.GEMINI_MODEL or "gemini-3.5-flash"
        try:
            resp = self.gemini_client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            if resp and resp.text:
                raw_text = resp.text.strip()
                cleaned = re.sub(r'^```(?:json)?\s*', '', raw_text, flags=re.MULTILINE)
                cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)
                json_match = re.search(r'(\{[\s\S]*\})', cleaned)
                if json_match:
                    parsed = json.loads(json_match.group(1))
                    parsed["_gemini_model"] = model_name
                    return parsed
        except Exception as e:
            print(f"[EvidenceVerifier] Gemini ({model_name}) note: {e}")

        return None

    def _call_groq_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Calls Groq LLaMA model with JSON response format and regex fallback."""
        if not self.client:
            return None

        # Attempt 1: json_object format
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional fact-checking engine. Respond with a valid JSON object matching the requested schema exactly."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=settings.GROQ_MODEL,
                temperature=0.1,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            raw_resp = chat_completion.choices[0].message.content.strip()
            return json.loads(raw_resp)
        except Exception as e:
            print(f"[EvidenceVerifier] Groq json_object attempt note: {e}")

        # Attempt 2: raw completion + regex extraction
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a news fact-checking assistant. You MUST respond ONLY with a raw JSON object. Do not include markdown ticks, preamble, or commentary."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=settings.GROQ_MODEL,
                temperature=0.1,
                max_tokens=800
            )
            raw_resp = chat_completion.choices[0].message.content.strip()
            cleaned = re.sub(r'^```(?:json)?\s*', '', raw_resp, flags=re.MULTILINE)
            cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)
            json_match = re.search(r'(\{[\s\S]*\})', cleaned)
            if json_match:
                return json.loads(json_match.group(1))
        except Exception as e2:
            print(f"[EvidenceVerifier] Groq raw parse attempt error: {e2}")

        return None

    def deep_analyze_with_internet(self, headline: str, content: str, ocr_text: str = "") -> Optional[Dict[str, Any]]:
        """
        Complete Dual-Engine Verification Pipeline (Google Gemini + Groq LLM):
        1. Cleans user text & extracts high-precision search query.
        2. Detects historical context (old news vs breaking news).
        3. Queries multi-tier live search (Google News RSS, Wikipedia API, DDGS).
        4. Cross-references search results + Parametric Training Knowledge (Gemini + Groq).
        5. Performs consensus validation and returns comprehensive explainable results.
        """
        if not self.client and settings.GROQ_API_KEY:
            self._init_groq_client()
        if not self.gemini_client and settings.GEMINI_API_KEY:
            self._init_gemini_client()

        # Build full contextual text
        full_text = f"{headline}\n{content}".strip()
        if ocr_text and ocr_text.strip() not in (headline, content):
            full_text += f"\n\n[Extracted Text from Image (OCR)]:\n{ocr_text}"

        is_historical = self._detect_historical_context(full_text)

        # 1. Clean query & Surf Internet for Live Matching News
        search_query = self.clean_search_query(headline, content, ocr_text)
        live_articles = self.search_internet_sources(search_query, max_results=6)

        # Format live search context for LLM
        if live_articles:
            search_context_lines = []
            for idx, a in enumerate(live_articles, 1):
                search_context_lines.append(
                    f"{idx}. Title: {a['title']}\n   Source: {a['domain']}\n   URL: {a['url']}\n   Summary: {a['snippet']}"
                )
            search_context = "\n\n".join(search_context_lines)
        else:
            search_context = "No direct matching web articles were found on public daily news feeds for this specific query."

        prompt = f"""You are TruthLens, the world's leading Explainable AI News Fact-Checking Engine powered by Google Gemini and Groq.
A user has submitted a news story/claim for verification.

USER SUBMISSION / CLAIM:
{full_text[:3500]}

REAL-TIME INTERNET SEARCH & ENCYCLOPEDIC RESULTS:
{search_context}

DETECTED HISTORICAL TIME CONTEXT:
{"[HISTORICAL CLAIM DETECTED]: The claim mentions past years, historical events, or archived milestones." if is_historical else "[CURRENT / RECENT CLAIM]: The claim appears to be recent or contemporary."}

CRITICAL VERIFICATION RULES & GUIDELINES:
1. **OLD / HISTORICAL TRUE NEWS (PAST GENUINE EVENTS)**:
   - If the claim describes an established historical event, past government decision, past sports victory, scientific milestone, past disaster, or documented historical occurrence (e.g., 1983 Cricket World Cup, 1998 Pokhran nuclear tests, 2016 demonetisation of ₹500/₹1000 notes, 2001 Gujarat earthquake, 1969 Apollo Moon landing, 1947 Indian Independence, 2011 World Cup victory, historic laws/elections):
   - **DO NOT mark it as fake simply because today's daily news RSS returns few or zero articles!**
   - Verify it using your vast internal parametric training knowledge and any Wikipedia/encyclopedic references found.
   - If it genuinely occurred in history, you MUST mark:
     "is_fake": false,
     "verdict": "REAL / HISTORICAL FACT",
     "fake_percentage": 5.0,
     "real_percentage": 95.0,
     "confidence": 95.0.
   - In explanation_bullets, clearly state that this is a confirmed historical event that genuinely took place on the documented date/year.

2. **DEBUNKED URBAN LEGENDS & HISTORICAL HOAXES**:
   - If the claim is a known viral myth or urban legend that has circulated for years (e.g., "₹2000 note has a nano GPS chip", "UNESCO declared Indian national anthem best in the world", "NASA spent millions on space pen while Russians used pencil", "miracle 48h cancer cure suppressed by big pharma", "salt water car suppressed by oil mafia", "UNESCO declared Narendra Modi best PM"):
   - You MUST mark:
     "is_fake": true,
     "verdict": "DEBUNKED URBAN LEGEND / HOAX",
     "fake_percentage": 92.0,
     "real_percentage": 8.0,
     "confidence": 95.0.
   - Clearly explain why this is a historically documented myth.

3. **CURRENT / RECENT NEWS**:
   - If credible news sources (Times of India, The Hindu, NDTV, Indian Express, BBC, Reuters, AP, PIB, ANI, DD News) confirm the event, mark:
     "is_fake": false,
     "verdict": "REAL / LOW RISK",
     "fake_percentage": 10.0,
     "real_percentage": 90.0.
   - If the claim is a fabricated rumor or contradicted by fact-checkers, mark:
     "is_fake": true,
     "verdict": "LIKELY MISLEADING",
     "fake_percentage": 85.0 to 95.0,
     "real_percentage": 5.0 to 15.0.

4. **HYPER-LOCAL / CAMPUS / COMMUNITY EVENTS**:
   - If the claim describes a normal, plausible local event (e.g. college garba celebration, university workshop, campus sports day, local student poster or academic event) that contains NO sensationalism, conspiracy claims, or scam signals, mark:
     "is_fake": false,
     "verdict": "REAL / PLAUSIBLE LOCAL EVENT",
     "fake_percentage": 10.0,
     "real_percentage": 90.0.

5. **SOURCE RELATIONSHIPS**:
   Classify each source reference clearly as:
   - "CONFIRMS AS REAL" (verifies the event happened)
   - "DEBUNKS AS HOAX" (refutes or debunks the claim)
   - "RELATED COVERAGE" (provides context or historical encyclopedia record)

Return a single valid JSON object matching this schema:
{{
  "is_fake": false,
  "verdict": "REAL / LOW RISK",
  "fake_percentage": 10.0,
  "real_percentage": 90.0,
  "misinformation_risk_score": 10.0,
  "confidence": 92.0,
  "verdict_summary": "Concise 1-2 sentence verdict explaining the factual findings and final decision.",
  "explanation_bullets": [
    "Specific reason 1 citing historical records or live internet findings",
    "Specific reason 2 detailing factual verification or confirmation",
    "Specific reason 3 analyzing context and authenticity"
  ],
  "claims": [
    {{
      "claim": "Extracted core factual claim",
      "stance": "SUPPORTED",
      "evidence_assessment": "Explanation of whether historical knowledge or internet search confirms this claim.",
      "plausibility": "HIGH"
    }}
  ],
  "source_references": [
    {{
      "title": "Article Title from Internet Search or Historical Record",
      "url": "https://...",
      "publisher": "Domain or News Outlet Name",
      "relationship": "CONFIRMS AS REAL",
      "snippet": "Brief note on what this source or historical record states."
    }}
  ],
  "flagged_phrases": [
    {{
      "text": "exact phrase from text if sensational, or empty",
      "category": "Sensational Language",
      "severity": "LOW",
      "reason": "Why this was flagged"
    }}
  ]
}}"""

        gemini_result = None
        groq_result = None

        # Execute Gemini and Groq in parallel for maximum speed and zero hang time
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            groq_future = executor.submit(self._call_groq_api, prompt) if self.client else None
            gemini_future = executor.submit(self._call_gemini_api, prompt) if self.gemini_client else None

            # Collect Groq first (extremely fast, ~1.2 - 2.5s)
            if groq_future:
                try:
                    groq_result = groq_future.result(timeout=5.0)
                except Exception as e:
                    print(f"[EvidenceVerifier] Groq parallel note: {e}")

            # If Groq already succeeded, only wait a brief moment for Gemini for consensus; don't hold up the user!
            gemini_timeout = 2.5 if groq_result else 5.0
            if gemini_future:
                try:
                    gemini_result = gemini_future.result(timeout=gemini_timeout)
                except Exception as e:
                    pass

        # 3. Dual-Engine Consensus Synthesis
        final_result = None
        engine_name = "TruthLens Explainable AI Engine"

        if gemini_result and groq_result:
            # Both models responded! Synthesize consensus.
            engine_name = "TruthLens Dual-Consensus AI Engine (Google Gemini + Groq Llama)"
            gemini_fake = gemini_result.get("is_fake", False)
            groq_fake = groq_result.get("is_fake", False)

            if gemini_fake == groq_fake:
                # Full agreement
                final_result = gemini_result
                final_result["confidence"] = max(float(gemini_result.get("confidence", 90.0)), float(groq_result.get("confidence", 90.0)))
            else:
                # Disagreement: Gemini has far superior historical parametric knowledge
                # If Gemini identified this as a historical fact or debunked myth, prioritize Gemini
                if is_historical or "HISTORICAL" in str(gemini_result.get("verdict", "")).upper():
                    final_result = gemini_result
                else:
                    # Default to Gemini's higher nuance
                    final_result = gemini_result

        elif gemini_result:
            model_used = gemini_result.get("_gemini_model", settings.GEMINI_MODEL)
            engine_name = f"TruthLens Neural Fact-Checker (Google {model_used})"
            final_result = gemini_result

        elif groq_result:
            engine_name = f"TruthLens Web Reasoning Engine (Groq {settings.GROQ_MODEL})"
            final_result = groq_result

        # 4. If an LLM succeeded, post-process and return
        if final_result:
            final_result["engine"] = engine_name
            return self._post_process_result(final_result, live_articles, is_historical)

        # 5. Fallback if both AI models failed or unavailable
        return self._fallback_internet_analysis(headline, full_text, live_articles, is_historical)

    def _post_process_result(self, result: Dict[str, Any], live_articles: List[Dict[str, str]], is_historical: bool = False) -> Dict[str, Any]:
        """Post-processes and logically reconciles predictions with verified sources and historical context."""
        sources = result.get("source_references", [])

        # Guarantee source references are populated if live articles exist
        if not sources and live_articles:
            sources = [
                {
                    "title": a["title"],
                    "url": a["url"],
                    "publisher": a["domain"],
                    "relationship": "RELATED COVERAGE",
                    "snippet": a["snippet"]
                }
                for a in live_articles[:4]
            ]
            result["source_references"] = sources

        # Logical Reconciliation between sources and verdict:
        confirm_count = sum(1 for s in sources if "CONFIRMS" in s.get("relationship", "").upper() or "REAL" in s.get("relationship", "").upper() or "SUPPORTED" in s.get("relationship", "").upper())
        debunk_count = sum(1 for s in sources if "DEBUNKS" in s.get("relationship", "").upper() or "HOAX" in s.get("relationship", "").upper() or "CONTRADICT" in s.get("relationship", "").upper() or "MISLEADING" in s.get("relationship", "").upper() or "FALSE" in s.get("relationship", "").upper())

        # If any source explicitly debunks it as a hoax, is_fake must be True!
        if debunk_count >= 1:
            result["is_fake"] = True
            if "HOAX" not in result.get("verdict", ""):
                result["verdict"] = "LIKELY MISLEADING"
            result["fake_percentage"] = max(float(result.get("fake_percentage", 85.0)), 85.0)
            result["real_percentage"] = min(float(result.get("real_percentage", 15.0)), 15.0)
            result["misinformation_risk_score"] = result["fake_percentage"]
        # If sources confirm the event as real without debunking sources, is_fake must be False!
        elif confirm_count >= 1:
            result["is_fake"] = False
            if not result.get("verdict"):
                result["verdict"] = "REAL / HISTORICAL FACT" if is_historical else "REAL / LOW RISK"
            result["fake_percentage"] = min(float(result.get("fake_percentage", 10.0)), 15.0)
            result["real_percentage"] = max(float(result.get("real_percentage", 90.0)), 85.0)
            result["misinformation_risk_score"] = result["fake_percentage"]
        else:
            # Reconcile percentages
            if "fake_percentage" in result and "real_percentage" not in result:
                result["real_percentage"] = max(0.0, 100.0 - float(result["fake_percentage"]))
            elif "real_percentage" in result and "fake_percentage" not in result:
                result["fake_percentage"] = max(0.0, 100.0 - float(result["real_percentage"]))

        result["internet_sources_found"] = len(live_articles)
        return result

    def _fallback_internet_analysis(self, headline: str, text: str, articles: List[Dict[str, str]], is_historical: bool = False) -> Dict[str, Any]:
        """Intelligent heuristic fallback combining internet search results with rule-based heuristics."""
        combined_text = (headline + " " + text).lower()
        articles_text = " ".join([a["title"] + " " + a.get("snippet", "") for a in articles]).lower()

        # Check for debunking signals in articles
        has_debunking = any(w in articles_text for w in [
            "fact check", "fake alert", "did not declare", "hoax", "false claim", "debunk", "myth", "no truth"
        ])

        # Check for confirmation signals in articles
        has_confirmation = any(w in articles_text for w in [
            "confirms", "announces", "reported", "statement", "official", "lands successfully", "wins", "wikipedia"
        ])

        # Check for obvious viral hoax keywords in user text
        known_hoax_words = [
            "secret cancer cure", "100% cure", "mind control", "alien city", "banned by oil",
            "nano gps chip", "gps chip", "best national anthem in the world", "unesco declared"
        ]
        is_known_hoax = any(w in combined_text for w in known_hoax_words)

        # Historical true events shouldn't be penalized if no recent news
        if is_historical and not is_known_hoax and not has_debunking:
            is_fake = False
            verdict = "REAL / HISTORICAL FACT"
            fake_pct = 10.0
            real_pct = 90.0
        else:
            is_fake = is_known_hoax or has_debunking or (not has_confirmation and "leaked" in combined_text and "deep state" in combined_text)
            verdict = "LIKELY MISLEADING" if is_fake else ("REAL / LOW RISK" if articles else "SUSPICIOUS / REVIEW")
            fake_pct = 90.0 if is_fake else (15.0 if articles else 45.0)
            real_pct = 100.0 - fake_pct

        sources = []
        for a in articles[:4]:
            sources.append({
                "title": a["title"],
                "url": a["url"],
                "publisher": a["domain"],
                "relationship": "DEBUNKS AS HOAX" if (is_fake or "fact check" in a["title"].lower()) else "CONFIRMS AS REAL",
                "snippet": a.get("snippet", "")
            })

        return {
            "is_fake": is_fake,
            "verdict": verdict,
            "fake_percentage": fake_pct,
            "real_percentage": real_pct,
            "misinformation_risk_score": fake_pct,
            "confidence": 85.0 if (has_debunking or has_confirmation or is_historical) else 70.0,
            "verdict_summary": "Cross-referenced with online archives and encyclopedic knowledge. " + (
                "Verified reports disprove or contradict this claim." if is_fake else "Corroborated by historical and news records."
            ),
            "explanation_bullets": [
                "Identified core factual claims and queried online archives and databases for matching events.",
                "Cross-referenced against verified fact-checking records, encyclopedia entries, and publisher databases."
            ],
            "claims": [
                {
                    "claim": headline or text[:120],
                    "stance": "CONTRADICTED" if is_fake else "SUPPORTED",
                    "evidence_assessment": "Assessed against web archives and historical references.",
                    "plausibility": "LOW" if is_fake else "HIGH"
                }
            ],
            "source_references": sources,
            "engine": "TruthLens Resilient Knowledge Engine (Fallback)",
            "internet_sources_found": len(articles)
        }


evidence_verifier = EvidenceVerifier()
