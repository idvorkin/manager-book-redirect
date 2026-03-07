#!python3
import urllib.parse
from datetime import datetime, timedelta

# import asyncio
from typing import Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from icecream import ic
from modal import App, Image, asgi_app

# Constants
DEFAULT_PREVIEW_MAX_CHARS = 400
DEFAULT_PREVIEW_IMAGE = "https://github.com/idvorkin/blob/raw/master/idvorkin-bunny-ears-ar-2020-with-motto-1200-628.png"
ALLOWED_DOMAINS = ["idvork.in", "www.idvork.in"]
REQUEST_TIMEOUT = 5
CACHE_TTL_MINUTES = 15  # Cache pages for 15 minutes

# Cache for webpage HTML: key = url, value = (html_content, expiry_time)
page_cache: Dict[str, Tuple[str, datetime]] = {}


# Helper functions
def validate_url(url: str) -> bool:
    """Validate that the URL is safe to fetch"""
    try:
        parsed = urllib.parse.urlparse(url)
        # Only allow specific domains
        if parsed.netloc not in ALLOWED_DOMAINS:
            ic(f"URL domain not allowed: {parsed.netloc}")
            return False
        # Only allow HTTP/HTTPS
        if parsed.scheme not in ["http", "https"]:
            ic(f"URL scheme not allowed: {parsed.scheme}")
            return False
        return True
    except Exception as e:
        ic(f"Error validating URL {url}: {e}")
        return False


def truncate_text(text: str, max_chars: int) -> str:
    """Truncate text to max_chars with ellipsis if needed, ending on a word boundary"""
    if len(text) <= max_chars:
        return text

    # Truncate to max_chars
    truncated = text[:max_chars]

    # Find the last space to end on a word boundary
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]

    return truncated + "..."


def fetch_cached_html(url: str) -> Optional[str]:
    """Fetch HTML from cache or from URL if not cached"""
    if not validate_url(url):
        return None

    # Check cache first
    now = datetime.now()
    if url in page_cache:
        cached_html, expiry_time = page_cache[url]
        if now < expiry_time:
            # Cache hit - return cached HTML
            return cached_html
        else:
            # Cache expired - remove it
            del page_cache[url]

    # Cache miss or expired - fetch from URL
    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        html = r.text

        # Cache the result for future use
        expiry_time = now + timedelta(minutes=CACHE_TTL_MINUTES)
        page_cache[url] = (html, expiry_time)

        return html
    except requests.RequestException:
        # Return None on error
        return None
    except Exception:
        # Return None on any other error
        return None


# Embedded shared functions (from Redirect/shared.py)
def humanize_url_part(s):
    if s is None:
        return ""
    text = s.replace("-", " ").capitalize()
    # Keep Igor capitalized
    text = text.replace("igor", "Igor")
    return text


# short alias
def hup(s):
    return humanize_url_part(s)


def param_remap_legacy(param1, param2):
    # excited to code with python 3.10 :)
    # returns title, page, anchor

    no_params = param1 is None and param2 is None
    if no_params:
        # Assume manager book, with no anchor
        return "Igor's book of management", "manager-book", ""

    single_param = param2 is None

    if single_param:
        # Only an anchor is provided, default to manager-book
        anchor = param1
        return f"{hup(anchor)} (Igor's Manager Book)", "manager-book", anchor

    # page and anchor provided
    page, anchor = param1, param2
    return f"{hup(anchor)} ({(hup(page))})", page, anchor


def get_preview_image_from_url(url: str) -> str:
    """Fetch the preview image from a URL"""
    if not validate_url(url):
        return DEFAULT_PREVIEW_IMAGE

    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")

        image = soup.find("meta", property="og:image")
        if image and image.get("content"):
            return _resolve_image_url(image["content"], url)
    except requests.RequestException as e:
        ic(f"Request error getting preview image from {url}: {e}")
    except Exception as e:
        ic(f"Unexpected error getting preview image from {url}: {e}")

    return DEFAULT_PREVIEW_IMAGE


