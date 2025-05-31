#!python3
import requests
from bs4 import BeautifulSoup

# import asyncio
from typing import Dict
from icecream import ic
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from modal import Image, App, asgi_app


# Embedded shared functions (from Redirect/shared.py)
def humanize_url_part(s):
    if s is None:
        return ""
    return s.replace("-", " ").capitalize()


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


def get_preview_image_from_url(url):
    try:
        r = requests.get(url, timeout=5)
        html = r.text
        soup = BeautifulSoup(html, "html.parser")

        image = soup.find("meta", property="og:image")
        if image and image.get("content"):
            return image["content"]
    except Exception as e:
        ic(f"Error getting preview image: {e}")

    # Fallback image
    return "https://github.com/idvorkin/blob/raw/master/idvorkin-bunny-ears-ar-2020-with-motto-1200-628.png"


def get_html_for_redirect(param1, param2):
    title, page, anchor = param_remap_legacy(param1, param2)

    description = "Description Ignored"
    preview_image = "https://github.com/idvorkin/blob/raw/master/idvorkin-bunny-ears-ar-2020-with-motto-1200-628.png"
    p = get_preview_image_from_url(f"https://idvork.in/{page}")
    if p:
        preview_image = p

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


@web_app.get("/{full_path:path}")
async def read_all(request: Request, full_path: str):
    parts = full_path.split("/", 2)

    param1 = parts[0] if len(parts) > 0 else None
    param2 = parts[1] if len(parts) > 1 else None

    if not full_path or full_path == "favicon.ico":
        param1 = None
        param2 = None

    html_content = get_html_for_redirect(param1, param2)
    return HTMLResponse(content=html_content, status_code=200)
