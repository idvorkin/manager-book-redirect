import urllib.parse
from typing import Optional

import requests
from bs4 import BeautifulSoup

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
            print(f"URL domain not allowed: {parsed.netloc}")
            return False
        # Only allow HTTP/HTTPS
        if parsed.scheme not in ["http", "https"]:
            print(f"URL scheme not allowed: {parsed.scheme}")
            return False
        return True
    except Exception as e:
        print(f"Error validating URL {url}: {e}")
        return False


def truncate_text(text: str, max_chars: int) -> str:
    """Truncate text to max_chars with ellipsis if needed"""
    if len(text) > max_chars:
        return text[:max_chars] + "..."
    return text


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
        print(f"Request error getting preview image from {url}: {e}")
    except Exception as e:
        print(f"Unexpected error getting preview image from {url}: {e}")

    return DEFAULT_PREVIEW_IMAGE


def get_preview_text_from_url(
    url: str, anchor: Optional[str] = None, max_chars: int = DEFAULT_PREVIEW_MAX_CHARS
) -> Optional[str]:
    """Fetch the first paragraph after the title/anchor from the blog post."""
    if not validate_url(url):
        return None

    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")

        # If we have an anchor, try to find the content after that specific section
        if anchor:
            # Try to find the heading with this ID
            heading = soup.find(id=anchor)
            if heading:
                # Get the next sibling paragraphs after the heading
                current = heading.find_next_sibling()
                while current:
                    if current.name == "p" and current.get_text(strip=True):
                        text = current.get_text(strip=True)
                        return truncate_text(text, max_chars)
                    # Stop if we hit another heading
                    elif current.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                        break
                    current = current.find_next_sibling()

        # Fallback: find the first paragraph in the main content
        # Look for article or main content area
        article = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", class_="content")
        )
        if article:
            first_para = article.find("p")
            if first_para:
                text = first_para.get_text(strip=True)
                return truncate_text(text, max_chars)

        # Last resort: find any paragraph
        first_para = soup.find("p")
        if first_para:
            text = first_para.get_text(strip=True)
            return truncate_text(text, max_chars)

    except requests.RequestException as e:
        print(f"Request error getting preview text from {url} (anchor: {anchor}): {e}")
    except Exception as e:
        print(f"Unexpected error getting preview text from {url}: {e}")

    return None


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
