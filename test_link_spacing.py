#!/usr/bin/env python3
"""Test that links are properly spaced when extracted for og:description"""

from modal_redirect import get_preview_text_from_url
from unittest.mock import patch, Mock
from bs4 import BeautifulSoup


def test_link_spacing_in_preview_text():
    """Test that links have proper spacing when extracted"""
    
    # Mock HTML with links that need spacing
    mock_html = """
    <html>
    <body>
        <article>
            <p>This is some text<a href="/link">with a link</a>that needs spacing.</p>
            <p>Another paragraph with<a href="/another">multiple</a>links<a href="/third">here</a>too.</p>
        </article>
    </body>
    </html>
    """
    
    # Mock the requests.get to return our test HTML
    with patch('modal_redirect.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Call the function
        result = get_preview_text_from_url("https://idvork.in/test", max_chars=200)
        
        # Check that links have proper spacing
        assert "text with a link that" in result
        assert "with multiple links here too" in result
        
        # Make sure there are spaces around the link text
        assert "textwith a linkthat" not in result
        assert "withmultiplelinksheretoo" not in result


def test_link_spacing_with_anchor():
    """Test that links have proper spacing when extracting from anchor section"""
    
    # Mock HTML with an anchor section containing links
    mock_html = """
    <html>
    <body>
        <h2 id="test-section">Test Section</h2>
        <p>Content before<a href="/link">the link</a>and after.</p>
        <p>More content with<a href="/another">another link</a>here.</p>
    </body>
    </html>
    """
    
    # Mock the requests.get to return our test HTML
    with patch('modal_redirect.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Call the function with an anchor
        result = get_preview_text_from_url("https://idvork.in/test", anchor="test-section", max_chars=200)
        
        # Check that links have proper spacing
        assert "before the link and" in result
        assert "with another link here" in result
        
        # Make sure there are no concatenated words
        assert "beforethe linkand" not in result
        assert "withanother linkhere" not in result


def test_beautifulsoup_separator():
    """Direct test of BeautifulSoup's get_text with separator"""
    
    html = '<p>Text before<a href="#">link text</a>text after</p>'
    soup = BeautifulSoup(html, 'html.parser')
    
    # Without separator (default behavior - concatenates)
    text_no_separator = soup.get_text(strip=True)
    assert text_no_separator == "Text beforelink texttext after"
    
    # With separator (adds spaces between elements)
    text_with_separator = soup.get_text(separator=" ", strip=True)
    assert text_with_separator == "Text before link text text after"


if __name__ == "__main__":
    test_link_spacing_in_preview_text()
    test_link_spacing_with_anchor()
    test_beautifulsoup_separator()
    print("All tests passed!")