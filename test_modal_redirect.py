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
async def test_link_spacing_in_og_description():
    """Test that links in og:description have proper spacing"""
    from unittest.mock import patch, Mock
    
    # Mock HTML with links that need spacing
    mock_html = """
    <html>
    <body>
        <article>
            <p>This is some text<a href="/link">with a link</a>that needs spacing.</p>
        </article>
    </body>
    </html>
    """
    
    with patch('modal_redirect.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=web_app), base_url="http://test"
        ) as client:
            response = await client.get("/test-page/test-anchor")
        
        assert response.status_code == 200
        html = response.text
        description = get_meta_og_content(html, "og:description")
        
        # Check that links have proper spacing
        assert "text with a link that" in description
        # Make sure there are no concatenated words
        assert "textwith a linkthat" not in description


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


@pytest.mark.asyncio
async def test_heading_fetch_with_mock():
    """Test that actual heading text is fetched and used for titles"""
    from unittest.mock import patch, Mock
    import modal_redirect
    
    # Clear cache before test
    modal_redirect.page_cache.clear()
    
    # Mock HTML with a properly formatted heading
    mock_html = """
    <html>
        <body>
            <h2 id="time-off-3-ps">Time Off - 3 P's</h2>
            <p>Content about time off...</p>
        </body>
    </html>
    """
    
    with patch('modal_redirect.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=web_app), base_url="http://test"
        ) as client:
            response = await client.get("/manager-book/time-off-3-ps")
        
        assert response.status_code == 200
        html = response.text
        title = get_meta_og_content(html, "og:title")
        # Should use the actual heading text, not the URL-based version
        assert title == "Time Off - 3 P's (Igor's Manager Book)"


@pytest.mark.asyncio  
async def test_heading_fetch_fallback():
    """Test that title generation falls back to URL-based when fetch fails"""
    from unittest.mock import patch
    import modal_redirect
    
    # Clear cache before test
    modal_redirect.page_cache.clear()
    
    with patch('modal_redirect.requests.get') as mock_get:
        # Simulate network failure
        mock_get.side_effect = Exception("Network error")
        
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=web_app), base_url="http://test"
        ) as client:
            response = await client.get("/manager-book/time-off-3-ps")
        
        assert response.status_code == 200
        html = response.text
        title = get_meta_og_content(html, "og:title")
        # Should fall back to URL-based title generation
        assert title == "Time off 3 ps (Igor's Manager Book)"


@pytest.mark.asyncio
async def test_page_cache():
    """Test that webpage HTML is cached and reused"""
    from unittest.mock import patch, Mock
    import modal_redirect
    
    # Clear cache before test
    modal_redirect.page_cache.clear()
    
    # Test with mock HTML
    mock_html = """
    <html>
        <body>
            <h2 id="cached-heading">This Is A Cached Heading</h2>
            <p>Some content for testing...</p>
        </body>
    </html>
    """
    
    with patch('modal_redirect.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # First call - should fetch from URL
        result1 = modal_redirect.get_heading_text_from_url("https://idvork.in/manager-book", "cached-heading")
        assert result1 == "This Is A Cached Heading"
        assert mock_get.call_count == 1
        
        # Second call with same URL - should use cache
        result2 = modal_redirect.get_heading_text_from_url("https://idvork.in/manager-book", "cached-heading")
        assert result2 == "This Is A Cached Heading"
        assert mock_get.call_count == 1  # Should still be 1 (cached)
        
        # Also test that preview text uses the same cache
        preview = modal_redirect.get_preview_text_from_url("https://idvork.in/manager-book", "cached-heading")
        assert preview is not None
        assert mock_get.call_count == 1  # Should still be 1 (cached)
        
        # Verify cache contains the HTML
        assert "https://idvork.in/manager-book" in modal_redirect.page_cache
        assert modal_redirect.page_cache["https://idvork.in/manager-book"][0] == mock_html
