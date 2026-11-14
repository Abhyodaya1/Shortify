"""YouTube Intelligence Service
Wraps the 11 specialized YouTube agent skills (yt-package, yt-script/hookscore, yt-seo, yt-retention)
into deterministic, zero-latency editorial intelligence for clip packaging and ranking.
"""

from __future__ import annotations
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Constants from yt-package
DESKTOP_LIMIT, MOBILE_LIMIT, HARD_LIMIT = 60, 40, 100
VAGUE_WORDS = {
    "amazing", "incredible", "insane", "crazy", "huge", "massive", "ultimate", "best", "powerful",
    "secret", "revolutionary", "mindblowing", "epic", "perfect", "complete", "everything"
}
STOP_WORDS = {
    "the", "a", "an", "of", "for", "to", "in", "on", "and", "or", "is", "are", "with", "your", "you",
    "my", "i", "this", "that", "it", "how", "what", "why"
}

# Regex from yt-script / hookscore
FILLER_WORDS = {
    "basically", "actually", "literally", "just", "really", "very", "so", "kind", "sort", "like",
    "guys", "hey", "welcome", "today", "video", "subscribe", "channel"
}
CONCRETE_RE = re.compile(r"\b(\d[\d,.]*\s?(%|k|m|x|s|m|h)?|\$\d|\d+\s?(second|minute|hour|day|week|month|year)s?)\b", re.I)
YOU_RE = re.compile(r"\b(you|your|you're|youre|yourself)\b", re.I)
STAKE_RE = re.compile(r"\b(lose|lost|wasting|waste|quit|fail|broke|cost|risk|before|stop|never|die|dying|dead)\b", re.I)
CURIOSITY_RE = re.compile(r"\b(why|how|what|which|until|before|but|nobody|almost|except|reason|actually)\b", re.I)


