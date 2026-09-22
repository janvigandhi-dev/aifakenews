"""
Instagram Post & Image Analysis Service for TruthLens.

Handles:
1. Instagram post link analysis — scrape metadata, send to LLM, cross-reference via web search
2. Image upload analysis — Groq Vision for OCR + description, cross-reference via web search
"""

import re
import json
import base64
import httpx
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from groq import Groq
from backend.config import settings

# DuckDuckGo search for finding similar news
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None


class InstagramAnalyzer:
    def __init__(self):
        self.client = None
        if settings.GROQ_API_KEY:
            try:
                self.client = Groq(api_key=settings.GROQ_API_KEY)
            except Exception as e:
                print(f"[InstagramAnalyzer] Groq initialization warning: {e}")

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    # ──────────────────────────────────────────────
    # Instagram Link Analysis
    # ──────────────────────────────────────────────

    def _is_instagram_url(self, url: str) -> bool:
        """Check if URL is from Instagram."""
        return bool(re.search(r'(instagram\.com|instagr\.am)', url, re.IGNORECASE))

    async def _scrape_instagram_metadata(self, url: str) -> Dict[str, str]:
        """
        Attempt to scrape whatever metadata is available from an Instagram page.
        Instagram heavily blocks scraping, so we grab og: meta tags from the initial HTML.
        """
        result = {"title": "", "description": "", "image_url": "", "raw_text": ""}

        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, headers=self.headers) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    return result

                html = response.text
                soup = BeautifulSoup(html, "html.parser")

                # Extract Open Graph metadata
                og_title = soup.find("meta", property="og:title")
                if og_title and og_title.get("content"):
                    result["title"] = og_title["content"].strip()

                og_desc = soup.find("meta", property="og:description")
                if og_desc and og_desc.get("content"):
                    result["description"] = og_desc["content"].strip()

                og_image = soup.find("meta", property="og:image")
                if og_image and og_image.get("content"):
                    result["image_url"] = og_image["content"].strip()

                # Also try twitter card metadata
                tw_desc = soup.find("meta", attrs={"name": "twitter:description"})
                if tw_desc and tw_desc.get("content") and not result["description"]:
                    result["description"] = tw_desc["content"].strip()

                # Try to extract any visible text from the page
                for tag in soup(["script", "style", "noscript", "svg"]):
                    tag.decompose()
                visible_text = soup.get_text(separator=" ", strip=True)
                if visible_text and len(visible_text) > 50:
                    result["raw_text"] = visible_text[:2000]

        except Exception as e:
            print(f"[InstagramAnalyzer] Scrape error: {e}")

        return result

    def _search_similar_news(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search for similar news articles using DuckDuckGo."""
        if not DDGS:
            return []

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", r.get("link", "")),
                        "snippet": r.get("body", r.get("snippet", ""))
                    }
                    for r in results
                ]
        except Exception as e:
            print(f"[InstagramAnalyzer] DuckDuckGo search error: {e}")
            return []

    def _llm_extract_instagram_claim(self, url: str, metadata: Dict[str, str]) -> Dict[str, str]:
        """Use Groq LLM to interpret the Instagram post content and extract the news claim."""
        if not self.client:
            return {"headline": metadata.get("title", ""), "content": metadata.get("description", ""), "claim": ""}

        scraped_context = ""
        if metadata.get("title"):
            scraped_context += f"Page Title: {metadata['title']}\n"
        if metadata.get("description"):
            scraped_context += f"Caption/Description: {metadata['description']}\n"
        if metadata.get("raw_text"):
            scraped_context += f"Page Text Snippet: {metadata['raw_text'][:1000]}\n"

        prompt = f"""You are TruthLens, a news verification AI. A user has submitted an Instagram post URL for fact-checking.

Instagram URL: {url}
{f"Scraped Metadata:{chr(10)}{scraped_context}" if scraped_context.strip() else "No metadata could be scraped from this Instagram post (page is blocked/private)."}

Your task:
1. Based on the available metadata and your knowledge, identify what NEWS CLAIM or INFORMATION this Instagram post is sharing.
2. Extract a clear headline summarizing the claim.
3. Reconstruct the key content/body of the news claim being shared.
4. If no metadata is available, use the URL structure (reel ID, username) to provide whatever context you can.

Return a valid JSON object with this exact schema:
{{
  "headline": "Clear headline summarizing the news claim in the post",
  "content": "Detailed description of the claim or news being shared in 2-4 sentences",
  "claim_type": "POLITICAL" | "HEALTH" | "SCIENCE" | "SOCIAL" | "FINANCIAL" | "GENERAL",
  "context_quality": "HIGH" | "MEDIUM" | "LOW",
  "context_note": "Brief note about how much context was available"
}}
Respond with JSON only."""

        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a news verification assistant. Respond with raw JSON only."},
                    {"role": "user", "content": prompt}
                ],
                model=settings.GROQ_MODEL,
                temperature=0.1,
                max_tokens=800
            )

            raw = completion.choices[0].message.content.strip()
            cleaned = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
            cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)

            json_match = re.search(r'(\{[\s\S]*\})', cleaned)
            if json_match:
                return json.loads(json_match.group(1))
        except Exception as e:
            print(f"[InstagramAnalyzer] LLM claim extraction error: {e}")

        return {
            "headline": metadata.get("title", "Instagram Post Analysis"),
            "content": metadata.get("description", "Could not extract detailed content from this Instagram post."),
            "claim_type": "GENERAL",
            "context_quality": "LOW",
            "context_note": "Limited metadata available from Instagram."
        }

    def _llm_crosscheck_verdict(self, claim_headline: str, claim_content: str,
                                 search_results: List[Dict[str, str]], source_type: str = "Instagram") -> Dict[str, Any]:
        """Use Groq LLM to cross-reference the claim against found news articles and produce a verdict."""
        if not self.client:
            return self._fallback_social_verdict(claim_headline, search_results)

        search_context = ""
        if search_results:
            for i, article in enumerate(search_results[:5], 1):
                search_context += f"\n{i}. [{article.get('title', 'Untitled')}]\n   URL: {article.get('url', 'N/A')}\n   Snippet: {article.get('snippet', 'No snippet')}\n"
        else:
            search_context = "\nNo similar news articles were found via web search."

        prompt = f"""You are TruthLens, an AI fact-checking system. Analyze this {source_type} claim against the similar news found online.

CLAIM FROM {source_type.upper()}:
Headline: {claim_headline}
Content: {claim_content[:2000]}

SIMILAR NEWS FOUND ONLINE:
{search_context}

Based on the comparison between the original claim and the news articles found:
1. Assess whether the claim is SUPPORTED, CONTRADICTED, or UNVERIFIED by existing credible reports.
2. Check for exaggeration, misquotation, or out-of-context framing.
3. Note any discrepancies between the {source_type} claim and mainstream reporting.

Return a valid JSON object:
{{
  "social_verdict": "LIKELY TRUE" | "LIKELY FALSE" | "MISLEADING / OUT OF CONTEXT" | "UNVERIFIED / INSUFFICIENT DATA",
  "confidence": 85,
  "reasoning": "2-3 sentence explanation of your assessment.",
  "key_findings": [
    "Finding 1: what the search results confirm or deny",
    "Finding 2: notable discrepancy or confirmation"
  ],
  "matching_sources": [
    {{
      "title": "Title of matching/relevant article",
      "url": "URL",
      "relationship": "CONFIRMS" | "CONTRADICTS" | "PARTIALLY CONFIRMS" | "UNRELATED"
    }}
  ],
  "recommendation": "What the user should do next to verify this claim"
}}
Respond with JSON only."""

        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a professional fact-checking engine. Respond with raw JSON only."},
                    {"role": "user", "content": prompt}
                ],
                model=settings.GROQ_MODEL,
                temperature=0.1,
                max_tokens=1200
            )

            raw = completion.choices[0].message.content.strip()
            cleaned = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
            cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)

            json_match = re.search(r'(\{[\s\S]*\})', cleaned)
            if json_match:
                result = json.loads(json_match.group(1))
                result["engine"] = f"TruthLens Social Media Analyzer (Groq {settings.GROQ_MODEL})"
                result["search_results_count"] = len(search_results)
                return result
        except Exception as e:
            print(f"[InstagramAnalyzer] LLM cross-check error: {e}")

        return self._fallback_social_verdict(claim_headline, search_results)

    def _fallback_social_verdict(self, headline: str, search_results: List[Dict[str, str]]) -> Dict[str, Any]:
        """Fallback verdict when LLM is unavailable."""
        return {
            "social_verdict": "UNVERIFIED / INSUFFICIENT DATA",
            "confidence": 50,
            "reasoning": "Unable to perform AI-powered cross-referencing. The claim should be manually verified against trusted news sources.",
            "key_findings": [
                f"Found {len(search_results)} potentially related articles via web search." if search_results else "No similar news articles found online."
            ],
            "matching_sources": [
                {"title": r.get("title", ""), "url": r.get("url", ""), "relationship": "REQUIRES REVIEW"}
                for r in search_results[:3]
            ],
            "recommendation": "Verify this claim with established news agencies like Reuters, AP, or BBC.",
            "engine": "TruthLens Heuristic Social Analyzer (Fallback)",
            "search_results_count": len(search_results)
        }

    async def analyze_instagram_link(self, url: str) -> Dict[str, Any]:
        """
        Full Instagram post analysis pipeline:
        1. Scrape metadata
        2. LLM claim extraction
        3. Web search for similar news
        4. LLM cross-reference verdict
        """
        if not self._is_instagram_url(url):
            return {
                "success": False,
                "error": "This does not appear to be an Instagram URL. Please paste a valid Instagram post or reel link."
            }

        # Step 1: Scrape whatever metadata Instagram allows
        metadata = await self._scrape_instagram_metadata(url)

        # Step 2: LLM extracts the news claim
        claim_data = self._llm_extract_instagram_claim(url, metadata)
        headline = claim_data.get("headline", "Instagram Post")
        content = claim_data.get("content", "")

        # Step 3: Search for similar news
        search_query = headline if headline else content[:200]
        search_results = self._search_similar_news(search_query)

        # Step 4: LLM cross-references and produces verdict
        social_verdict = self._llm_crosscheck_verdict(headline, content, search_results, source_type="Instagram")

        return {
            "success": True,
            "headline": headline,
            "content": content,
            "source_url": url,
            "source_type": "instagram",
            "scraped_metadata": {
                "og_title": metadata.get("title", ""),
                "og_description": metadata.get("description", ""),
                "og_image": metadata.get("image_url", ""),
                "context_quality": claim_data.get("context_quality", "LOW"),
                "context_note": claim_data.get("context_note", "")
            },
            "social_media_analysis": social_verdict,
            "similar_articles": search_results
        }

    # ──────────────────────────────────────────────
    # Image Upload Analysis
    # ──────────────────────────────────────────────

    def _analyze_image_with_vision(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Send image to Groq Vision model for description + OCR text extraction.
        """
        if not self.client:
            return {
                "image_description": "Vision model unavailable. Please ensure GROQ_API_KEY is configured.",
                "extracted_text": "",
                "headline": "Image Analysis",
                "content": ""
            }

        # Determine MIME type
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "jpeg"
        mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp", "gif": "image/gif"}
        mime_type = mime_map.get(ext, "image/jpeg")

        # Encode to base64
        b64_image = base64.b64encode(image_bytes).decode("utf-8")

        prompt = """You are TruthLens, an AI news verification system analyzing an uploaded image.

Analyze this image carefully and provide:
1. A detailed description of what the image shows (people, events, text overlays, graphics, logos)
2. Extract ALL visible text from the image EXACTLY as written (OCR). Include headlines, captions, watermarks, chyrons, social media text, everything.
3. Identify what NEWS CLAIM or information this image is trying to convey
4. A clear headline summarizing the news claim in the image

Return a valid JSON object:
{
  "image_description": "Detailed description of the image contents",
  "extracted_text": "ALL visible text extracted from the image, preserving line breaks with \\n",
  "headline": "Clear headline summarizing the news claim shown",
  "content": "2-4 sentence description of the news claim or information being conveyed",
  "image_type": "NEWS_SCREENSHOT" | "SOCIAL_MEDIA_POST" | "MEME" | "INFOGRAPHIC" | "PHOTOGRAPH" | "OTHER",
  "has_text": true,
  "text_confidence": "HIGH" | "MEDIUM" | "LOW"
}
Respond with JSON only."""

        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{b64_image}"
                                }
                            }
                        ]
                    }
                ],
                model=settings.GROQ_VISION_MODEL,
                temperature=0.1,
                max_tokens=1500
            )

            raw = completion.choices[0].message.content.strip()
            cleaned = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
            cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)

            json_match = re.search(r'(\{[\s\S]*\})', cleaned)
            if json_match:
                return json.loads(json_match.group(1))
        except Exception as e:
            print(f"[InstagramAnalyzer] Vision analysis error: {e}")

        return {
            "image_description": "Could not analyze image with vision model.",
            "extracted_text": "",
            "headline": "Image Analysis",
            "content": "The vision model could not process this image. Try uploading a clearer image.",
            "image_type": "OTHER",
            "has_text": False,
            "text_confidence": "LOW"
        }

    async def analyze_image(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Full image analysis pipeline:
        1. Vision model for description + OCR
        2. Web search for similar news
        3. LLM cross-reference verdict
        """
        # Step 1: Vision model analysis
        vision_result = self._analyze_image_with_vision(image_bytes, filename)

        headline = vision_result.get("headline", "Image Analysis")
        content = vision_result.get("content", "")
        extracted_text = vision_result.get("extracted_text", "")

        # Build search query from extracted text or description
        search_query = extracted_text[:200] if extracted_text else headline
        if not search_query or len(search_query.strip()) < 10:
            search_query = vision_result.get("image_description", "")[:200]

        # Step 2: Search for similar news
        search_results = self._search_similar_news(search_query) if search_query.strip() else []

        # Step 3: LLM cross-references with combined context
        combined_content = content
        if extracted_text:
            combined_content += f"\n\nExtracted Text from Image:\n{extracted_text}"

        social_verdict = self._llm_crosscheck_verdict(
            headline, combined_content, search_results, source_type="Uploaded Image"
        )

        return {
            "success": True,
            "headline": headline,
            "content": content,
            "source_type": "image_upload",
            "image_analysis": {
                "description": vision_result.get("image_description", ""),
                "extracted_text": extracted_text,
                "image_type": vision_result.get("image_type", "OTHER"),
                "has_text": vision_result.get("has_text", False),
                "text_confidence": vision_result.get("text_confidence", "LOW")
            },
            "social_media_analysis": social_verdict,
            "similar_articles": search_results
        }


instagram_analyzer = InstagramAnalyzer()