def get_preview_text_from_url(
    url: str, anchor: Optional[str] = None, max_chars: int = DEFAULT_PREVIEW_MAX_CHARS
) -> Optional[str]:
    """Fetch paragraphs after the title/anchor from the blog post until we reach max_chars."""
    # Get cached or fresh HTML
    html = fetch_cached_html(url)
    if not html:
        return None

    try:
        soup = BeautifulSoup(html, "html.parser")

        collected_text = []
        total_chars = 0

        # If we have an anchor, try to find the content after that specific section
        if anchor:
            # Try to find the heading with this ID
            heading = soup.find(id=anchor)
            if heading:
                # Get the next sibling paragraphs after the heading
                current = heading.find_next_sibling()
                while current and total_chars < max_chars:
                    if current.name == "p" and current.get_text(strip=True):
                        text = current.get_text(separator=" ", strip=True)
                        collected_text.append(text)
                        total_chars += len(text) + 1  # +1 for space between paragraphs
                    # Stop if we hit another heading
                    elif current.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                        break
                    current = current.find_next_sibling()

                if collected_text:
                    combined_text = " ".join(collected_text)
                    return truncate_text(combined_text, max_chars)

        # Fallback: find paragraphs in the main content
        # Look for article or main content area
        article = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", class_="content")
        )

        if article:
            paragraphs = article.find_all("p")
        else:
            # Last resort: find any paragraphs
            paragraphs = soup.find_all("p")

        # Collect paragraphs until we reach max_chars
        for para in paragraphs:
            if total_chars >= max_chars:
                break
            text = para.get_text(separator=" ", strip=True)
            if text:  # Only add non-empty paragraphs
                collected_text.append(text)
                total_chars += len(text) + 1  # +1 for space between paragraphs

        if collected_text:
            combined_text = " ".join(collected_text)
            return truncate_text(combined_text, max_chars)

    except Exception as e:
        ic(f"Error parsing HTML for preview text from {url}: {e}")

    return None


def get_heading_text_from_url(url: str, anchor: Optional[str] = None) -> Optional[str]:
    """Fetch the actual heading text from the document"""
    if not anchor:
        return None

    # Get cached or fresh HTML
    html = fetch_cached_html(url)
    if not html:
        return None

    try:
        soup = BeautifulSoup(html, "html.parser")

        # Try to find the heading with this ID
        heading = soup.find(id=anchor)
        if heading and heading.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            text = heading.get_text(strip=True)
            # Return text if non-empty
            if text:
                return text

    except Exception:
        # Silent error - fallback will be used
        pass

    return None


