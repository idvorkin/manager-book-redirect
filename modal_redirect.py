#!python3
from Redirect.shared import get_html_for_redirect

# import asyncio
from typing import Dict
from icecream import ic
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from modal import Image, App, asgi_app

web_app = FastAPI()
app = App("igor-blog")  # Note: prior to April 2024, "app" was called "stub"


from modal import Image

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
    parts = full_path.split('/', 2)
    
    param1 = parts[0] if len(parts) > 0 else None
    param2 = parts[1] if len(parts) > 1 else None

    if not full_path or full_path == "favicon.ico":
        param1 = None
        param2 = None
            
    html_content = get_html_for_redirect(param1, param2)
    return HTMLResponse(content=html_content, status_code=200)

