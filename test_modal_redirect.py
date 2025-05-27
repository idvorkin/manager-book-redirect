import pytest
import httpx
from bs4 import BeautifulSoup # For parsing HTML and checking tags

# Assuming modal_redirect.py is in the same directory or accessible in PYTHONPATH
# and web_app is the FastAPI instance.
from modal_redirect import web_app

# Helper function to extract meta tag content
def get_meta_og_content(html_text, property_name):
    soup = BeautifulSoup(html_text, 'html.parser')
    tag = soup.find("meta", property=property_name)
    return tag["content"] if tag else None

# Helper function to extract redirect URL
def get_redirect_url(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    script_tag = soup.find("script")
    if script_tag:
        script_content = script_tag.string
        # Example: window.location.href = "https://idvork.in/page#anchor";
        if "window.location.href" in script_content:
            url_part = script_content.split("window.location.href = \"")[1]
            return url_part.split("\";")[0]
    return None

@pytest.mark.asyncio
async def test_redirect_no_params():
    async with httpx.AsyncClient(app=web_app, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    html = response.text
    assert get_meta_og_content(html, "og:title") == "Igor's book of management"
    assert get_meta_og_content(html, "og:url") == "https://idvork.in/manager-book#"
    assert get_redirect_url(html) == "https://idvork.in/manager-book#"

@pytest.mark.asyncio
async def test_redirect_favicon():
    async with httpx.AsyncClient(app=web_app, base_url="http://test") as client:
        response = await client.get("/favicon.ico")
    assert response.status_code == 200
    html = response.text
    assert get_meta_og_content(html, "og:title") == "Igor's book of management" # Or however favicon is handled
    assert get_meta_og_content(html, "og:url") == "https://idvork.in/manager-book#"
    assert get_redirect_url(html) == "https://idvork.in/manager-book#"


@pytest.mark.asyncio
async def test_redirect_one_param_topic():
    async with httpx.AsyncClient(app=web_app, base_url="http://test") as client:
        response = await client.get("/my-topic")
    assert response.status_code == 200
    html = response.text
    assert get_meta_og_content(html, "og:title") == "My topic (Igor's Manager Book)"
    assert get_meta_og_content(html, "og:url") == "https://idvork.in/manager-book#my-topic"
    assert get_redirect_url(html) == "https://idvork.in/manager-book#my-topic"

@pytest.mark.asyncio
async def test_redirect_two_params_page_and_topic():
    async with httpx.AsyncClient(app=web_app, base_url="http://test") as client:
        response = await client.get("/my-page/my-topic")
    assert response.status_code == 200
    html = response.text
    assert get_meta_og_content(html, "og:title") == "My topic (My page)" # Note: hup capitalizes
    assert get_meta_og_content(html, "og:url") == "https://idvork.in/my-page#my-topic"
    assert get_redirect_url(html) == "https://idvork.in/my-page#my-topic"

@pytest.mark.asyncio
async def test_redirect_three_params_ignored():
    async with httpx.AsyncClient(app=web_app, base_url="http://test") as client:
        response = await client.get("/my-page/my-topic/extra-part")
    assert response.status_code == 200
    html = response.text
    # Behavior for >2 params is to use first two.
    assert get_meta_og_content(html, "og:title") == "My topic (My page)"
    assert get_meta_og_content(html, "og:url") == "https://idvork.in/my-page#my-topic"
    assert get_redirect_url(html) == "https://idvork.in/my-page#my-topic"