class YouTubeIntelligenceService:
    """Provides deterministic scoring and packaging intelligence inspired by YouTube creator agent skills."""

    @classmethod
    def words(cls, text: str) -> List[str]:
        return re.findall(r"[a-z0-9'%$.]+", text.lower())

    @classmethod
    def score_hook(cls, hook_text: str) -> Dict[str, Any]:
        """Scores a hook on five properties (0-100 each) with a 60% mean / 40% weakest-link verdict."""
        t = hook_text.strip()
        w = cls.words(t)
        if not w:
            return {"score": 0, "verdict": "Empty hook", "issues": ["No text provided"]}

        # 1. Specificity (0-100)
        nums = len(CONCRETE_RE.findall(t))
        vague_count = sum(1 for x in w if x in VAGUE_WORDS)
        filler_count = sum(1 for x in w if x in FILLER_WORDS)
        s = 34 + nums * 22 - vague_count * 16 - filler_count * 5
        s += min(18, 6 * sum(1 for x in t.split()[1:] if x[:1].isupper()))
        specificity = max(0, min(100, s))

        # 2. Direct Address (0-100)
        you_count = len(YOU_RE.findall(t))
        first_address = 30 if YOU_RE.search(" ".join(t.split()[:6])) else 0
        address = max(0, min(100, 26 + you_count * 20 + first_address))

        # 3. Stakes (0-100)
        stake_count = len(STAKE_RE.findall(t))
        stakes = max(0, min(100, 22 + stake_count * 26 + (14 if CONCRETE_RE.search(t) else 0)))

        # 4. Curiosity Gap (0-100)
        curiosity_count = len(CURIOSITY_RE.findall(t))
        q = 18 if t.strip().endswith("?") else 0
        closed = -18 if re.search(r"\b(because|so that|which means)\b", t, re.I) else 0
        curiosity = max(0, min(100, 24 + curiosity_count * 17 + q + closed))

        # 5. Brevity (0-100)
        wc = len(w)
        if wc <= 14:
            brevity = 100
        elif wc <= 22:
            brevity = max(0, 100 - (wc - 14) * 8)
        else:
            brevity = max(0, 36 - (wc - 22) * 4)

        metrics = {
            "specificity": specificity,
            "direct_address": address,
            "stakes": stakes,
            "curiosity_gap": curiosity,
            "brevity": brevity,
        }

        weakest_key = min(metrics, key=metrics.get)
        weakest_score = metrics[weakest_key]
        mean_score = sum(metrics.values()) / len(metrics)
        # 60% mean, 40% weakest link
        final_score = int(0.6 * mean_score + 0.4 * weakest_score)

        issues = []
        if address < 50:
            issues.append("Needs direct address ('you' / 'your') in opening seconds.")
        if specificity < 50:
            issues.append("Too abstract; swap filler for a concrete number, timeframe, or proper noun.")
        if stakes < 50:
            issues.append("Stakes are low; signpost what the viewer risks or loses.")
        if brevity < 50:
            issues.append("Over 22 words; tighten the opening take down to under 15 words.")

        return {
            "score": final_score,
            "metrics": metrics,
            "weakest_link": weakest_key,
            "issues": issues,
            "is_viral_grade": final_score >= 75,
        }

    @classmethod
    def lint_packaging(cls, title: str, thumbnail_text: Optional[str] = None) -> Dict[str, Any]:
        """Lints title length, mobile truncation, and thumbnail synergy according to yt-package rules."""
        t = title.strip()
        n = len(t)
        issues, good = [], []

        if n > HARD_LIMIT:
            issues.append(f"{n} characters exceeds YouTube's hard limit of {HARD_LIMIT}")
        elif n > DESKTOP_LIMIT:
            issues.append(f"{n} characters: desktop search cuts near {DESKTOP_LIMIT}")
        else:
            good.append(f"{n} characters, safely within desktop limit")

        if n > MOBILE_LIMIT:
            head = t[:MOBILE_LIMIT].rsplit(" ", 1)[0]
            issues.append(f"Mobile feed truncates to '{head}...'; ensure core hook is preserved")

        caps = [w for w in t.split() if len(w) > 2 and w.isupper()]
        if len(caps) > 2:
            issues.append(f"{len(caps)} all-caps words may trigger spam filters (limit to 2)")
        elif caps:
            good.append(f"{len(caps)} all-caps word for visual punch")

        vague_found = [w for w in cls.words(t) if w in VAGUE_WORDS]
        if vague_found:
            issues.append(f"Vague words ({', '.join(sorted(set(vague_found)))}); replace with concrete details")

        nums = re.findall(r"\d[\d,.]*%?", t)
        if nums:
            good.append(f"Carries concrete figure ({', '.join(nums[:3])})")
        else:
            issues.append("No number or timeframe found; numbers boost CTR significantly")

        if thumbnail_text:
            tw = set(cls.words(t)) - STOP_WORDS
            hw = set(cls.words(thumbnail_text)) - STOP_WORDS
            shared = tw & hw
            if shared:
                issues.append(f"Thumbnail text repeats title on '{', '.join(sorted(shared))}'; thumbnail should say what title does not")
            else:
                good.append("Thumbnail and title carry distinct complementary text")

            thumb_word_count = len(cls.words(thumbnail_text))
            if thumb_word_count > 3:
                issues.append(f"{thumb_word_count} words on thumbnail; 3 words is maximum at feed size")

        score = max(0, min(100, 100 - 14 * len(issues) + 4 * len(good)))

        return {
            "title": t,
            "chars": n,
            "score": score,
            "issues": issues,
            "good": good,
            "is_optimized": score >= 80,
        }

    @classmethod
    def generate_seo_metadata(cls, topic: str, headline: str, channel_handle: str = "@AbhyodayaClips") -> Dict[str, Any]:
        """Generates high-CTR descriptions, hashtags, and targeted tags according to yt-seo."""
        clean_topic = topic.replace("#", "").strip()
        tags = [
            "Shorts",
            "YouTubeShorts",
            "Trending",
            "Viral",
            clean_topic.split()[0] if clean_topic else "Growth",
            "LifeLessons",
            "Success",
            "Mindset",
        ]

        description = (
            f"{headline}\n\n"
            f"Here is the breakdown on {clean_topic}. Watch the full insight above.\n\n"
            f"Subscribe to {channel_handle} for daily high-impact clips and lessons.\n\n"
            f"#Shorts #{clean_topic.replace(' ', '')} #Viral #Mindset"
        )

        return {
            "title": headline[:58],
            "description": description,
            "tags": tags,
            "thumbnail_concept": {
                "badge_text": clean_topic[:14].upper(),
                "hook_phrase": "DON'T MISS THIS",
                "recommended_colors": ["#183746", "#81E1DA", "#FFFFFF"],
            }
        }