def _resolve_image_url(src: str, page_url: str) -> str:
    """Resolve a potentially relative image URL to an absolute URL."""
    if src.startswith(("http://", "https://")):
        return src
    parsed = urllib.parse.urlparse(page_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    if src.startswith("/"):
        return base + src
    return base + "/" + src


def get_section_image_from_url(url: str, anchor: Optional[str] = None) -> Optional[str]:
    """Find the first image in the section after the anchor heading."""
    if not anchor:
        return None

    html = fetch_cached_html(url)
    if not html:
        return None

    try:
        soup = BeautifulSoup(html, "html.parser")
        heading = soup.find(id=anchor)
        if not heading:
            return None

        heading_level = (
            int(heading.name[1])
            if heading.name in ["h1", "h2", "h3", "h4", "h5", "h6"]
            else None
        )
        if heading_level is None:
            return None

        current = heading.find_next_sibling()
        while current:
            # Stop at a heading of same or higher level
            if current.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                current_level = int(current.name[1])
                if current_level <= heading_level:
                    break

            # Check for img directly or inside this element
            if current.name == "img" and current.get("src"):
                return _resolve_image_url(current["src"], url)
            img = current.find("img")
            if img and img.get("src"):
                return _resolve_image_url(img["src"], url)

            current = current.find_next_sibling()

    except Exception:
        pass

    return None


def generate_title(page, anchor):
    """Generate a title from page and anchor"""
    if page == "manager-book" and not anchor:
        return "Igor's book of management"
    elif page == "manager-book" and anchor:
        # Try to get actual heading text from the document
        actual_heading = get_heading_text_from_url(f"https://idvork.in/{page}", anchor)
        if actual_heading:
            return f"{actual_heading} (Igor's Manager Book)"
        # Fallback to URL-based generation
        anchor_text = hup(anchor)
        return f"{anchor_text} (Igor's Manager Book)"
    elif anchor:
        # Try to get actual heading text from the document
        actual_heading = get_heading_text_from_url(f"https://idvork.in/{page}", anchor)
        if actual_heading:
            page_text = hup(page)
            return f"{actual_heading} ({page_text})"
        # Fallback to URL-based generation
        anchor_text = hup(anchor)
        page_text = hup(page)
        return f"{anchor_text} ({page_text})"
    else:
        # Just the page - keep existing logic
        return hup(page)


def get_html_for_redirect_simple(title, page, anchor):
    """Simplified HTML generation without legacy remapping"""
    # Always fetch preview text for description
    description = "Description Ignored"
    preview_text = get_preview_text_from_url(f"https://idvork.in/{page}", anchor)
    if preview_text:
        description = preview_text

    # Use section-specific image if available, otherwise page-level og:image
    section_image = get_section_image_from_url(f"https://idvork.in/{page}", anchor)
    preview_image = (
        section_image
        if section_image
        else get_preview_image_from_url(f"https://idvork.in/{page}")
    )

    # Build the redirect URL
    # Always include # for backwards compatibility
    redirect_url = f"https://idvork.in/{page}#{anchor if anchor else ''}"

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <!-- Open Graph -->
    <meta property="og:title" content="{title}" />
    <meta property="og:url" content="{redirect_url}" />
    <meta property="og:description" content="{description}" />
    <meta name="description" content="{description}" />
    <meta property="og:image" content="{preview_image}" />

    <!-- Icons -->
    <link rel="apple-touch-icon" sizes="180x180"
    href="https://github.com/idvorkin/blob/raw/master/idvorkin-bunny-ears-ar-2020-180-180.png" />
    <link rel="icon" type="image/png" sizes="32x32"
    href="https://github.com/idvorkin/blob/raw/master/idvorkin-bunny-ears-ar-2020-32-32.png" />
</head>
<body>
    <script>
        window.location.href = "{redirect_url}";
    </script>
    Redirecting to: {redirect_url}
</body>
</html>
"""
    return html


# Keep the old function for backwards compatibility but simplified
def get_html_for_redirect(param1, param2):
    title, page, anchor = param_remap_legacy(param1, param2)

    # Always fetch preview text for description
    description = "Description Ignored"
    preview_text = get_preview_text_from_url(f"https://idvork.in/{page}", anchor)
    if preview_text:
        description = preview_text

    preview_image = get_preview_image_from_url(f"https://idvork.in/{page}")

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <!-- Open Graph
        https://stackoverflow.com/questions/19778620/provide-an-image-for-whatsapp-link-sharing
    -->
    <meta property="og:title" content="{title}" />
    <meta property="og:url" content="https://idvork.in/{page}#{anchor}" />
    <meta property="og:description" content="{description}" />
    <meta name="description" content="{description}" />
    <meta property="og:image"
        content="{preview_image}" />

<!-- Icons -->
    <link rel="apple-touch-icon" sizes="180x180"
    href="https://github.com/idvorkin/blob/raw/master/idvorkin-bunny-ears-ar-2020-180-180.png" />
    <link rel="icon" type="image/png" sizes="32x32"
    href="https://github.com/idvorkin/blob/raw/master/idvorkin-bunny-ears-ar-2020-32-32.png" />
</head>
<body>
    <script>
        window.location.href = "https://idvork.in/{page}#{anchor}";
    </script>
    Redirector:
        - Param1:    {param1},
        - Param2: {param2}
        - Title: {title},
        - Page: {page},
        - Anchor: {anchor}
        - Image: {preview_image}
</body>
</html>
"""
    return html


web_app = FastAPI()
app = App("igor-blog")  # Note: prior to April 2024, "app" was called "stub"

default_image = Image.debian_slim(python_version="3.10").pip_install(
    ["icecream", "httpx", "requests", "beautifulsoup4", "fastapi"]
)


# https://modal.com/docs/guide/webhooks
@app.function(image=default_image)
@asgi_app()
def fastapi_app():
    return web_app


@web_app.get("/preview_text/{full_path:path}")
async def get_preview(request: Request, full_path: str):
    """API endpoint to get just the preview text for a given page/anchor"""
    # Check for path query parameter first
    path_param = request.query_params.get("path")

    if path_param:
        # Parse the path parameter (e.g., "manager-book#leadership")
        if "#" in path_param:
            page, anchor = path_param.split("#", 1)
        else:
            # No anchor, just a page
            page = path_param
            anchor = None
    else:
        # Use the URL path segments as before
        parts = full_path.split("/", 2)
        if len(parts) >= 2:
            page = parts[0]
            anchor = parts[1]
        elif len(parts) == 1 and parts[0]:
            # Single param - for backwards compatibility, treat as manager-book anchor
            page = "manager-book"
            anchor = parts[0]
        else:
            # Default to manager-book if nothing provided
            page = "manager-book"
            anchor = None

    # Fetch the preview text
    preview_text = get_preview_text_from_url(f"https://idvork.in/{page}", anchor)

    # Build tinyurl with query parameter for the path
    if anchor:
        path_param = f"{page}#{anchor}"
        url = f"https://tinyurl.com/igor-blog?path={urllib.parse.quote(path_param)}"
    elif page != "manager-book":
        url = f"https://tinyurl.com/igor-blog?path={urllib.parse.quote(page)}"
    else:
        url = "https://tinyurl.com/igor-blog"

    # Check for text_only parameter
    if request.query_params.get("text_only") == "true":
        # Return plain text format for easy copying
        if preview_text:
            plain_text = f"From: {url}\n\n{preview_text}"
        else:
            plain_text = f"From: {url}\n\nNo preview available"
        return PlainTextResponse(content=plain_text)

    if preview_text:
        return {"preview": preview_text, "url": url}
    else:
        return {"preview": "No preview available", "url": url}


@web_app.get("/preview/{full_path:path}")
async def preview_og(request: Request, full_path: str):
    """Show a visual preview of how the link will appear across different platforms."""
    # Parse path the same way as the redirect endpoint
    path_param = request.query_params.get("path")

    if path_param:
        if "#" in path_param:
            page, anchor = path_param.split("#", 1)
        else:
            page = path_param
            anchor = None
    else:
        parts = full_path.split("/", 2)
        if not full_path:
            page = "manager-book"
            anchor = None
        elif len(parts) >= 2:
            page = parts[0]
            anchor = parts[1]
        elif len(parts) == 1:
            page = "manager-book"
            anchor = parts[0]
        else:
            page = "manager-book"
            anchor = None

    title = generate_title(page, anchor)
    description = "Description Ignored"
    preview_text = get_preview_text_from_url(f"https://idvork.in/{page}", anchor)
    if preview_text:
        description = preview_text

    section_image = get_section_image_from_url(f"https://idvork.in/{page}", anchor)
    preview_image = (
        section_image
        if section_image
        else get_preview_image_from_url(f"https://idvork.in/{page}")
    )
    redirect_url = f"https://idvork.in/{page}#{anchor if anchor else ''}"

    # Build tinyurl for sharing
    if anchor:
        tinyurl_path = f"{page}#{anchor}"
        tinyurl = (
            f"https://tinyurl.com/igor-blog?path={urllib.parse.quote(tinyurl_path)}"
        )
    elif page != "manager-book":
        tinyurl = f"https://tinyurl.com/igor-blog?path={urllib.parse.quote(page)}"
    else:
        tinyurl = "https://tinyurl.com/igor-blog"

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>OG Preview: {title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 24px; }}
        h1 {{ font-size: 20px; margin-bottom: 8px; color: #333; }}
        .subtitle {{ color: #666; margin-bottom: 8px; font-size: 14px; word-break: break-all; }}
        .share-url {{ margin-bottom: 24px; }}
        .share-url a {{ color: #1264a3; font-size: 14px; word-break: break-all; }}
        .share-url .copy-btn {{ background: #1264a3; color: #fff; border: none; border-radius: 4px; padding: 4px 12px; cursor: pointer; font-size: 13px; margin-left: 8px; }}
        .share-url .copy-btn:hover {{ background: #0d4f82; }}
        .metadata {{ background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 24px; border: 1px solid #e0e0e0; }}
        .metadata dt {{ font-weight: 600; color: #555; font-size: 12px; text-transform: uppercase; margin-top: 8px; }}
        .metadata dt:first-child {{ margin-top: 0; }}
        .metadata dd {{ color: #333; margin-bottom: 4px; word-break: break-all; }}
        .platforms {{ display: flex; flex-wrap: wrap; gap: 24px; }}
        .platform {{ flex: 1; min-width: 320px; max-width: 500px; }}
        .platform-label {{ font-size: 13px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }}

        /* iMessage style */
        .imessage {{ background: #e9e9eb; border-radius: 18px; padding: 4px; overflow: hidden; }}
        .imessage .card {{ border-radius: 16px; overflow: hidden; background: #fff; }}
        .imessage .card img {{ width: 100%; height: 180px; object-fit: cover; }}
        .imessage .card-body {{ padding: 8px 12px 10px; }}
        .imessage .card-body .domain {{ font-size: 11px; color: #8e8e93; text-transform: uppercase; }}
        .imessage .card-body .title {{ font-size: 15px; font-weight: 600; color: #000; margin-top: 2px; }}
        .imessage .card-body .desc {{ font-size: 13px; color: #8e8e93; margin-top: 2px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}

        /* WhatsApp style */
        .whatsapp {{ background: #e5ddd5; border-radius: 8px; padding: 8px; }}
        .whatsapp .card {{ background: #fff; border-radius: 8px; overflow: hidden; border-left: 4px solid #25d366; }}
        .whatsapp .card img {{ width: 100%; height: 160px; object-fit: cover; }}
        .whatsapp .card-body {{ padding: 8px 12px; }}
        .whatsapp .card-body .domain {{ font-size: 12px; color: #027eb5; }}
        .whatsapp .card-body .title {{ font-size: 14px; font-weight: 600; color: #000; margin-top: 2px; }}
        .whatsapp .card-body .desc {{ font-size: 13px; color: #666; margin-top: 4px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}

        /* Slack style */
        .slack {{ background: #fff; border-radius: 8px; padding: 12px; border: 1px solid #e0e0e0; }}
        .slack .card {{ border-left: 4px solid #e0e0e0; padding-left: 12px; }}
        .slack .card .domain {{ font-size: 12px; font-weight: 700; color: #1d1c1d; }}
        .slack .card .title {{ font-size: 15px; font-weight: 700; color: #1264a3; margin-top: 4px; }}
        .slack .card .desc {{ font-size: 14px; color: #1d1c1d; margin-top: 4px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}
        .slack .card img {{ width: 100%; max-height: 200px; object-fit: cover; border-radius: 4px; margin-top: 8px; }}

        /* Google Chat style */
        .gchat {{ background: #fff; border-radius: 8px; padding: 12px; border: 1px solid #dadce0; }}
        .gchat .card {{ border: 1px solid #dadce0; border-radius: 8px; overflow: hidden; }}
        .gchat .card img {{ width: 100%; height: 160px; object-fit: cover; }}
        .gchat .card-body {{ padding: 12px; }}
        .gchat .card-body .domain {{ font-size: 12px; color: #5f6368; }}
        .gchat .card-body .title {{ font-size: 14px; font-weight: 500; color: #202124; margin-top: 4px; }}
        .gchat .card-body .desc {{ font-size: 13px; color: #5f6368; margin-top: 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
    </style>
</head>
<body>
    <h1>Link Preview for: {title}</h1>
    <p class="subtitle">{redirect_url}</p>
    <div class="share-url">
        Share: <a href="{tinyurl}" id="share-link">{tinyurl}</a>
        <button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('share-link').href)">Copy</button>
    </div>

    <div class="metadata">
        <dl>
            <dt>og:title</dt><dd>{title}</dd>
            <dt>og:description</dt><dd>{description}</dd>
            <dt>og:image</dt><dd>{preview_image}</dd>
            <dt>og:url</dt><dd>{redirect_url}</dd>
            <dt>Image source</dt><dd>{"Section image" if section_image else "Page-level og:image"}</dd>
            <dt>Share URL (tinyurl)</dt><dd><a href="{tinyurl}">{tinyurl}</a></dd>
        </dl>
    </div>

    <div class="platforms">
        <div class="platform">
            <div class="platform-label">iMessage</div>
            <div class="imessage"><div class="card">
                <img src="{preview_image}" alt="preview">
                <div class="card-body">
                    <div class="domain">idvork.in</div>
                    <div class="title">{title}</div>
                    <div class="desc">{description}</div>
                </div>
            </div></div>
        </div>

        <div class="platform">
            <div class="platform-label">WhatsApp</div>
            <div class="whatsapp"><div class="card">
                <img src="{preview_image}" alt="preview">
                <div class="card-body">
                    <div class="domain">idvork.in</div>
                    <div class="title">{title}</div>
                    <div class="desc">{description}</div>
                </div>
            </div></div>
        </div>

        <div class="platform">
            <div class="platform-label">Slack</div>
            <div class="slack"><div class="card">
                <div class="domain">idvork.in</div>
                <div class="title">{title}</div>
                <div class="desc">{description}</div>
                <img src="{preview_image}" alt="preview">
            </div></div>
        </div>

        <div class="platform">
            <div class="platform-label">Google Chat</div>
            <div class="gchat"><div class="card">
                <img src="{preview_image}" alt="preview">
                <div class="card-body">
                    <div class="domain">idvork.in</div>
                    <div class="title">{title}</div>
                    <div class="desc">{description}</div>
                </div>
            </div></div>
        </div>
    </div>
</body>
</html>
"""
    return HTMLResponse(content=html, status_code=200)


@web_app.get("/{full_path:path}")
async def read_all(request: Request, full_path: str):
    # Check for path query parameter first
    path_param = request.query_params.get("path")

    if path_param:
        # Parse the path parameter (e.g., "manager-book#leadership")
        if "#" in path_param:
            page, anchor = path_param.split("#", 1)
        else:
            # No anchor, just a page
            page = path_param
            anchor = None
    else:
        # Use the URL path segments as before
        parts = full_path.split("/", 2)

        if not full_path or full_path == "favicon.ico":
            # Default to manager-book
            page = "manager-book"
            anchor = None
        elif len(parts) >= 2:
            page = parts[0]
            anchor = parts[1]
        elif len(parts) == 1:
            # Single param could be either a page or an anchor for manager-book
            # For backwards compatibility, treat it as an anchor for manager-book
            page = "manager-book"
            anchor = parts[0]
        else:
            page = "manager-book"
            anchor = None

    # Generate title from page and anchor
    title = generate_title(page, anchor)

    # Generate the HTML with the simplified parameters
    html_content = get_html_for_redirect_simple(title, page, anchor)
    return HTMLResponse(content=html_content, status_code=200)
