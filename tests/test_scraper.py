import pytest

from watchtower.scraper import UnsafeTargetError, _assert_public_host, _extract_text


def test_extract_text_whole_page():
    html = "<html><body><h1>Title</h1><p>Body text</p></body></html>"
    text = _extract_text(html, css_selector=None)
    assert "Title" in text
    assert "Body text" in text


def test_extract_text_with_selector():
    html = '<div class="price">$19.99</div><div class="other">ignore me</div>'
    text = _extract_text(html, css_selector=".price")
    assert text == "$19.99"


def test_extract_text_selector_matches_nothing_raises():
    html = "<div>hello</div>"
    with pytest.raises(ValueError):
        _extract_text(html, css_selector=".does-not-exist")


def test_localhost_is_blocked():
    with pytest.raises(UnsafeTargetError):
        _assert_public_host("http://localhost:8000/admin")


def test_loopback_ip_is_blocked():
    with pytest.raises(UnsafeTargetError):
        _assert_public_host("http://127.0.0.1/secret")


def test_private_network_is_blocked():
    with pytest.raises(UnsafeTargetError):
        _assert_public_host("http://192.168.1.1/router-admin")


def test_link_local_metadata_endpoint_is_blocked():
    # This is the classic cloud-metadata SSRF target (AWS/GCP/Azure).
    with pytest.raises(UnsafeTargetError):
        _assert_public_host("http://169.254.169.254/latest/meta-data/")
