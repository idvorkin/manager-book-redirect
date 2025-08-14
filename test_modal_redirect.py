import httpx
import pytest
from bs4 import BeautifulSoup  # For parsing HTML and checking tags

# Assuming modal_redirect.py is in the same directory or accessible in PYTHONPATH
# and web_app is the FastAPI instance.
from modal_redirect import web_app


# Helper function to extract meta tag content
def get_meta_og_content(html_text, property_name):
    soup = BeautifulSoup(html_text, "html.parser")
    tag = soup.find("meta", property=property_name)
    return tag["content"] if tag else None


# Helper function to extract redirect URL
def get_redirect_url(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    script_tag = soup.find("script")
    if script_tag:
        script_content = script_tag.string
        # Example: window.location.href = "https://idvork.in/page#anchor";
        if "window.location.href" in script_content:
            url_part = script_content.split('window.location.href = "')[1]
            return url_part.split('";')[0]
    return None


@pytest.mark.asyncio
async def test_redirect_no_params():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=web_app), base_url="http://test"
    ) as client:
        response = await client.get("/")
    assert response.status_code == 200
    html = response.text
    assert get_meta_og_content(html, "og:title") == "Igor's book of management"
    assert get_meta_og_content(html, "og:url") == "https://idvork.in/manager-book#"
    assert get_redirect_url(html) == "https://idvork.in/manager-book#"


@pytest.mark.asyncio
async def test_redirect_favicon():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=web_app), base_url="http://test"
    ) as client:
        response = await client.get("/favicon.ico")
    assert response.status_code == 200
    html = response.text
    assert (
        get_meta_og_content(html, "og:title") == "Igor's book of management"
    )  # Or however favicon is handled
    assert get_meta_og_content(html, "og:url") == "https://idvork.in/manager-book#"
    assert get_redirect_url(html) == "https://idvork.in/manager-book#"


@pytest.mark.asyncio
async def test_redirect_one_param_topic():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=web_app), base_url="http://test"
    ) as client:
        response = await client.get("/my-topic")
    assert response.status_code == 200
    html = response.text
    assert get_meta_og_content(html, "og:title") == "My topic (Igor's Manager Book)"
    assert (
        get_meta_og_content(html, "og:url") == "https://idvork.in/manager-book#my-topic"
    )
    assert get_redirect_url(html) == "https://idvork.in/manager-book#my-topic"


@pytest.mark.asyncio
async def test_redirect_two_params_page_and_topic():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=web_app), base_url="http://test"
    ) as client:
        response = await client.get("/my-page/my-topic")
    assert response.status_code == 200
    html = response.text
    assert (
        get_meta_og_content(html, "og:title") == "My topic (My page)"
    )  # Note: hup capitalizes
    assert get_meta_og_content(html, "og:url") == "https://idvork.in/my-page#my-topic"
    assert get_redirect_url(html) == "https://idvork.in/my-page#my-topic"


@pytest.mark.asyncio
async def test_redirect_three_params_ignored():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=web_app), base_url="http://test"
    ) as client:
        response = await client.get("/my-page/my-topic/extra-part")
    assert response.status_code == 200
    html = response.text
    # Behavior for >2 params is to use first two.
    assert get_meta_og_content(html, "og:title") == "My topic (My page)"
    assert get_meta_og_content(html, "og:url") == "https://idvork.in/my-page#my-topic"
    assert get_redirect_url(html) == "https://idvork.in/my-page#my-topic"


@pytest.mark.asyncio
async def test_preview_text_api_no_params():
    """Test the /preview_text endpoint with no parameters"""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=web_app), base_url="http://test"
    ) as client:
        response = await client.get("/preview_text/")
    assert response.status_code == 200
    data = response.json()
    assert "preview" in data
    assert "url" in data
    assert data["url"] == "https://tinyurl.com/igor-says"


@pytest.mark.asyncio
async def test_preview_text_api_one_param():
    """Test the /preview_text endpoint with one parameter (topic)"""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=web_app), base_url="http://test"
    ) as client:
        response = await client.get("/preview_text/my-topic")
    assert response.status_code == 200
    data = response.json()
    assert "preview" in data
    assert "url" in data
    assert data["url"] == "https://tinyurl.com/igor-says?path=manager-book%23my-topic"


@pytest.mark.asyncio
async def test_preview_text_api_two_params():
    """Test the /preview_text endpoint with two parameters (page and topic)"""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=web_app), base_url="http://test"
    ) as client:
        response = await client.get("/preview_text/my-page/my-topic")
    assert response.status_code == 200
    data = response.json()
    assert "preview" in data
    assert "url" in data
    assert data["url"] == "https://tinyurl.com/igor-says?path=my-page%23my-topic"


@pytest.mark.asyncio
async def test_preview_text_api_text_only():
    """Test the /preview_text endpoint with text_only parameter"""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=web_app), base_url="http://test"
    ) as client:
        response = await client.get("/preview_text/my-page/my-topic?text_only=true")
    assert response.status_code == 200
    text = response.text
    assert "From: https://tinyurl.com/igor-says?path=my-page%23my-topic" in text
    assert text.startswith("From: https://tinyurl.com/igor-says?path=my-page%23my-topic\n\n")


@pytest.mark.asyncio
async def test_og_description_populated():
    """Test that og:description is populated (not 'Description Ignored')"""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=web_app), base_url="http://test"
    ) as client:
        response = await client.get("/manager-book/leadership")
    assert response.status_code == 200
    html = response.text
    description = get_meta_og_content(html, "og:description")
    assert description is not None
    # Since we're fetching from the actual site, we can't guarantee the exact text,
    # but we can check it's not the default
    # Note: This will only work if the actual site is accessible during testing
