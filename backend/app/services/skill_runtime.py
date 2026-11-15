"""Runtime loader and execution engine for Jake Schincariol's YouTube Agent Skills.
Loads skill instructions from skills/ and executes runtime helper scripts:
- skills/yt-package/title.py: 40/60 char truncation, duplication, vague words, numbers/entities.
- skills/yt-script/hookscore.py: 5-property hook scoring algorithm.
- skills/yt-viral/swipe.py: Viral outlier and pattern classification.
- skills/yt-seo/SKILL.md: Search snippet (first 2 lines), max 15 disambiguation tags, Query Test.
- skills/yt-shorts/SKILL.md: Self-contained moment criteria, hook replacement.
"""

from __future__ import annotations
import os
import sys
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class YouTubeSkillRuntime:
    """Discovers, loads, and executes Jake Schincariol's YouTube creator skills at runtime."""

    _cached_skills_dir: Optional[Path] = None
    _title_module = None
    _hookscore_module = None
    _swipe_module = None

    @classmethod
    def get_skills_dir(cls) -> Path:
        """Locates the skills directory in workspace or parent paths."""
        if cls._cached_skills_dir and cls._cached_skills_dir.exists():
            return cls._cached_skills_dir

        candidates = [
            Path("skills").resolve(),
            Path.cwd() / "skills",
            Path(__file__).resolve().parents[3] / "skills",
            Path(__file__).resolve().parents[4] / "skills",
        ]
        for c in candidates:
            if c.exists() and (c / "yt-seo" / "SKILL.md").exists():
                cls._cached_skills_dir = c
                return c

        fallback = Path("skills").resolve()
        cls._cached_skills_dir = fallback
        return fallback

    @classmethod
    def load_skill_markdown(cls, skill_name: str) -> str:
        """Loads raw SKILL.md markdown text for a specified skill."""
        skills_dir = cls.get_skills_dir()
        skill_file = skills_dir / skill_name / "SKILL.md"
        if skill_file.exists():
            return skill_file.read_text(encoding="utf-8")
        return ""

    @classmethod
    def get_package_seo_guidance(cls) -> str:
        """Extracts runtime operational directives from yt-seo and yt-package SKILL.md."""
        seo_md = cls.load_skill_markdown("yt-seo")
        pkg_md = cls.load_skill_markdown("yt-package")
        shorts_md = cls.load_skill_markdown("yt-shorts")

        guidance_sections = []

        if seo_md:
            guidance_sections.append(
                "--- JAKE SCHINCARIOL / yt-seo DIRECTIVES ---\n"
                "- The Description Search Snippet: The first two lines are the ONLY lines visible before '...more' "
                "and act as the search snippet. State clearly what the video gives the viewer in the exact search words they type.\n"
                "- Tags, honestly: Tags are a weak signal used for disambiguation (spellings, tool names, artist/song names, abbreviations people actually type). "
                "Stop at 15 tags maximum. Plain text only, no '#'. A wall of tags is not a strategy; stuffing unrelated tags violates YouTube terms.\n"
                "- The Query Test: Identify the three search queries this video should win. The title and the first two description lines MUST naturally contain the words in those queries.\n"
                "- Never invent numbers, sources, or claims absent from the source."
            )

        if pkg_md:
            guidance_sections.append(
                "--- JAKE SCHINCARIOL / yt-package DIRECTIVES ---\n"
                "- Title and thumbnail are ONE unit. Thumbnail must NOT repeat the title (different words, same promise).\n"
                "- 60 characters is the desktop search cutoff; 40 characters is the mobile home feed cutoff. Ensure the core hook and subject sit inside the first 40 characters.\n"
                "- A concrete number, an entity name, or a date beats every vague adjective (avoid: amazing, insane, secret, ultimate, mindblowing).\n"
                "- Two all-caps words is the absolute ceiling before a title reads as spam. Never use all-caps titles."
            )

        if shorts_md:
            guidance_sections.append(
                "--- JAKE SCHINCARIOL / yt-shorts DIRECTIVES ---\n"
                "- A Short must survive without the long video around it: opens on a complete thought, contains a turn/climax, and ends on a line, not a trail-off.\n"
                "- First two seconds require high-impact curiosity or statement that confirmation-checks the title promise."
            )

        if not guidance_sections:
            return (
                "Apply core YouTube packaging rules: First two lines of description act as search snippet; "
                "titles under 60 chars desktop / 40 chars mobile; up to 15 plain disambiguation tags without '#'; "
                "no raw transcript dumping; no generic boilerplate."
            )

        return "\n\n".join(guidance_sections)

    @classmethod
    def _get_module(cls, rel_path: str, mod_name: str):
        """Dynamically imports a Python helper module from the skills folder."""
        skills_dir = cls.get_skills_dir()
        script_path = skills_dir / rel_path
        if not script_path.exists():
            return None
        try:
            spec = importlib.util.spec_from_file_location(mod_name, str(script_path))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[mod_name] = mod
                spec.loader.exec_module(mod)
                return mod
        except Exception as e:
            print(f"[YouTubeSkillRuntime] Failed to import {rel_path}: {e}")
            return None
        return None

    @classmethod
    def check_title(cls, title_text: str, thumbnail_text: str = "") -> Dict[str, Any]:
        """Runs skills/yt-package/title.py against a title candidate."""
        if cls._title_module is None:
            cls._title_module = cls._get_module("yt-package/title.py", "jake_title_checker")

        if cls._title_module and hasattr(cls._title_module, "check"):
            try:
                res = cls._title_module.check(title_text, thumbnail_text)
                return {
                    "source": "jake_title_py",
                    "title": res.get("title", title_text),
                    "chars": res.get("chars", len(title_text)),
                    "score": res.get("score", 70),
                    "issues": [f"{code}: {msg}" for code, msg in res.get("issues", [])],
                    "good": res.get("good", []),
                    "mobile_safe": len(title_text) <= 40,
                    "desktop_safe": len(title_text) <= 60,
                }
            except Exception as e:
                return {"source": "fallback", "error": str(e), "mobile_safe": len(title_text) <= 40}

        # Fallback lint logic
        chars = len(title_text)
        issues = []
        if chars > 60:
            issues.append("desktop-cut: truncated on desktop search (>60 chars)")
        if chars > 40:
            issues.append("mobile-cut: truncated on mobile home feed (>40 chars)")
        return {
            "source": "fallback",
            "title": title_text,
            "chars": chars,
            "score": 75 if chars <= 40 else (60 if chars <= 60 else 45),
            "issues": issues,
            "good": ["Under 40 chars mobile safe"] if chars <= 40 else [],
            "mobile_safe": chars <= 40,
            "desktop_safe": chars <= 60,
        }

    @classmethod
    def score_hook(cls, hook_text: str) -> Dict[str, Any]:
        """Runs skills/yt-script/hookscore.py against an opening hook."""
        if cls._hookscore_module is None:
            cls._hookscore_module = cls._get_module("yt-script/hookscore.py", "jake_hookscore")

        if cls._hookscore_module and hasattr(cls._hookscore_module, "score"):
            try:
                scores, overall, formula, rank = cls._hookscore_module.score(hook_text)
                return {
                    "source": "jake_hookscore_py",
                    "hook": hook_text,
                    "score": overall,
                    "formula": formula,
                    "rank": rank,
                    "breakdown": scores,
                }
            except Exception as e:
                return {"source": "fallback", "error": str(e), "score": 75}

        return {"source": "fallback", "hook": hook_text, "score": 75, "formula": "Direct Hook"}

    @classmethod
    def classify_title_swipe(cls, title_text: str) -> str:
        """Runs skills/yt-viral/swipe.py to classify the viral angle pattern."""
        if cls._swipe_module is None:
            cls._swipe_module = cls._get_module("yt-viral/swipe.py", "jake_swipe")

        if cls._swipe_module and hasattr(cls._swipe_module, "classify"):
            try:
                return str(cls._swipe_module.classify(title_text))
            except Exception:
                return "Direct"
        return "Direct"
