"""Master Timeline Compositor & YouTube Packaging Engine.
Orchestrates Phase 1 MVP end-to-end:
- Acoustic word alignment (WordAligner)
- Editorial hook & headline strategy (EditorialOrchestrator)
- Neural Voiceover synthesis & Loudness normalization (TTSManager)
- Cinematic kinetic subtitles & QA verification (KineticSubtitleCompiler, SubtitleQAService)
- Content packaging & YouTube metadata generation (ContentPackagerService / Role 06)
- FFmpeg multi-stream composition, rendering, and export validation
"""

from __future__ import annotations
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx
from dotenv import load_dotenv

from .word_aligner import WordAligner
from .editorial_orchestrator import EditorialOrchestrator
from .tts_engine import TTSManager
from .kinetic_subtitle_compiler import KineticSubtitleCompiler, SubtitleQAService
from .card_overlay_generator import CardOverlayGenerator
from ..models.editorial_profile import EditorialProfile
from ..storage.profile_store import ProfileStore

load_dotenv()

PROMPT_PACK_DIR = Path("shorts_ai_roles_prompt_pack")
STORAGE_RENDERS = Path("backend/storage/renders")
STORAGE_RENDERS.mkdir(parents=True, exist_ok=True)


class ContentPackagerService:
    """Executes Role 06 (Content Packager) from shorts_ai_roles_prompt_pack."""

    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL_FAST = os.getenv("GROQ_MODEL_FAST", "qwen/qwen3.8-27b")

    @classmethod
    def package_content(
        cls,
        clip_id: str,
        transcript: str,
        central_idea: str,
        opening_hook: str = "",
        ending_hook: str = "",
        key_terms: Optional[List[str]] = None,
        channel_name: str = "Creator Studio",
        channel_niche: str = "Creator Education & Video Production",
        target_audience: str = "Mobile short-form video viewers",
        brand_voice: str = "Direct, engaging, authentic",
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runs Role 06 Content Packager to produce titles, description, tags, and hashtags."""
        sys_prompt = (PROMPT_PACK_DIR / "06_content_packager" / "system.md").read_text(encoding="utf-8")
        user_template = (PROMPT_PACK_DIR / "06_content_packager" / "user.md").read_text(encoding="utf-8")

        data = {
            "clip_id": clip_id,
            "channel_name": channel_name,
            "channel_niche": channel_niche,
            "target_audience": target_audience,
            "language": "en",
            "brand_voice": brand_voice,
            "transcript": transcript,
            "central_idea": central_idea,
            "opening_hook": opening_hook,
            "ending_hook": ending_hook,
            "key_terms": ", ".join(key_terms or ["video tips", "creator", "shorts growth"]),
        }

        user_prompt = user_template
        for k, v in data.items():
            user_prompt = user_prompt.replace(f"{{{{{k}}}}}", str(v))

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            package = {
                "clip_id": clip_id,
                "titles": [
                    {"text": f"Why This Mistake Kills Your Views", "angle": "curiosity-driven", "accuracy_note": "Direct from transcript"},
                    {"text": f"Stop Doing This When Editing", "angle": "actionable", "accuracy_note": "Direct advice"},
                    {"text": f"The Creator Secret Nobody Explains", "angle": "insider-truth", "accuracy_note": "Accurate takeaway"},
                ],
                "recommended_title_index": 0,
                "description": f"Master this essential strategy to immediately improve your video retention and engagement.\n\n#shorts #creator #editing",
                "tags": ["shorts", "creator tips", "video editing", "retention"],
                "hashtags": ["#shorts", "#creator", "#viralvideo"],
                "metadata_warnings": [],
                "rationale": "High-clarity, non-clickbait titles grounded strictly in the clip's thesis.",
            }
        else:
            payload = {
                "model": cls.MODEL_FAST,
                "messages": [
                    {"role": "system", "content": sys_prompt + "\nOutput strictly valid JSON only."},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "max_tokens": 2048,
                "temperature": 0.3,
            }
            headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}

            try:
                with httpx.Client(timeout=25.0) as client:
                    resp = client.post(cls.GROQ_API_URL, json=payload, headers=headers)
                if resp.status_code == 200:
                    package = resp.json()["choices"][0]["message"]["content"]
                    if isinstance(package, str):
                        package = json.loads(package)
                else:
                    package = {
                        "clip_id": clip_id,
                        "titles": [{"text": "Essential Creator Strategy", "angle": "direct"}],
                        "recommended_title_index": 0,
                        "description": "Essential takeaway from the video.",
                        "tags": ["shorts", "creators"],
                        "hashtags": ["#shorts"],
                    }
            except Exception as e:
                package = {
                    "clip_id": clip_id,
                    "titles": [{"text": "Essential Creator Strategy", "angle": "direct"}],
                    "recommended_title_index": 0,
                    "description": "Essential takeaway from the video.",
                    "tags": ["shorts"],
                    "hashtags": ["#shorts"],
                    "error": str(e),
                }

        if output_dir:
            out_p = Path(output_dir) / "packaging_metadata.json"
            out_p.parent.mkdir(parents=True, exist_ok=True)
            with open(out_p, "w", encoding="utf-8") as f:
                json.dump(package, f, indent=2)

        return package


class MasterTimelineCompositor:
    """End-to-End Orchestrator for Phase 1 MVP."""

    @classmethod
    async def process_and_render_clip(
        cls,
        source_video_path: str,
        start_sec: float,
        end_sec: float,
        clip_id: str,
        output_dir: Optional[str] = None,
        crop_data: Optional[Dict[str, Any]] = None,
        # Layout & Framing options (Feature 2)
        layout_mode: str = "full_9_16", # "full_9_16", "split_screen", "split_screen_comment", "tweet_card", "fit_ambient_blur"
        card_type: Optional[str] = None, # "none", "reddit_card", "tweet_card", "instagram_card", "youtube_comment"
        background_video_path: Optional[str] = None,
        video_scale_percent: int = 48,
        # Social Card & Comment Card Overlay options (Feature 2)
        social_author: Optional[str] = "Motion Creator",
        social_handle: Optional[str] = "@motioncreator",
        social_badge: Optional[str] = "verified",
        social_text: Optional[str] = None,
        # Hook & Audio options
        enable_opening_hook: bool = False,
        opening_hook_text: Optional[str] = None,
        enable_ending_hook: bool = False,
        ending_hook_text: Optional[str] = None,
        headline_text: Optional[str] = None,
        tts_voice: str = "en-US-ChristopherNeural",
        # Subtitle styling options
        subtitle_preset: str = "mrbeast",
        custom_active_color: Optional[str] = None,
        custom_primary_color: Optional[str] = None,
        custom_font_name: Optional[str] = None,
        custom_animation: Optional[str] = None,
        custom_all_caps: Optional[bool] = None,
        custom_outline_width: Optional[float] = None,
        # Card & Subtitle positioning options
        card_vertical_position: Optional[int] = 20,
        card_width_percent: Optional[int] = 90,
        subtitle_vertical_position: Optional[int] = 75,
        # Target export resolution
        target_width: int = 1080,
        target_height: int = 1920,
        use_single_pass: bool = False,
    ) -> Dict[str, Any]:
        """Runs the entire modular pipeline and renders broadcast-quality final.mp4 with all artifacts."""
        out_dir = Path(output_dir) if output_dir else STORAGE_RENDERS / clip_id
        out_dir.mkdir(parents=True, exist_ok=True)

        clip_duration = max(1.0, end_sec - start_sec)
        src_path = Path(source_video_path).resolve()

        # =========================================================================
        # 1. Step 1: Acoustic Word Alignment (WordAligner)
        # =========================================================================
        alignment_data = WordAligner.align_clip(
            source_media_path=str(src_path),
            start_sec=start_sec,
            end_sec=end_sec,
            output_dir=str(out_dir),
            clip_id=clip_id,
        )
        clip_words = alignment_data.get("words", [])
        if isinstance(alignment_data.get("transcript"), dict):
            reference_transcript = alignment_data["transcript"].get("full_text", "")
        else:
            reference_transcript = alignment_data.get("full_text") or str(alignment_data.get("transcript", ""))

        # =========================================================================
        # 2. Step 2: Contextual Hook Generation (Roles 01-04)
        # =========================================================================
        hooks_data = None
        hooks_file = out_dir / "hooks.json"

        if not opening_hook_text or not headline_text:
            hooks_data = EditorialOrchestrator.run_pipeline(
                clip_id=clip_id,
                transcript_data={"full_text": reference_transcript},
                duration_seconds=clip_duration,
                output_dir=str(out_dir),
            )
            rec = hooks_data.get("recommended_selection", {})
            if not opening_hook_text:
                opening_hook_text = rec.get("opening_hook", "")
            if not headline_text:
                headline_text = rec.get("headline", "")
            if not ending_hook_text:
                ending_hook_text = rec.get("ending_hook", "")
        else:
            # Persist explicit choices
            hooks_data = {
                "clip_id": clip_id,
                "recommended_selection": {
                    "opening_hook": opening_hook_text,
                    "headline": headline_text,
                    "ending_hook": ending_hook_text or "",
                }
            }
            with open(hooks_file, "w", encoding="utf-8") as f:
                json.dump(hooks_data, f, indent=2)

        # =========================================================================
        # 3. Step 3: Neural Voice Synthesis & Loudness Normalization (Role 07)
        # =========================================================================
        opening_audio_path = None
        opening_audio_dur = 0.0
        opening_hook_words = []

        if enable_opening_hook and opening_hook_text and opening_hook_text.strip():
            tts_res = await TTSManager.generate_voiceover_hook(
                clip_id=clip_id,
                hook_text=opening_hook_text,
                segment_type="opening",
                output_dir=str(out_dir),
                voice_id=tts_voice,
                transcript=reference_transcript,
            )
            if tts_res.get("success"):
                opening_audio_path = tts_res["audio_file"]
                opening_audio_dur = tts_res["actual_duration_seconds"]

                # Generate simple word-timing span for the opening hook voiceover
                hook_words_raw = opening_hook_text.split()
                if hook_words_raw and opening_audio_dur > 0:
                    w_span = opening_audio_dur / len(hook_words_raw)
                    for idx, w in enumerate(hook_words_raw):
                        opening_hook_words.append({
                            "word": w,
                            "start": round(idx * w_span, 2),
                            "end": round((idx + 1) * w_span, 2),
                        })

        ending_audio_path = None
        ending_audio_dur = 0.0
        if enable_ending_hook and ending_hook_text and ending_hook_text.strip():
            tts_res = await TTSManager.generate_voiceover_hook(
                clip_id=clip_id,
                hook_text=ending_hook_text,
                segment_type="ending",
                output_dir=str(out_dir),
                voice_id=tts_voice,
                transcript=reference_transcript,
            )
            if tts_res.get("success"):
                ending_audio_path = tts_res["audio_file"]
                ending_audio_dur = tts_res["actual_duration_seconds"]

        # =========================================================================
        # 4. Step 4: Kinetic Subtitles & Subtitle QA (Role 05)
        # =========================================================================
        # Combine timeline words: opening hook words + original clip words offset by opening_audio_dur
        combined_words = []
        if opening_hook_words:
            combined_words.extend(opening_hook_words)

        for w in clip_words:
            combined_words.append({
                "word": w.get("word", ""),
                "start": round(w.get("start", 0.0) + opening_audio_dur, 3),
                "end": round(w.get("end", 0.0) + opening_audio_dur, 3),
            })

        # Resolve card requirement cleanly & independently
        eff_card_type = (card_type or "").lower().strip()
        if not eff_card_type:
            if layout_mode in ["reddit_card", "tweet_card", "twitter_card", "instagram_card", "youtube_comment", "split_screen_comment"]:
                eff_card_type = layout_mode
            else:
                eff_card_type = "none"

        has_card = eff_card_type not in ["none", "pure_video", "disabled", "no", ""]
        is_reddit = has_card and (eff_card_type == "reddit_card")
        is_instagram = has_card and (eff_card_type == "instagram_card")
        is_youtube = has_card and (eff_card_type in ["youtube_comment", "youtube_card", "split_screen_comment"])
        is_tweet = has_card and (eff_card_type in ["tweet_card", "twitter_card", "quote_card"] or (not is_reddit and not is_instagram and not is_youtube))

        ass_path = out_dir / "subtitles.ass"
        KineticSubtitleCompiler.compile_ass(
            words=combined_words,
            output_path=str(ass_path),
            headline_text=headline_text,
            preset_name=subtitle_preset,
            custom_active_color=custom_active_color,
            custom_primary_color=custom_primary_color,
            custom_font_name=custom_font_name,
            custom_animation=custom_animation,
            custom_all_caps=custom_all_caps,
            custom_outline_width=custom_outline_width,
            time_offset_sec=0.0, # Already offset in combined_words
            video_width=target_width,
            video_height=target_height,
            subtitle_vertical_position=subtitle_vertical_position,
            suppress_headline=has_card,
        )

        qa_report = SubtitleQAService.audit_subtitles(
            clip_id=clip_id,
            reference_transcript=reference_transcript,
            subtitles_words=clip_words,
            output_dir=str(out_dir),
        )

        # =========================================================================
        # 5. Content Packaging (Role 06)
        # =========================================================================
        central_idea = (
            hooks_data.get("transcript_analysis", {}).get("central_topic")
            or "High-impact creator video insights"
        ) if hooks_data else "High-impact creator video insights"

        packaging = ContentPackagerService.package_content(
            clip_id=clip_id,
            transcript=reference_transcript,
            central_idea=central_idea,
            opening_hook=opening_hook_text or "",
            ending_hook=ending_hook_text or "",
            output_dir=str(out_dir),
        )

        # =========================================================================
        # 6. Step 5: Multi-Stream Master Composition & Video Render (FFmpeg)
        # =========================================================================
        final_mp4_path = out_dir / "final.mp4"
        composed_raw_path = out_dir / "composed_raw.mp4"

        # Resolve speaker crop parameters & smooth camera pan expression
        crop_info = crop_data or {}
        src_w = crop_info.get("source_width", 1920)
        src_h = crop_info.get("source_height", 1080)
        crop_w = crop_info.get("crop_width", int(src_h * 9 / 16))
        crop_h = crop_info.get("crop_height", src_h)
        crop_x = crop_info.get("optimal_crop_x", (src_w - crop_w) // 2)
        crop_expr = crop_info.get("crop_expr", str(crop_x))
        has_motion = crop_info.get("has_motion", False)

        encoder = cls._detect_encoder()

        # Step 6A: Render main clip with layout composition (split_screen, fit_ambient_blur, or full_9_16)
        main_clip_raw = out_dir / "main_clip_raw.mp4"

        # Background video resolution for split screen or ambient canvas (defaulting to Minecraft)
        bg_video = background_video_path
        if not bg_video or not Path(bg_video).exists():
            default_bg = Path("backend/storage/backgrounds/minecraft_parkour.mp4")
            if default_bg.exists():
                bg_video = str(default_bg.resolve())

        card_overlay_path = None
        c_w, c_h = 0, 0
        card_y = int(target_height * (card_vertical_position / 100.0)) if card_vertical_position else 220

        if has_card:
            card_w = int(target_width * (card_width_percent / 100.0)) if card_width_percent else 940

            # Discard dummy preset placeholder texts and ensure transcript virality hook is used
            dummy_social_texts = [
                "what happens when ai changes",
                "most people are thinking about this",
                "the #1 secret",
                "if you produce 10 shorts daily",
                "what formula do you use",
                "every creator gets asked",
                "every soldier gets asked",
                "code and media are permissionless",
            ]
            is_dummy = False
            if social_text:
                st_lower = social_text.lower()
                is_dummy = any(d in st_lower for d in dummy_social_texts)

            if social_text and not is_dummy:
                c_text = social_text
            else:
                c_text = opening_hook_text or headline_text or reference_transcript[:140]

            if is_reddit:
                card_overlay_path = out_dir / "reddit_card.png"
                CardOverlayGenerator.generate_reddit_hook_card(
                    subreddit=social_author if "r/" in (social_author or "") else f"r/{social_author or 'technology'}",
                    author_name=social_handle or "u/example",
                    question_text=c_text,
                    output_path=str(card_overlay_path),
                    card_width=card_w,
                )
            elif is_instagram:
                card_overlay_path = out_dir / "instagram_card.png"
                CardOverlayGenerator.generate_instagram_card(
                    author_name=social_author or "creator_hub",
                    handle=social_handle or "@creator_hub",
                    hook_text=c_text,
                    output_path=str(card_overlay_path),
                    card_width=card_w,
                )
            elif is_youtube:
                card_overlay_path = out_dir / "comment_card.png"
                CardOverlayGenerator.generate_comment_card(
                    author_name=social_author or "Creator Fan",
                    badge_text=social_badge or "CA$ 14.99 SUPERCHAT",
                    comment_text=c_text,
                    output_path=str(card_overlay_path),
                    card_width=card_w,
                )
            else: # is_tweet
                card_overlay_path = out_dir / "tweet_card.png"
                CardOverlayGenerator.generate_tweet_card(
                    author_name=social_author or "Legacy of the Brave",
                    handle=social_handle or "@LegacyoftheBrave",
                    tweet_text=c_text,
                    output_path=str(card_overlay_path),
                    canvas_width=target_width,
                    card_width=card_w,
                )

            if card_overlay_path and card_overlay_path.exists():
                from PIL import Image as PILImage
                with PILImage.open(str(card_overlay_path)) as c_img:
                    c_w, c_h = c_img.size

        # Rendering Step: Support single-pass filter_complex or legacy multi-pass
        should_use_single_pass = use_single_pass or os.getenv("SHORTIFY_RENDERER") == "single_pass"

        single_pass_success = False
        if should_use_single_pass and not (opening_audio_path or ending_audio_path):
            try:
                cls._render_single_pass_filter_complex(
                    src_path=src_path,
                    start_sec=start_sec,
                    end_sec=end_sec,
                    clip_duration=clip_duration,
                    layout_mode=layout_mode,
                    bg_video=bg_video,
                    card_overlay_path=card_overlay_path,
                    card_y=card_y,
                    c_w=c_w,
                    c_h=c_h,
                    video_scale_percent=video_scale_percent,
                    target_width=target_width,
                    target_height=target_height,
                    crop_info=crop_info,
                    ass_path=ass_path,
                    final_mp4_path=final_mp4_path,
                    encoder=encoder,
                    has_card=has_card,
                )
                if final_mp4_path.exists() and cls._measure_duration(str(final_mp4_path)) > 0:
                    single_pass_success = True
            except Exception as e:
                print(f"[Renderer] Single-pass render failed ({e}), falling back to legacy multi-pass...")
                if final_mp4_path.exists():
                    try:
                        final_mp4_path.unlink()
                    except Exception:
                        pass

        if not single_pass_success:
            cls._render_legacy_multipass(
                src_path=src_path,
                start_sec=start_sec,
                end_sec=end_sec,
                clip_duration=clip_duration,
                layout_mode=layout_mode,
                bg_video=bg_video,
                card_overlay_path=card_overlay_path,
                card_y=card_y,
                c_w=c_w,
                c_h=c_h,
                video_scale_percent=video_scale_percent,
                target_width=target_width,
                target_height=target_height,
                crop_info=crop_info,
                ass_path=ass_path,
                final_mp4_path=final_mp4_path,
                composed_raw_path=composed_raw_path,
                main_clip_raw=main_clip_raw,
                out_dir=out_dir,
                encoder=encoder,
                opening_audio_path=opening_audio_path,
                opening_audio_dur=opening_audio_dur,
                ending_audio_path=ending_audio_path,
                ending_audio_dur=ending_audio_dur,
                has_card=has_card,
            )

        final_dur = cls._measure_duration(str(final_mp4_path))
        total_expected_dur = round(clip_duration + opening_audio_dur + ending_audio_dur, 2)

        # Step 6D: Generate comprehensive render_report.json
        report = {
            "clip_id": clip_id,
            "status": "success" if final_mp4_path.exists() and final_dur > 0 else "failed",
            "source_media": str(src_path),
            "start_sec": start_sec,
            "end_sec": end_sec,
            "clip_duration_sec": clip_duration,
            "total_duration_sec": final_dur,
            "expected_duration_sec": total_expected_dur,
            "video_format": {
                "resolution": f"{target_width}x{target_height}",
                "aspect_ratio": "9:16",
                "codec": "h264",
                "audio_codec": "aac",
            },
            "hooks": {
                "opening_hook_enabled": bool(opening_audio_path),
                "opening_hook_text": opening_hook_text,
                "opening_hook_duration_sec": opening_audio_dur,
                "headline_text": headline_text,
                "ending_hook_enabled": bool(ending_audio_path),
                "ending_hook_text": ending_hook_text,
            },
            "subtitles": {
                "preset": subtitle_preset,
                "word_count": len(combined_words),
                "qa_status": qa_report.get("status", "pass"),
                "qa_issues": qa_report.get("issues", []),
            },
            "packaging": packaging,
            "output_files": {
                "final_video": str(final_mp4_path.resolve()),
                "transcript": str((out_dir / "transcript.json").resolve()),
                "word_alignment": str((out_dir / "word_alignment.json").resolve()),
                "hooks": str((out_dir / "hooks.json").resolve()),
                "opening_voice": str(Path(opening_audio_path).resolve()) if opening_audio_path else None,
                "subtitles_ass": str(ass_path.resolve()),
                "subtitle_qa_report": str((out_dir / "subtitle_qa_report.json").resolve()),
                "packaging_metadata": str((out_dir / "packaging_metadata.json").resolve()),
                "render_report": str((out_dir / "render_report.json").resolve()),
            }
        }

        with open(out_dir / "render_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return report

    @classmethod
    def re_render_subtitles_fast(
        cls,
        clip_dir: str,
        subtitle_preset: str = "mrbeast",
        custom_active_color: Optional[str] = None,
        custom_font_name: Optional[str] = None,
        headline_text: Optional[str] = None,
        video_width: int = 1080,
        video_height: int = 1920,
    ) -> Dict[str, Any]:
        """2-second fast re-rendering: Re-burns ASS subtitles onto composed_raw.mp4 without re-running source analysis."""
        c_dir = Path(clip_dir)
        composed_raw = c_dir / "composed_raw.mp4"
        final_mp4 = c_dir / "final.mp4"
        word_align_file = c_dir / "word_alignment.json"

        if not composed_raw.exists() or not word_align_file.exists():
            return {"success": False, "error": "Clip artifacts not found"}

        with open(word_align_file, "r", encoding="utf-8") as f:
            align_data = json.load(f)

        words = align_data if isinstance(align_data, list) else align_data.get("words", [])

        # Check for opening hook duration to keep timing synchronized with composed_raw.mp4
        time_offset = 0.0
        opening_hook_words = []
        report_file = c_dir / "render_report.json"
        if report_file.exists():
            try:
                with open(report_file, "r", encoding="utf-8") as rf:
                    rep = json.load(rf)
                time_offset = float(rep.get("hooks", {}).get("opening_hook_duration_sec", 0.0))
                hook_txt = rep.get("hooks", {}).get("opening_hook_text", "")
                if not headline_text:
                    headline_text = rep.get("hooks", {}).get("headline_text")
                if time_offset > 0 and hook_txt:
                    h_words = hook_txt.split()
                    w_span = time_offset / len(h_words)
                    for idx, w in enumerate(h_words):
                        opening_hook_words.append({
                            "word": w,
                            "start": round(idx * w_span, 2),
                            "end": round((idx + 1) * w_span, 2),
                        })
            except Exception:
                pass

        combined_words = []
        if opening_hook_words:
            combined_words.extend(opening_hook_words)
        for w in words:
            combined_words.append({
                "word": w.get("word", ""),
                "start": round(w.get("start", 0.0) + time_offset, 3),
                "end": round(w.get("end", 0.0) + time_offset, 3),
            })

        ass_path = c_dir / "subtitles.ass"

        KineticSubtitleCompiler.compile_ass(
            words=combined_words,
            output_path=str(ass_path),
            headline_text=headline_text,
            preset_name=subtitle_preset,
            custom_active_color=custom_active_color,
            custom_font_name=custom_font_name,
            time_offset_sec=0.0,
            video_width=video_width,
            video_height=video_height,
        )

        encoder = cls._detect_encoder()
        escaped_ass = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")

        cmd = [
            "ffmpeg", "-y",
            "-i", str(composed_raw.resolve()),
            "-vf", f"subtitles='{escaped_ass}'",
            "-c:v", encoder,
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            "-movflags", "+faststart",
            str(final_mp4.resolve()),
        ]
        res = cls._safe_run_ffmpeg(cmd, timeout=180)
        if res.returncode != 0:
            cmd[cmd.index("-c:v") + 1] = "libx264"
            cls._safe_run_ffmpeg(cmd, timeout=180)

        return {
            "success": True,
            "final_video": str(final_mp4.resolve()),
            "subtitles_ass": str(ass_path.resolve()),
            "preset": subtitle_preset,
        }

    @classmethod
    def _render_legacy_multipass(
        cls,
        src_path: Path,
        start_sec: float,
        end_sec: float,
        clip_duration: float,
        layout_mode: str,
        bg_video: Optional[str],
        card_overlay_path: Optional[Path],
        card_y: int,
        c_w: int,
        c_h: int,
        video_scale_percent: int,
        target_width: int,
        target_height: int,
        crop_info: Dict[str, Any],
        ass_path: Path,
        final_mp4_path: Path,
        composed_raw_path: Path,
        main_clip_raw: Path,
        out_dir: Path,
        encoder: str,
        opening_audio_path: Optional[str],
        opening_audio_dur: float,
        ending_audio_path: Optional[str],
        ending_audio_dur: float,
        has_card: bool,
    ) -> None:
        """Executes the battle-tested multi-pass compositing pipeline (production default)."""
        src_w = crop_info.get("source_width", 1920)
        src_h = crop_info.get("source_height", 1080)
        crop_w = crop_info.get("crop_width", int(src_h * 9 / 16))
        crop_h = crop_info.get("crop_height", src_h)
        crop_x = crop_info.get("optimal_crop_x", (src_w - crop_w) // 2)
        crop_expr = crop_info.get("crop_expr", str(crop_x))
        has_motion = crop_info.get("has_motion", False)

# Render Main Video Stream based on Layout Mode & Overlay
        is_split = layout_mode in ["split_screen", "split_screen_comment", "split_50_50", "split_60_40", "stacked"] and bg_video and Path(bg_video).exists()
        is_ambient = layout_mode in ["fit_ambient_blur", "blurred_bg", "floating", "card", "card_frame", "blurred"]

        if is_split:
            scale_pct = max(30, min(80, video_scale_percent))
            top_h = int(target_height * (scale_pct / 100))
            if top_h % 2 != 0:
                top_h += 1
            bot_h = target_height - top_h

            top_aspect = target_width / top_h
            if src_w / max(1, src_h) > top_aspect:
                spk_cw = int(src_h * top_aspect)
                spk_ch = src_h
                offset_x = (crop_w - spk_cw) // 2
                if has_motion and crop_expr != str(crop_x):
                    spk_cx = f"max(0,min({src_w - spk_cw},{crop_expr}+{offset_x}))"
                else:
                    spk_cx = str(max(0, min(src_w - spk_cw, crop_x + offset_x)))
                spk_cy = 0
            else:
                spk_cw = src_w
                spk_ch = int(src_w / top_aspect)
                spk_cx = "0"
                spk_cy = (src_h - spk_ch) // 2

            spk_cw = (spk_cw // 2) * 2
            spk_ch = (spk_ch // 2) * 2

            if has_card and card_overlay_path and card_overlay_path.exists():
                split_filter = (
                    f"[0:v]crop=w={spk_cw}:h={spk_ch}:x='{spk_cx}':y={spk_cy},scale={target_width}:{top_h}[top]; "
                    rf"[1:v]crop=w=min(iw\,ih*{target_width}/{bot_h}):h=min(ih\,iw*{bot_h}/{target_width}):x=(iw-ow)/2:y=(ih-oh)/2,scale={target_width}:{bot_h}[bot]; "
                    f"[top][bot]vstack=inputs=2[stacked]; "
                    f"[2:v]scale={c_w}:{c_h}[card]; "
                    f"[stacked][card]overlay=(W-w)/2:{card_y}[v]"
                )
                main_cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{start_sec:.3f}",
                    "-i", str(src_path),
                    "-stream_loop", "-1",
                    "-i", str(Path(bg_video).resolve()),
                    "-i", str(card_overlay_path.resolve()),
                    "-filter_complex", split_filter,
                    "-map", "[v]",
                    "-map", "0:a:0",
                    "-t", f"{clip_duration:.3f}",
                    "-shortest",
                    "-r", "30",
                    "-c:v", encoder,
                    "-preset", "fast",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "48000",
                    "-ac", "2",
                    str(main_clip_raw.resolve()),
                ]
            else:
                split_filter = (
                    f"[0:v]crop=w={spk_cw}:h={spk_ch}:x='{spk_cx}':y={spk_cy},scale={target_width}:{top_h}[top]; "
                    rf"[1:v]crop=w=min(iw\,ih*{target_width}/{bot_h}):h=min(ih\,iw*{bot_h}/{target_width}):x=(iw-ow)/2:y=(ih-oh)/2,scale={target_width}:{bot_h}[bot]; "
                    f"[top][bot]vstack=inputs=2[v]"
                )
                main_cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{start_sec:.3f}",
                    "-i", str(src_path),
                    "-stream_loop", "-1",
                    "-i", str(Path(bg_video).resolve()),
                    "-filter_complex", split_filter,
                    "-map", "[v]",
                    "-map", "0:a:0",
                    "-t", f"{clip_duration:.3f}",
                    "-shortest",
                    "-r", "30",
                    "-c:v", encoder,
                    "-preset", "fast",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "48000",
                    "-ac", "2",
                    str(main_clip_raw.resolve()),
                ]
        elif is_ambient:
            card_w = int(target_width * 0.92)
            card_h = int(card_w * (src_h / max(1, src_w)))
            if card_h % 2 != 0:
                card_h += 1
            vid_y = int((target_height * 0.70 - card_h) / 2 + target_height * 0.12)

            # High retention backdrop: use Minecraft or gameplay video blurred as backdrop by default
            has_gameplay_bg = bool(bg_video and Path(bg_video).exists())

            if has_gameplay_bg:
                if has_card and card_overlay_path and card_overlay_path.exists():
                    ambient_filter = (
                        f"[1:v]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,crop={target_width}:{target_height},boxblur=25:5,eq=brightness=-0.15:contrast=1.05[bg]; "
                        f"[0:v]scale={card_w}:{card_h}[fg]; "
                        f"[2:v]scale={c_w}:{c_h}[card]; "
                        f"[bg][fg]overlay=(W-w)/2:{vid_y}[base]; "
                        f"[base][card]overlay=(W-w)/2:{card_y}[v]"
                    )
                    main_cmd = [
                        "ffmpeg", "-y",
                        "-ss", f"{start_sec:.3f}",
                        "-i", str(src_path),
                        "-stream_loop", "-1",
                        "-i", str(Path(bg_video).resolve()),
                        "-i", str(card_overlay_path.resolve()),
                        "-t", f"{clip_duration:.3f}",
                        "-filter_complex", ambient_filter,
                        "-map", "[v]",
                        "-map", "0:a:0",
                        "-r", "30",
                        "-c:v", encoder,
                        "-preset", "fast",
                        "-pix_fmt", "yuv420p",
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-ar", "48000",
                        "-ac", "2",
                        str(main_clip_raw.resolve()),
                    ]
                else:
                    ambient_filter = (
                        f"[1:v]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,crop={target_width}:{target_height},boxblur=25:5,eq=brightness=-0.15:contrast=1.05[bg]; "
                        f"[0:v]scale={card_w}:{card_h}[fg]; "
                        f"[bg][fg]overlay=(W-w)/2:{vid_y}[v]"
                    )
                    main_cmd = [
                        "ffmpeg", "-y",
                        "-ss", f"{start_sec:.3f}",
                        "-i", str(src_path),
                        "-stream_loop", "-1",
                        "-i", str(Path(bg_video).resolve()),
                        "-t", f"{clip_duration:.3f}",
                        "-filter_complex", ambient_filter,
                        "-map", "[v]",
                        "-map", "0:a:0",
                        "-r", "30",
                        "-c:v", encoder,
                        "-preset", "fast",
                        "-pix_fmt", "yuv420p",
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-ar", "48000",
                        "-ac", "2",
                        str(main_clip_raw.resolve()),
                    ]
            else:
                if has_card and card_overlay_path and card_overlay_path.exists():
                    ambient_filter = (
                        f"[0:v]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,crop={target_width}:{target_height},boxblur=25:5,eq=brightness=-0.15:contrast=1.05[bg]; "
                        f"[0:v]scale={card_w}:{card_h}[fg]; "
                        f"[1:v]scale={c_w}:{c_h}[card]; "
                        f"[bg][fg]overlay=(W-w)/2:{vid_y}[base]; "
                        f"[base][card]overlay=(W-w)/2:{card_y}[v]"
                    )
                    main_cmd = [
                        "ffmpeg", "-y",
                        "-ss", f"{start_sec:.3f}",
                        "-i", str(src_path),
                        "-i", str(card_overlay_path.resolve()),
                        "-t", f"{clip_duration:.3f}",
                        "-filter_complex", ambient_filter,
                        "-map", "[v]",
                        "-map", "0:a:0",
                        "-r", "30",
                        "-c:v", encoder,
                        "-preset", "fast",
                        "-pix_fmt", "yuv420p",
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-ar", "48000",
                        "-ac", "2",
                        str(main_clip_raw.resolve()),
                    ]
                else:
                    ambient_filter = (
                        f"[0:v]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,crop={target_width}:{target_height},boxblur=25:5,eq=brightness=-0.15:contrast=1.05[bg]; "
                        f"[0:v]scale={card_w}:{card_h}[fg]; "
                        f"[bg][fg]overlay=(W-w)/2:{vid_y}[v]"
                    )
                    main_cmd = [
                        "ffmpeg", "-y",
                        "-ss", f"{start_sec:.3f}",
                        "-i", str(src_path),
                        "-t", f"{clip_duration:.3f}",
                        "-filter_complex", ambient_filter,
                        "-map", "[v]",
                        "-map", "0:a:0",
                        "-r", "30",
                        "-c:v", encoder,
                        "-preset", "fast",
                        "-pix_fmt", "yuv420p",
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-ar", "48000",
                        "-ac", "2",
                        str(main_clip_raw.resolve()),
                    ]
        else:
            # Full 9:16 speaker framing (with optional social card overlay)
            full_crop_x = f"'{crop_expr}'" if (has_motion and crop_expr != str(crop_x)) else str(crop_x)

            if has_card and card_overlay_path and card_overlay_path.exists():
                full_card_filter = (
                    f"[0:v]crop=w={crop_w}:h={crop_h}:x={full_crop_x}:y=0,scale={target_width}:{target_height}[vid]; "
                    f"[1:v]scale={c_w}:{c_h}[card]; "
                    f"[vid][card]overlay=(W-w)/2:{card_y}[v]"
                )
                main_cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{start_sec:.3f}",
                    "-i", str(src_path),
                    "-i", str(card_overlay_path.resolve()),
                    "-t", f"{clip_duration:.3f}",
                    "-filter_complex", full_card_filter,
                    "-map", "[v]",
                    "-map", "0:a:0",
                    "-r", "30",
                    "-c:v", encoder,
                    "-preset", "fast",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "48000",
                    "-ac", "2",
                    str(main_clip_raw.resolve()),
                ]
            else:
                main_cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{start_sec:.3f}",
                    "-i", str(src_path),
                    "-t", f"{clip_duration:.3f}",
                    "-vf", f"crop=w={crop_w}:h={crop_h}:x={full_crop_x}:y=0,scale={target_width}:{target_height}",
                    "-r", "30",
                    "-c:v", encoder,
                    "-preset", "fast",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "48000",
                    "-ac", "2",
                    str(main_clip_raw.resolve()),
                ]

        res_main = cls._safe_run_ffmpeg(main_cmd, timeout=180)
        if res_main.returncode != 0:
            main_cmd[main_cmd.index("-c:v") + 1] = "libx264"
            cls._safe_run_ffmpeg(main_cmd, timeout=180)

        # Step 6B: If opening voiceover exists, render cinematic intro card with neural voice mapped to audio
        has_intro = bool(opening_audio_path and opening_audio_dur > 0 and Path(opening_audio_path).exists())
        has_outro = bool(ending_audio_path and ending_audio_dur > 0 and Path(ending_audio_path).exists())

        if has_intro or has_outro:
            inputs = []
            filter_segments = []
            segment_idx = 0

            # 1. Opening Voiceover Intro Card
            if has_intro:
                intro_card_mp4 = out_dir / "intro_card.mp4"
                intro_cmd = [
                    "ffmpeg", "-y",
                    "-stream_loop", "-1",
                    "-i", str(main_clip_raw.resolve()),
                    "-i", str(Path(opening_audio_path).resolve()),
                    "-t", f"{opening_audio_dur:.3f}",
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-vf", "boxblur=15:5,eq=brightness=-0.15:contrast=1.1",
                    "-r", "30",
                    "-c:v", encoder,
                    "-preset", "fast",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "48000",
                    "-ac", "2",
                    "-shortest",
                    str(intro_card_mp4.resolve()),
                ]
                res_intro = cls._safe_run_ffmpeg(intro_cmd, timeout=180)
                if res_intro.returncode != 0:
                    intro_cmd[intro_cmd.index("-c:v") + 1] = "libx264"
                    cls._safe_run_ffmpeg(intro_cmd, timeout=180)

                inputs.extend(["-i", str(intro_card_mp4.resolve())])
                filter_segments.append(f"[{segment_idx}:v][{segment_idx}:a]")
                segment_idx += 1

            # 2. Main Spoken Video Clip
            inputs.extend(["-i", str(main_clip_raw.resolve())])
            filter_segments.append(f"[{segment_idx}:v][{segment_idx}:a]")
            segment_idx += 1

            # 3. Optional Ending Voiceover Outro Card
            if has_outro:
                outro_card_mp4 = out_dir / "outro_card.mp4"
                outro_cmd = [
                    "ffmpeg", "-y",
                    "-sseof", "-1",
                    "-i", str(main_clip_raw.resolve()),
                    "-i", str(Path(ending_audio_path).resolve()),
                    "-t", f"{ending_audio_dur:.3f}",
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-vf", "boxblur=15:5,eq=brightness=-0.15:contrast=1.1",
                    "-r", "30",
                    "-c:v", encoder,
                    "-preset", "fast",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "48000",
                    "-ac", "2",
                    "-shortest",
                    str(outro_card_mp4.resolve()),
                ]
                res_outro = cls._safe_run_ffmpeg(outro_cmd, timeout=180)
                if res_outro.returncode != 0:
                    outro_cmd[outro_cmd.index("-c:v") + 1] = "libx264"
                    cls._safe_run_ffmpeg(outro_cmd, timeout=180)

                inputs.extend(["-i", str(outro_card_mp4.resolve())])
                filter_segments.append(f"[{segment_idx}:v][{segment_idx}:a]")
                segment_idx += 1

            # Concatenate all parts via filter_complex for seamless sample-accurate audio & video
            concat_filter = f"{''.join(filter_segments)}concat=n={segment_idx}:v=1:a=1[v][a]"
            concat_cmd = [
                "ffmpeg", "-y",
                *inputs,
                "-filter_complex", concat_filter,
                "-map", "[v]",
                "-map", "[a]",
                "-c:v", encoder,
                "-preset", "fast",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "48000",
                "-ac", "2",
                str(composed_raw_path.resolve()),
            ]
            res_concat = cls._safe_run_ffmpeg(concat_cmd, timeout=180)
            if res_concat.returncode != 0:
                concat_cmd[concat_cmd.index("-c:v") + 1] = "libx264"
                cls._safe_run_ffmpeg(concat_cmd, timeout=180)
        else:
            # No opening or ending voiceover: main clip is the composed raw
            if main_clip_raw.exists():
                if composed_raw_path.exists():
                    composed_raw_path.unlink()
                main_clip_raw.rename(composed_raw_path)

        # Step 6C: Burn kinetic subtitles onto composed video (2-second blazing fast pass)
        escaped_ass = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
        burn_cmd = [
            "ffmpeg", "-y",
            "-i", str(composed_raw_path.resolve()),
            "-vf", f"subtitles='{escaped_ass}'",
            "-c:v", encoder,
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            "-movflags", "+faststart",
            str(final_mp4_path.resolve()),
        ]
        res_burn = cls._safe_run_ffmpeg(burn_cmd, timeout=180)
        if res_burn.returncode != 0:
            burn_cmd[burn_cmd.index("-c:v") + 1] = "libx264"
            cls._safe_run_ffmpeg(burn_cmd, timeout=180)

        # Verify export integrity

    @classmethod
    def _render_single_pass_filter_complex(
        cls,
        src_path: Path,
        start_sec: float,
        end_sec: float,
        clip_duration: float,
        layout_mode: str,
        bg_video: Optional[str],
        card_overlay_path: Optional[Path],
        card_y: int,
        c_w: int,
        c_h: int,
        video_scale_percent: int,
        target_width: int,
        target_height: int,
        crop_info: Dict[str, Any],
        ass_path: Path,
        final_mp4_path: Path,
        encoder: str,
        has_card: bool,
    ) -> None:
        """Executes a unified single-pass filter_complex pipeline combining layout, overlay, and subtitles directly to final.mp4."""
        escaped_ass = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")

        src_w = crop_info.get("source_width", 1920)
        src_h = crop_info.get("source_height", 1080)
        crop_w = crop_info.get("crop_width", int(src_h * 9 / 16))
        crop_h = crop_info.get("crop_height", src_h)
        crop_x = crop_info.get("optimal_crop_x", (src_w - crop_w) // 2)
        crop_expr = crop_info.get("crop_expr", str(crop_x))
        has_motion = crop_info.get("has_motion", False)

        is_split = layout_mode in ["split_screen", "split_screen_comment", "split_50_50", "split_60_40", "stacked"] and bg_video and Path(bg_video).exists()
        is_ambient = layout_mode in ["fit_ambient_blur", "blurred_bg", "floating", "card", "card_frame", "blurred"]

        if is_split:
            scale_pct = max(30, min(80, video_scale_percent))
            top_h = int(target_height * (scale_pct / 100))
            if top_h % 2 != 0:
                top_h += 1
            bot_h = target_height - top_h

            top_aspect = target_width / top_h
            if src_w / max(1, src_h) > top_aspect:
                spk_cw = int(src_h * top_aspect)
                spk_ch = src_h
                offset_x = (crop_w - spk_cw) // 2
                if has_motion and crop_expr != str(crop_x):
                    spk_cx = f"max(0,min({src_w - spk_cw},{crop_expr}+{offset_x}))"
                else:
                    spk_cx = str(max(0, min(src_w - spk_cw, crop_x + offset_x)))
                spk_cy = 0
            else:
                spk_cw = src_w
                spk_ch = int(src_w / top_aspect)
                spk_cx = "0"
                spk_cy = (src_h - spk_ch) // 2

            spk_cw = (spk_cw // 2) * 2
            spk_ch = (spk_ch // 2) * 2

            if has_card and card_overlay_path and card_overlay_path.exists():
                split_filter = (
                    f"[0:v]crop=w={spk_cw}:h={spk_ch}:x='{spk_cx}':y={spk_cy},scale={target_width}:{top_h}[top]; "
                    rf"[1:v]crop=w=min(iw\,ih*{target_width}/{bot_h}):h=min(ih\,iw*{bot_h}/{target_width}):x=(iw-ow)/2:y=(ih-oh)/2,scale={target_width}:{bot_h}[bot]; "
                    f"[top][bot]vstack=inputs=2[stacked]; "
                    f"[2:v]scale={c_w}:{c_h}[card]; "
                    f"[stacked][card]overlay=(W-w)/2:{card_y},subtitles='{escaped_ass}'[v]"
                )
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{start_sec:.3f}",
                    "-i", str(src_path),
                    "-stream_loop", "-1",
                    "-i", str(Path(bg_video).resolve()),
                    "-i", str(card_overlay_path.resolve()),
                    "-filter_complex", split_filter,
                    "-map", "[v]",
                    "-map", "0:a:0",
                    "-t", f"{clip_duration:.3f}",
                    "-shortest",
                    "-r", "30",
                    "-c:v", encoder,
                    "-preset", "fast",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "48000",
                    "-ac", "2",
                    "-movflags", "+faststart",
                    str(final_mp4_path.resolve()),
                ]
            else:
                split_filter = (
                    f"[0:v]crop=w={spk_cw}:h={spk_ch}:x='{spk_cx}':y={spk_cy},scale={target_width}:{top_h}[top]; "
                    rf"[1:v]crop=w=min(iw\,ih*{target_width}/{bot_h}):h=min(ih\,iw*{bot_h}/{target_width}):x=(iw-ow)/2:y=(ih-oh)/2,scale={target_width}:{bot_h}[bot]; "
                    f"[top][bot]vstack=inputs=2,subtitles='{escaped_ass}'[v]"
                )
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{start_sec:.3f}",
                    "-i", str(src_path),
                    "-stream_loop", "-1",
                    "-i", str(Path(bg_video).resolve()),
                    "-filter_complex", split_filter,
                    "-map", "[v]",
                    "-map", "0:a:0",
                    "-t", f"{clip_duration:.3f}",
                    "-shortest",
                    "-r", "30",
                    "-c:v", encoder,
                    "-preset", "fast",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "48000",
                    "-ac", "2",
                    "-movflags", "+faststart",
                    str(final_mp4_path.resolve()),
                ]
        elif is_ambient:
            card_w = int(target_width * 0.92)
            card_h = int(card_w * (src_h / max(1, src_w)))
            if card_h % 2 != 0:
                card_h += 1
            vid_y = int((target_height * 0.70 - card_h) / 2 + target_height * 0.12)
            has_gameplay_bg = bool(bg_video and Path(bg_video).exists())

            if has_gameplay_bg:
                if has_card and card_overlay_path and card_overlay_path.exists():
                    ambient_filter = (
                        f"[1:v]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,crop={target_width}:{target_height},boxblur=25:5,eq=brightness=-0.15:contrast=1.05[bg]; "
                        f"[0:v]scale={card_w}:{card_h}[fg]; "
                        f"[2:v]scale={c_w}:{c_h}[card]; "
                        f"[bg][fg]overlay=(W-w)/2:{vid_y}[base]; "
                        f"[base][card]overlay=(W-w)/2:{card_y},subtitles='{escaped_ass}'[v]"
                    )
                    cmd = [
                        "ffmpeg", "-y",
                        "-ss", f"{start_sec:.3f}",
                        "-i", str(src_path),
                        "-stream_loop", "-1",
                        "-i", str(Path(bg_video).resolve()),
                        "-i", str(card_overlay_path.resolve()),
                        "-t", f"{clip_duration:.3f}",
                        "-filter_complex", ambient_filter,
                        "-map", "[v]",
                        "-map", "0:a:0",
                        "-r", "30",
                        "-c:v", encoder,
                        "-preset", "fast",
                        "-pix_fmt", "yuv420p",
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-ar", "48000",
                        "-ac", "2",
                        "-movflags", "+faststart",
                        str(final_mp4_path.resolve()),
                    ]
                else:
                    ambient_filter = (
                        f"[1:v]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,crop={target_width}:{target_height},boxblur=25:5,eq=brightness=-0.15:contrast=1.05[bg]; "
                        f"[0:v]scale={card_w}:{card_h}[fg]; "
                        f"[bg][fg]overlay=(W-w)/2:{vid_y},subtitles='{escaped_ass}'[v]"
                    )
                    cmd = [
                        "ffmpeg", "-y",
                        "-ss", f"{start_sec:.3f}",
                        "-i", str(src_path),
                        "-stream_loop", "-1",
                        "-i", str(Path(bg_video).resolve()),
                        "-t", f"{clip_duration:.3f}",
                        "-filter_complex", ambient_filter,
                        "-map", "[v]",
                        "-map", "0:a:0",
                        "-r", "30",
                        "-c:v", encoder,
                        "-preset", "fast",
                        "-pix_fmt", "yuv420p",
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-ar", "48000",
                        "-ac", "2",
                        "-movflags", "+faststart",
                        str(final_mp4_path.resolve()),
                    ]
            else:
                if has_card and card_overlay_path and card_overlay_path.exists():
                    ambient_filter = (
                        f"[0:v]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,crop={target_width}:{target_height},boxblur=25:5,eq=brightness=-0.15:contrast=1.05[bg]; "
                        f"[0:v]scale={card_w}:{card_h}[fg]; "
                        f"[1:v]scale={c_w}:{c_h}[card]; "
                        f"[bg][fg]overlay=(W-w)/2:{vid_y}[base]; "
                        f"[base][card]overlay=(W-w)/2:{card_y},subtitles='{escaped_ass}'[v]"
                    )
                    cmd = [
                        "ffmpeg", "-y",
                        "-ss", f"{start_sec:.3f}",
                        "-i", str(src_path),
                        "-i", str(card_overlay_path.resolve()),
                        "-t", f"{clip_duration:.3f}",
                        "-filter_complex", ambient_filter,
                        "-map", "[v]",
                        "-map", "0:a:0",
                        "-r", "30",
                        "-c:v", encoder,
                        "-preset", "fast",
                        "-pix_fmt", "yuv420p",
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-ar", "48000",
                        "-ac", "2",
                        "-movflags", "+faststart",
                        str(final_mp4_path.resolve()),
                    ]
                else:
                    ambient_filter = (
                        f"[0:v]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,crop={target_width}:{target_height},boxblur=25:5,eq=brightness=-0.15:contrast=1.05[bg]; "
                        f"[0:v]scale={card_w}:{card_h}[fg]; "
                        f"[bg][fg]overlay=(W-w)/2:{vid_y},subtitles='{escaped_ass}'[v]"
                    )
                    cmd = [
                        "ffmpeg", "-y",
                        "-ss", f"{start_sec:.3f}",
                        "-i", str(src_path),
                        "-t", f"{clip_duration:.3f}",
                        "-filter_complex", ambient_filter,
                        "-map", "[v]",
                        "-map", "0:a:0",
                        "-r", "30",
                        "-c:v", encoder,
                        "-preset", "fast",
                        "-pix_fmt", "yuv420p",
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-ar", "48000",
                        "-ac", "2",
                        "-movflags", "+faststart",
                        str(final_mp4_path.resolve()),
                    ]
        else:
            full_crop_x = f"'{crop_expr}'" if (has_motion and crop_expr != str(crop_x)) else str(crop_x)
            if has_card and card_overlay_path and card_overlay_path.exists():
                full_card_filter = (
                    f"[0:v]crop=w={crop_w}:h={crop_h}:x={full_crop_x}:y=0,scale={target_width}:{target_height}[vid]; "
                    f"[1:v]scale={c_w}:{c_h}[card]; "
                    f"[vid][card]overlay=(W-w)/2:{card_y},subtitles='{escaped_ass}'[v]"
                )
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{start_sec:.3f}",
                    "-i", str(src_path),
                    "-i", str(card_overlay_path.resolve()),
                    "-t", f"{clip_duration:.3f}",
                    "-filter_complex", full_card_filter,
                    "-map", "[v]",
                    "-map", "0:a:0",
                    "-r", "30",
                    "-c:v", encoder,
                    "-preset", "fast",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "48000",
                    "-ac", "2",
                    "-movflags", "+faststart",
                    str(final_mp4_path.resolve()),
                ]
            else:
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{start_sec:.3f}",
                    "-i", str(src_path),
                    "-t", f"{clip_duration:.3f}",
                    "-vf", f"crop=w={crop_w}:h={crop_h}:x={full_crop_x}:y=0,scale={target_width}:{target_height},subtitles='{escaped_ass}'",
                    "-r", "30",
                    "-c:v", encoder,
                    "-preset", "fast",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "48000",
                    "-ac", "2",
                    "-movflags", "+faststart",
                    str(final_mp4_path.resolve()),
                ]

        res = cls._safe_run_ffmpeg(cmd, timeout=180)
        if res.returncode != 0:
            cmd[cmd.index("-c:v") + 1] = "libx264"
            cls._safe_run_ffmpeg(cmd, timeout=180)

    @staticmethod
    def _safe_run_ffmpeg(cmd: List[str], timeout: int = 180) -> subprocess.CompletedProcess:
        """Executes FFmpeg with strict timeout to prevent hung worker threads."""
        try:
            return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"FFmpeg process timed out after {timeout} seconds: {' '.join(cmd[:4])}")

    @staticmethod
    def _detect_encoder() -> str:
        try:
            res = subprocess.run(["ffmpeg", "-encoders"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            if "h264_nvenc" in res.stdout:
                return "h264_nvenc"
        except Exception:
            pass
        return "libx264"

    @staticmethod
    def _measure_duration(video_path: str) -> float:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(Path(video_path).resolve()),
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
            if res.returncode == 0:
                return round(float(res.stdout.strip()), 2)
        except Exception:
            pass
        return 0.0
