#!python3
import urllib.parse

# import asyncio
from typing import Optional

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
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]
    
    return truncated + "..."


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
            return image["content"]
    except requests.RequestException as e:
        ic(f"Request error getting preview image from {url}: {e}")
    except Exception as e:
        ic(f"Unexpected error getting preview image from {url}: {e}")

    return DEFAULT_PREVIEW_IMAGE


def get_preview_text_from_url(
    url: str, anchor: Optional[str] = None, max_chars: int = DEFAULT_PREVIEW_MAX_CHARS
) -> Optional[str]:
    """Fetch paragraphs after the title/anchor from the blog post until we reach max_chars."""
    if not validate_url(url):
        return None

    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        html = r.text
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

    except requests.RequestException as e:
        ic(f"Request error getting preview text from {url} (anchor: {anchor}): {e}")
    except Exception as e:
        ic(f"Unexpected error getting preview text from {url}: {e}")

    return None


def generate_title(page, anchor):
    """Generate a title from page and anchor"""
    if page == "manager-book" and not anchor:
        return "Igor's book of management"
    elif page == "manager-book" and anchor:
        # Special handling for manager-book
        anchor_text = hup(anchor)
        return f"{anchor_text} (Igor's Manager Book)"
    elif anchor:
        # Capitalize and replace hyphens with spaces
        anchor_text = hup(anchor)
        page_text = hup(page)
        return f"{anchor_text} ({page_text})"
    else:
        # Just the page
        return hup(page)


def get_html_for_redirect_simple(title, page, anchor):
    """Simplified HTML generation without legacy remapping"""
    # Always fetch preview text for description
    description = "Description Ignored"
    preview_text = get_preview_text_from_url(f"https://idvork.in/{page}", anchor)
    if preview_text:
        description = preview_text

    preview_image = get_preview_image_from_url(f"https://idvork.in/{page}")
    
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
        url = f"https://tinyurl.com/igor-says?path={urllib.parse.quote(path_param)}"
    elif page != "manager-book":
        url = f"https://tinyurl.com/igor-says?path={urllib.parse.quote(page)}"
    else:
        url = "https://tinyurl.com/igor-says"

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
