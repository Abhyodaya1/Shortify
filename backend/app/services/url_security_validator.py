"""Deep Multi-Layer URL & SSRF Security Validator for Shortify.
Validates scheme, hostname whitelisting, video ID syntax, and resolves DNS to block
private IP ranges, loopback addresses, and cloud metadata endpoints.
"""

from __future__ import annotations
import ipaddress
import re
import socket
from typing import Set, Tuple
from urllib.parse import urlparse, parse_qs


class SSRFSecurityError(ValueError):
    """Raised when a URL violates SSRF or security boundaries."""
    pass


class URLSecurityValidator:
    """Multi-layer validator for ingested video URLs."""

    ALLOWED_SCHEMES: Set[str] = {"http", "https"}
    ALLOWED_HOSTS: Set[str] = {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
    }
    VIDEO_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{11}$")

    # Private and reserved network blocks to block
    DISALLOWED_NETWORKS = [
        ipaddress.ip_network("0.0.0.0/8"),          # Current network (local identification)
        ipaddress.ip_network("10.0.0.0/8"),         # RFC 1918 Private class A
        ipaddress.ip_network("100.64.0.0/10"),      # Shared Address Space (CGNAT)
        ipaddress.ip_network("127.0.0.0/8"),        # Loopback
        ipaddress.ip_network("169.254.0.0/16"),     # Link-Local / Cloud Metadata (169.254.169.254)
        ipaddress.ip_network("172.16.0.0/12"),      # RFC 1918 Private class B
        ipaddress.ip_network("192.0.0.0/24"),       # IETF Protocol Assignments
        ipaddress.ip_network("192.0.2.0/24"),       # Documentation (TEST-NET-1)
        ipaddress.ip_network("192.168.0.0/16"),     # RFC 1918 Private class C
        ipaddress.ip_network("198.18.0.0/15"),      # Benchmark testing
        ipaddress.ip_network("198.51.100.0/24"),    # Documentation (TEST-NET-2)
        ipaddress.ip_network("203.0.113.0/24"),     # Documentation (TEST-NET-3)
        ipaddress.ip_network("224.0.0.0/4"),        # Multicast
        ipaddress.ip_network("240.0.0.0/4"),        # Reserved (former class E)
        ipaddress.ip_network("255.255.255.255/32"), # Limited broadcast
        # IPv6 blocks
        ipaddress.ip_network("::1/128"),            # Loopback
        ipaddress.ip_network("::/128"),             # Unspecified
        ipaddress.ip_network("fc00::/7"),           # Unique Local Address (ULA)
        ipaddress.ip_network("fe80::/10"),          # Link-local unicast
        ipaddress.ip_network("ff00::/8"),           # Multicast
        ipaddress.ip_network("2001:db8::/32"),      # Documentation
    ]

    @classmethod
    def extract_youtube_video_id(cls, url: str) -> str:
        """Extracts and syntactically validates an 11-character YouTube video ID."""
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()

        video_id: str = ""
        if hostname == "youtu.be":
            # Path is /<video_id>
            video_id = parsed.path.strip("/").split("/")[0] if parsed.path.strip("/") else ""
        elif hostname in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
            if parsed.path == "/watch":
                qs = parse_qs(parsed.query)
                v_list = qs.get("v")
                if v_list:
                    video_id = v_list[0]
            elif parsed.path.startswith("/shorts/"):
                video_id = parsed.path.split("/shorts/")[1].split("/")[0]
            elif parsed.path.startswith("/embed/"):
                video_id = parsed.path.split("/embed/")[1].split("/")[0]

        if not video_id or not cls.VIDEO_ID_PATTERN.match(video_id):
            raise ValueError(f"Invalid or missing YouTube video ID in URL: {url}")

        return video_id

    @classmethod
    def _is_ip_disallowed(cls, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        """Checks if an IP falls into private, loopback, or reserved address spaces."""
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return True

        # Check explicit network ranges
        for net in cls.DISALLOWED_NETWORKS:
            if ip in net:
                return True

        # Check IPv4-mapped IPv6 addresses (e.g. ::ffff:127.0.0.1)
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            return cls._is_ip_disallowed(ip.ipv4_mapped)

        return False

    @classmethod
    def validate_url(cls, url: str) -> Tuple[str, str]:
        """Validates a YouTube URL across all 4 security layers.

        Returns:
            Tuple[str, str]: (sanitized_url, video_id)
        Raises:
            SSRFSecurityError: If URL fails security or SSRF checks.
            ValueError: If scheme or video ID format is invalid.
        """
        if not url or not isinstance(url, str):
            raise SSRFSecurityError("URL cannot be empty.")

        url_clean = url.strip()

        # Layer 1: Protocol & Scheme Validation
        parsed = urlparse(url_clean)
        scheme = (parsed.scheme or "").lower()
        if scheme not in cls.ALLOWED_SCHEMES:
            raise SSRFSecurityError(
                f"Unsupported URL scheme '{scheme}'. Only HTTP and HTTPS protocols are permitted."
            )

        # Layer 2: Domain Whitelist Validation
        hostname = (parsed.hostname or "").lower()
        if not hostname or hostname not in cls.ALLOWED_HOSTS:
            raise SSRFSecurityError(
                f"Unauthorized video host '{hostname}'. Only official YouTube domains are permitted."
            )

        # Extract & validate video ID syntax
        video_id = cls.extract_youtube_video_id(url_clean)

        # Layer 3: DNS Pre-Resolution & Private IP Pinning
        try:
            # Resolve DNS records for hostname
            addr_info = socket.getaddrinfo(hostname, 443, proto=socket.IPPROTO_TCP)
        except socket.gaierror as e:
            raise SSRFSecurityError(f"DNS resolution failed for host '{hostname}': {e}")

        if not addr_info:
            raise SSRFSecurityError(f"No IP addresses resolved for host '{hostname}'.")

        for entry in addr_info:
            sockaddr = entry[4]
            ip_str = sockaddr[0]
            try:
                ip_obj = ipaddress.ip_address(ip_str)
            except ValueError:
                raise SSRFSecurityError(f"Invalid resolved IP address: {ip_str}")

            if cls._is_ip_disallowed(ip_obj):
                raise SSRFSecurityError(
                    f"Security violation: Host '{hostname}' resolved to blocked private or reserved IP address: {ip_str}"
                )

        return url_clean, video_id

