import re
import socket
from urllib.parse import urlparse
from typing import Dict, Any, Tuple, Optional
import httpx
from bs4 import BeautifulSoup

try:
    import trafilatura
except ImportError:
    trafilatura = None

# Block private/local IP ranges for SSRF prevention
BLOCKED_IP_PATTERNS = [
    r"^127\.",
    r"^10\.",
    r"^172\.(1[6-9]|2[0-9]|3[0-1])\.",
    r"^192\.168\.",
    r"^localhost$",
    r"^0\.0\.0\.0$"
]

class URLExtractor:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }

    def is_safe_url(self, url: str) -> Tuple[bool, str]:
        """Validates that URL has valid scheme and does not point to internal/private infrastructure."""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ["http", "https"]:
                return False, "Please enter a complete web link starting with https:// or http://"

            hostname = parsed.hostname
            if not hostname:
                return False, "Invalid website address."

            for pattern in BLOCKED_IP_PATTERNS:
                if re.match(pattern, hostname, re.IGNORECASE):
                    return False, "Access to internal network addresses is restricted."

            return True, "URL is safe"
        except Exception as e:
            return False, f"URL error: {str(e)}"

    async def extract_from_url(self, url: str) -> Dict[str, Any]:
        """Fetches page content and extracts title, author, date, domain, and article text."""
        is_safe, reason = self.is_safe_url(url)
        if not is_safe:
            return {
                "success": False,
                "error": reason,
                "url": url,
                "title": "",
                "content": "",
                "publisher": "",
                "is_https": False
            }

        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        is_https = parsed.scheme == "https"

        # 1. Try Trafilatura if available (fast and extracts high-quality article bodies)
        if trafilatura:
            try:
                downloaded = trafilatura.fetch_url(url)
                if downloaded:
                    traf_text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
                    metadata = trafilatura.extract_metadata(downloaded)
                    
                    if traf_text and len(traf_text.strip()) > 80:
                        title = (metadata.title if metadata and metadata.title else "").strip()
                        author = (metadata.author if metadata and metadata.author else "").strip()
                        pub_date = (metadata.date if metadata and metadata.date else "").strip()

                        if not title:
                            soup = BeautifulSoup(downloaded, "html.parser")
                            title = soup.title.string.strip() if soup.title else domain

                        return {
                            "success": True,
                            "url": url,
                            "title": title,
                            "content": traf_text.strip(),
                            "publisher": domain,
                            "domain": domain,
                            "author": author,
                            "published_date": pub_date,
                            "is_https": is_https,
                            "length": len(traf_text)
                        }
            except Exception as e:
                print(f"[URLExtractor] Trafilatura pass error: {e}")

        # 2. HTTP Client Fallback with realistic browser emulation
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=self.headers) as client:
                response = await client.get(url)
                if response.status_code == 403:
                    return {
                        "success": False,
                        "error": f"The website ({domain}) blocked automated reading (HTTP 403 Bot Protection / Paywall). Please copy and paste the article text directly.",
                        "url": url,
                        "publisher": domain,
                        "is_https": is_https
                    }
                elif response.status_code == 404:
                    return {
                        "success": False,
                        "error": f"The webpage was not found (HTTP 404). Please verify the link or paste the text manually.",
                        "url": url,
                        "publisher": domain,
                        "is_https": is_https
                    }
                elif response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Website returned status code {response.status_code}. Please paste the article text manually.",
                        "url": url,
                        "publisher": domain,
                        "is_https": is_https
                    }

                html_content = response.text
                soup = BeautifulSoup(html_content, "html.parser")

                # Remove noise
                for element in soup(["script", "style", "nav", "footer", "aside", "header", "form", "noscript", "svg", "button", "iframe"]):
                    element.decompose()

                # Extract Title
                title = ""
                og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
                if og_title and og_title.get("content"):
                    title = og_title["content"].strip()
                elif soup.title and soup.title.string:
                    title = soup.title.string.strip()
                elif soup.find("h1"):
                    title = soup.find("h1").get_text().strip()

                # Extract Body
                body_text = ""
                article_tag = soup.find("article") or soup.find("main") or soup.find(id=re.compile(r"article|content|story|body", re.I))
                
                if article_tag:
                    paragraphs = [p.get_text().strip() for p in article_tag.find_all("p") if len(p.get_text().strip()) > 25]
                    body_text = "\n\n".join(paragraphs)
                
                if not body_text or len(body_text) < 80:
                    paragraphs = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 25]
                    body_text = "\n\n".join(paragraphs)

                body_text = re.sub(r'\n{3,}', '\n\n', body_text).strip()

                if len(body_text) < 40:
                    return {
                        "success": False,
                        "error": f"Could not extract article body from {domain} (page may be paywalled or rendered via JavaScript). Please copy and paste the article text manually.",
                        "url": url,
                        "title": title,
                        "publisher": domain,
                        "is_https": is_https
                    }

                return {
                    "success": True,
                    "url": url,
                    "title": title or domain,
                    "content": body_text,
                    "publisher": domain,
                    "domain": domain,
                    "author": "",
                    "published_date": "",
                    "is_https": is_https,
                    "length": len(body_text)
                }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": f"The website ({domain}) took too long to respond. Please paste the article text manually.",
                "url": url,
                "publisher": domain,
                "is_https": is_https
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unable to fetch link: {str(e)}. Please paste the article text instead.",
                "url": url,
                "publisher": domain,
                "is_https": is_https
            }

url_extractor = URLExtractor()
