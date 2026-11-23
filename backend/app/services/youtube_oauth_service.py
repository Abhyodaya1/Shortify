"""YouTube OAuth Service
Handles Google OAuth 2.0 authorization, code exchange, token refresh, and channel profile retrieval.
"""

from __future__ import annotations
import os
from pathlib import Path
import urllib.parse
from dotenv import load_dotenv
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Ensure environment variables are loaded
load_dotenv(Path(__file__).resolve().parents[3] / ".env")
load_dotenv()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
YOUTUBE_CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/userinfo.profile",
]


class YouTubeTokenExpiredError(RuntimeError):
    """Raised when a Google OAuth refresh_token is expired or revoked (invalid_grant)."""
    pass


class YouTubeOAuthService:
    """Manages real YouTube OAuth2 authorization and channel info retrieval."""

    @classmethod
    def get_client_credentials(cls) -> Dict[str, str]:
        client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
        redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/v1/youtube/callback").strip()
        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        }

    @classmethod
    def is_configured(cls) -> bool:
        creds = cls.get_client_credentials()
        return bool(creds["client_id"] and creds["client_secret"])

    @classmethod
    def get_authorization_url(cls, state: str = "default_user") -> str:
        """Generates the Google OAuth 2.0 consent URL."""
        creds = cls.get_client_credentials()
        if not creds["client_id"]:
            raise ValueError("GOOGLE_CLIENT_ID is not configured in .env")

        params = {
            "client_id": creds["client_id"],
            "redirect_uri": creds["redirect_uri"],
            "response_type": "code",
            "scope": " ".join(YOUTUBE_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
        }
        return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

    @classmethod
    async def exchange_code_for_tokens(cls, code: str) -> Dict[str, Any]:
        """Exchanges authorization code for access_token and refresh_token."""
        creds = cls.get_client_credentials()
        data = {
            "code": code,
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "redirect_uri": creds["redirect_uri"],
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(GOOGLE_TOKEN_URL, data=data)
            if resp.status_code != 200:
                raise RuntimeError(f"Google token exchange failed ({resp.status_code}): {resp.text}")
            return resp.json()

    @classmethod
    async def refresh_access_token(cls, refresh_token: str) -> str:
        """Obtains a fresh access_token using a refresh_token."""
        creds = cls.get_client_credentials()
        data = {
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(GOOGLE_TOKEN_URL, data=data)
            if resp.status_code != 200:
                resp_text = resp.text
                if "invalid_grant" in resp_text:
                    raise YouTubeTokenExpiredError(
                        "Google OAuth token has expired or was revoked. Please reconnect your YouTube channel."
                    )
                raise RuntimeError(f"Token refresh failed ({resp.status_code}): {resp_text}")
            payload = resp.json()
            return payload["access_token"]

    @classmethod
    async def fetch_channel_profile(cls, access_token: str) -> Dict[str, Any]:
        """Fetches the user's primary YouTube channel metadata."""
        params = {
            "part": "snippet,statistics",
            "mine": "true",
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(YOUTUBE_CHANNELS_URL, params=params, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to fetch YouTube channel ({resp.status_code}): {resp.text}")
            data = resp.json()
            items = data.get("items", [])
            if not items:
                raise RuntimeError("No YouTube channel found for this Google account. Please create a channel on YouTube first.")
            item = items[0]
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            return {
                "channel_id": item.get("id"),
                "channel_title": snippet.get("title", "My Channel"),
                "custom_url": snippet.get("customUrl", f"@{snippet.get('title', 'channel')}"),
                "thumbnail_url": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                "subscriber_count": int(stats.get("subscriberCount", 0)),
                "video_count": int(stats.get("videoCount", 0)),
                "is_sandbox": 0,
            }

    @classmethod
    async def fetch_channel_videos(cls, access_token: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Fetches the user's real YouTube channel uploaded videos via YouTube Data API v3."""
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            # 1. Get uploads playlist ID
            chan_resp = await client.get(
                YOUTUBE_CHANNELS_URL,
                params={"part": "contentDetails", "mine": "true"},
                headers=headers,
            )
            if chan_resp.status_code != 200:
                return []
            chan_data = chan_resp.json()
            items = chan_data.get("items", [])
            if not items:
                return []
            uploads_playlist_id = items[0].get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
            if not uploads_playlist_id:
                return []

            # 2. Get playlist items (real uploaded videos)
            pl_resp = await client.get(
                "https://www.googleapis.com/youtube/v3/playlistItems",
                params={
                    "part": "snippet,contentDetails",
                    "playlistId": uploads_playlist_id,
                    "maxResults": max_results,
                },
                headers=headers,
            )
            if pl_resp.status_code != 200:
                return []
            pl_data = pl_resp.json()
            videos = []
            for item in pl_data.get("items", []):
                snippet = item.get("snippet", {})
                vid_id = item.get("contentDetails", {}).get("videoId")
                if not vid_id:
                    continue
                thumbs = snippet.get("thumbnails", {})
                thumb_url = (
                    thumbs.get("high", {}).get("url")
                    or thumbs.get("medium", {}).get("url")
                    or thumbs.get("default", {}).get("url")
                    or f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                )
                pub_date = snippet.get("publishedAt", "")[:10]
                videos.append({
                    "id": vid_id,
                    "title": snippet.get("title", "YouTube Video"),
                    "youtube_url": f"https://www.youtube.com/watch?v={vid_id}",
                    "duration_min": "10:00",
                    "views": "Live",
                    "published_date": pub_date,
                    "thumbnail": thumb_url,
                })
            return videos

