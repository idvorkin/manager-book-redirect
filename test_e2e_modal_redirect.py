import httpx
import pytest
from bs4 import BeautifulSoup

# The deployed Modal URL
DEPLOYED_URL = "https://idvorkin--igor-blog-fastapi-app.modal.run"


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
async def test_e2e_redirect_no_params():
    """Test the deployed service with no parameters"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(f"{DEPLOYED_URL}/")

    assert response.status_code == 200
    html = response.text
    assert get_meta_og_content(html, "og:title") == "Igor's book of management"
    assert get_meta_og_content(html, "og:url") == "https://idvork.in/manager-book#"
    assert get_redirect_url(html) == "https://idvork.in/manager-book#"


@pytest.mark.asyncio
async def test_e2e_redirect_favicon():
    """Test the deployed service with favicon request"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{DEPLOYED_URL}/favicon.ico")

    assert response.status_code == 200
    html = response.text
    assert get_meta_og_content(html, "og:title") == "Igor's book of management"
    assert get_meta_og_content(html, "og:url") == "https://idvork.in/manager-book#"
    assert get_redirect_url(html) == "https://idvork.in/manager-book#"


@pytest.mark.asyncio
async def test_e2e_redirect_one_param_topic():
    """Test the deployed service with one parameter (topic)"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{DEPLOYED_URL}/my-topic")

    assert response.status_code == 200
    html = response.text
    assert get_meta_og_content(html, "og:title") == "My topic (Igor's Manager Book)"
    assert (
        get_meta_og_content(html, "og:url") == "https://idvork.in/manager-book#my-topic"
    )
    assert get_redirect_url(html) == "https://idvork.in/manager-book#my-topic"


@pytest.mark.asyncio
async def test_e2e_redirect_two_params_page_and_topic():
    """Test the deployed service with two parameters (page and topic)"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{DEPLOYED_URL}/my-page/my-topic")

    assert response.status_code == 200
    html = response.text
    assert get_meta_og_content(html, "og:title") == "My topic (My page)"
    assert get_meta_og_content(html, "og:url") == "https://idvork.in/my-page#my-topic"
    assert get_redirect_url(html) == "https://idvork.in/my-page#my-topic"


@pytest.mark.asyncio
async def test_e2e_redirect_three_params_ignored():
    """Test the deployed service with three parameters (extra should be ignored)"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{DEPLOYED_URL}/my-page/my-topic/extra-part")

    assert response.status_code == 200
    html = response.text
    # Behavior for >2 params is to use first two.
    assert get_meta_og_content(html, "og:title") == "My topic (My page)"
    assert get_meta_og_content(html, "og:url") == "https://idvork.in/my-page#my-topic"
    assert get_redirect_url(html) == "https://idvork.in/my-page#my-topic"


@pytest.mark.asyncio
async def test_e2e_health_check():
    """Basic health check to ensure the service is responding"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{DEPLOYED_URL}/health-check")

    # Should return 200 even if it's a redirect page
    assert response.status_code == 200
    # Should contain some HTML content
    assert len(response.text) > 0
    assert "<html" in response.text.lower()


@pytest.mark.asyncio
async def test_e2e_preview_text_api_no_params():
    """Test the deployed /preview_text endpoint with no parameters"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{DEPLOYED_URL}/preview_text/")
    
    assert response.status_code == 200
    data = response.json()
    assert "preview" in data
    assert "url" in data
    assert data["url"] == "https://tinyurl.com/igor-says"


@pytest.mark.asyncio
async def test_e2e_preview_text_api_one_param():
    """Test the deployed /preview_text endpoint with one parameter"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{DEPLOYED_URL}/preview_text/my-topic")
    
    assert response.status_code == 200
    data = response.json()
    assert "preview" in data
    assert "url" in data
    assert data["url"] == "https://tinyurl.com/igor-says?path=manager-book%23my-topic"


@pytest.mark.asyncio
async def test_e2e_preview_text_api_two_params():
    """Test the deployed /preview_text endpoint with two parameters"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{DEPLOYED_URL}/preview_text/my-page/my-topic")
    
    assert response.status_code == 200
    data = response.json()
    assert "preview" in data
    assert "url" in data
    assert data["url"] == "https://tinyurl.com/igor-says?path=my-page%23my-topic"


@pytest.mark.asyncio
async def test_e2e_og_description_has_preview():
    """Test that og:description contains actual preview text (not default)"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{DEPLOYED_URL}/manager-book/one-on-ones")
    
    assert response.status_code == 200
    html = response.text
    description = get_meta_og_content(html, "og:description")
    
    # Should have a description
    assert description is not None
    # Should not be the default placeholder
    assert description != "Description Ignored"
    # Should have some meaningful content
    assert len(description) > 20
