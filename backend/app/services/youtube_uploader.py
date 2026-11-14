"""YouTube Resumable Video Uploader
Uploads 9:16 Shorts directly to YouTube using YouTube Data API v3 Resumable Protocol.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx
from .youtube_oauth_service import YouTubeOAuthService

UPLOAD_INIT_URL = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"


class YouTubeUploader:
    """Handles direct upload of video files to YouTube using Data API v3."""

    @classmethod
    def resolve_video_file(cls, video_path: str, clip_id: Optional[str] = None) -> Path:
        """Resolves video_path (which can be a local file path, URL, filename, or clip_id)
        to an actual local Path on disk."""
        # 1. Direct local file check
        if video_path:
            try:
                p = Path(video_path)
                if p.exists() and p.is_file():
                    return p.resolve()
            except Exception:
                pass

        candidate_names: List[str] = []
        if video_path:
            clean_str = video_path.split("?")[0].split("#")[0]
            fname = clean_str.rstrip("/").split("/")[-1].split("\\")[-1]
            if fname:
                candidate_names.append(fname)
            if fname.startswith("short_") and fname.endswith(".mp4"):
                extracted_id = fname[len("short_"):-len(".mp4")]
                candidate_names.append(f"clip_{extracted_id}")
                candidate_names.append(extracted_id)

        if clip_id:
            clean_cid = str(clip_id).strip()
            candidate_names.append(f"short_{clean_cid}.mp4")
            candidate_names.append(f"{clean_cid}.mp4")
            candidate_names.append(clean_cid)
            if clean_cid.startswith("clip_"):
                raw_id = clean_cid[len("clip_"):]
                candidate_names.append(f"short_{raw_id}.mp4")
                candidate_names.append(raw_id)
            else:
                candidate_names.append(f"clip_{clean_cid}")

        search_dirs = [
            Path("backend/storage/renders"),
            Path("storage/renders"),
            Path("backend/storage/clips"),
            Path("storage/clips"),
            Path.cwd() / "backend" / "storage" / "renders",
            Path.cwd() / "storage" / "renders",
            Path.cwd() / "backend" / "storage" / "clips",
            Path.cwd() / "storage" / "clips",
        ]

        for sdir in search_dirs:
            if not sdir.exists():
                continue
            for name in candidate_names:
                # Direct file in render directory
                f_path = sdir / name
                if f_path.exists() and f_path.is_file():
                    return f_path.resolve()

                if not name.endswith(".mp4"):
                    f_mp4 = sdir / f"{name}.mp4"
                    if f_mp4.exists() and f_mp4.is_file():
                        return f_mp4.resolve()

                # Inside subfolder: clip_{id}/final.mp4 or clip_{id}/composed_raw.mp4
                folder_name = name if name.startswith("clip_") else f"clip_{name.replace('short_', '').replace('.mp4', '')}"
                sub_final = sdir / folder_name / "final.mp4"
                if sub_final.exists() and sub_final.is_file():
                    return sub_final.resolve()

                sub_composed = sdir / folder_name / "composed_raw.mp4"
                if sub_composed.exists() and sub_composed.is_file():
                    return sub_composed.resolve()

        # Glob search across storage directory if still not found
        for sdir in search_dirs:
            if not sdir.exists():
                continue
            for name in candidate_names:
                pure_token = name.replace("short_", "").replace("clip_", "").replace(".mp4", "")
                if len(pure_token) >= 4:
                    matches = list(sdir.glob(f"*{pure_token}*.mp4"))
                    if matches:
                        return matches[0].resolve()

        # If it's a remote URL (not localhost), download to temporary file
        if video_path and (video_path.startswith("http://") or video_path.startswith("https://")):
            if not ("localhost" in video_path or "127.0.0.1" in video_path):
                dl_dir = Path("backend/storage/renders/downloads")
                dl_dir.mkdir(parents=True, exist_ok=True)
                clean_target = Path(video_path.split("?")[0].split("#")[0]).name
                target_path = dl_dir / f"download_{clean_target}"
                with httpx.Client(timeout=60.0) as client:
                    resp = client.get(video_path)
                    if resp.status_code == 200:
                        target_path.write_bytes(resp.content)
                        return target_path.resolve()

        raise FileNotFoundError(
            f"Video file could not be resolved from: '{video_path}' (clip_id='{clip_id}'). "
            f"Please verify that the Short has been rendered and exists in backend/storage/renders/."
        )

    @classmethod
    async def upload_video(
        cls,
        refresh_token: str,
        video_path: str,
        title: str,
        description: str,
        tags: List[str],
        privacy_status: str = "unlisted",
        publish_at: Optional[str] = None,
        clip_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Uploads a video to YouTube using the resumable upload protocol."""
        file_path = cls.resolve_video_file(video_path, clip_id=clip_id)
        if not file_path.exists():
            raise FileNotFoundError(f"Video file not found at: {file_path}")

        file_size = file_path.stat().st_size
        if file_size == 0:
            raise ValueError("Video file is empty (0 bytes)")

        # 1. Obtain a fresh access token using the stored refresh token
        access_token = await YouTubeOAuthService.refresh_access_token(refresh_token)

        # 2. Prepare metadata
        # Ensure #Shorts is present in title or description so YouTube flags it as a Short
        clean_title = title if "#Shorts" in title else f"{title} #Shorts"
        snippet = {
            "title": clean_title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "22", # People & Blogs
        }

        status: Dict[str, Any] = {
            "privacyStatus": privacy_status.lower(),
            "selfDeclaredMadeForKids": False,
        }
        if publish_at and privacy_status.lower() == "private":
            status["publishAt"] = publish_at

        metadata_body = {
            "snippet": snippet,
            "status": status,
        }

        # 3. Initialize the resumable upload session
        init_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(file_size),
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            init_resp = await client.post(UPLOAD_INIT_URL, json=metadata_body, headers=init_headers)
            if init_resp.status_code != 200:
                raise RuntimeError(f"YouTube upload initialization failed ({init_resp.status_code}): {init_resp.text}")

            upload_url = init_resp.headers.get("Location")
            if not upload_url:
                raise RuntimeError("YouTube did not return a resumable upload location header.")

        # 4. Stream upload the video binary bytes
        with open(file_path, "rb") as f:
            video_bytes = f.read()

        upload_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "video/mp4",
            "Content-Length": str(file_size),
            "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
        }

        # Use longer timeout for uploading full video
        async with httpx.AsyncClient(timeout=300.0) as client:
            upload_resp = await client.put(upload_url, content=video_bytes, headers=upload_headers)
            if upload_resp.status_code not in (200, 201):
                raise RuntimeError(f"YouTube video bytes upload failed ({upload_resp.status_code}): {upload_resp.text}")

            result = upload_resp.json()
            video_id = result.get("id")
            youtube_url = f"https://youtube.com/shorts/{video_id}"

            return {
                "status": "success",
                "youtube_video_id": video_id,
                "youtube_url": youtube_url,
                "raw_response": result,
            }

