"""
Fetches a URL, extracts the relevant text (whole page or a CSS selector),
and hashes it so we can detect changes cheaply without storing every
version of every page forever.
"""

from __future__ import annotations

import hashlib
import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from watchtower.config import settings


@dataclass
class CheckResult:
    success: bool
    extracted_text: str = ""
    content_hash: str = ""
    error: str | None = None


class UnsafeTargetError(Exception):
    """Raised when a watch URL resolves to a private/internal address."""


def _assert_public_host(url: str) -> None:
    """
    Block SSRF: refuse to fetch URLs whose host resolves to a private,
    loopback, or link-local address. Without this, a user could point a
    watch at http://169.254.169.254 or http://localhost:internal-service
    and use this server to probe your own infrastructure.
    """
    hostname = urlparse(url).hostname
    if hostname is None:
        raise UnsafeTargetError("URL has no hostname")
    try:
        resolved_ips = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        raise UnsafeTargetError(f"Could not resolve host: {hostname}") from e

    for family, _, _, _, sockaddr in resolved_ips:
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise UnsafeTargetError(f"Refusing to fetch internal/private address: {ip}")


def _extract_text(html: str, css_selector: str | None) -> str:
    soup = BeautifulSoup(html, "html.parser")
    if css_selector:
        elements = soup.select(css_selector)
        if not elements:
            raise ValueError(f"CSS selector matched nothing: {css_selector}")
        text = "\n".join(el.get_text(strip=True) for el in elements)
    else:
        text = soup.get_text(separator="\n", strip=True)
    return text


async def check_url(url: str, css_selector: str | None) -> CheckResult:
    """Fetch the URL and return the extracted text + hash, or an error."""
    try:
        _assert_public_host(url)
    except UnsafeTargetError as e:
        return CheckResult(success=False, error=str(e))

    try:
        async with httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": "Watchtower/0.1 (+https://github.com)"},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as e:
        return CheckResult(success=False, error=f"Request failed: {e}")

    try:
        text = _extract_text(response.text, css_selector)
    except ValueError as e:
        return CheckResult(success=False, error=str(e))

    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return CheckResult(success=True, extracted_text=text, content_hash=content_hash)
