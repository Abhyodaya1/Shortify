"""Unified YouTube Creator Skills Engine.
Consolidates deterministic mathematical algorithms, title linting heuristics, dead-air analysis,
hook scoring, and viral outlier calculations from YouTube agent skills:
- yt-package (title.py): Advisory title length (40/60 char warnings, 100 max), stop words, caps ratio.
- yt-script (hookscore.py): 5-property hook scoring (Specificity, Direct Address, Stakes, Curiosity, Brevity).
- yt-edit (deadair.py): Non-destructive advisory dead-air, filler, and retake detection.
- yt-viral (swipe.py): Outlier multiple (views / median) and relative lift ((views - median) / median).
"""

from __future__ import annotations
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Constants & thresholds from yt-package
DESKTOP_LIMIT: int = 60
MOBILE_LIMIT: int = 40
HARD_LIMIT: int = 100

VAGUE_WORDS = {
    "amazing", "incredible", "insane", "crazy", "huge", "massive", "ultimate", "best", "powerful",
    "secret", "revolutionary", "mindblowing", "epic", "perfect", "complete", "everything",
    "unbelievable", "shocking", "gamechanger", "magic", "wonder"
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

# Regex from yt-edit / deadair
FILLER_ONLY = re.compile(
    r"^[\s,.-]*((um+|uh+|er+|ah+|so|okay|ok|right|yeah|like|anyway|basically|"
    r"actually|you know|i mean|let me see|hold on)[\s,.-]*)+$",
    re.I
)

# 21 Hook formula patterns from skills/yt-script/hooks.json
HOOK_FORMULAS = [
    {"name": "Negative Constraint", "match": [r"\bstop\b", r"\bnever\b", r"\bdon't\b", r"\bdont\b", r"\bquit\b"]},
    {"name": "Curiosity Gap", "match": [r"\bthe secret\b", r"\bwhy nobody\b", r"\bwhat happens when\b", r"\bhidden\b"]},
    {"name": "Contrarian Truth", "match": [r"\blie\b", r"\bwrong\b", r"\bmyth\b", r"\btruth about\b"]},
    {"name": "Specific Number / Timeline", "match": [r"\b\d+\s?(days?|weeks?|months?|years?|hours?|minutes?|seconds?)\b", r"\$\d+"]},
    {"name": "Direct Challenge", "match": [r"\bare you\b", r"\bcan you\b", r"\bif you\b", r"\byou should\b"]},
    {"name": "Bold Prediction", "match": [r"\bwill happen\b", r"\bthe future of\b", r"\bby 202\d\b"]},
]


class YouTubeIntelligenceService:
    """Unified YouTube Creator Skills Engine providing deterministic heuristics and advisory intelligence."""

    @classmethod
    def words(cls, text: str) -> List[str]:
        """Extracts sanitized word tokens."""
        return re.findall(r"[a-z0-9'%$.]+", text.lower())

    # -------------------------------------------------------------------------
    # 1. yt-script: Hook Scoring (5-Property Algorithm)
    # -------------------------------------------------------------------------
    @classmethod
    def score_hook(cls, hook_text: str) -> Dict[str, Any]:
        """Scores a hook on five properties (0-100 each) with a 60% mean / 40% weakest-link verdict."""
        t = (hook_text or "").strip()
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

    # -------------------------------------------------------------------------
    # 2. yt-package: Title & Packaging Linter (Advisory Heuristics)
    # -------------------------------------------------------------------------
    @classmethod
    def lint_title(cls, title: str, thumbnail_text: Optional[str] = None) -> Dict[str, Any]:
        """Lints title length, mobile truncation, and thumbnail synergy according to yt-package rules.

        Treats 40/60 character limits as advisory warnings, not blocking rejections.
        Platform limit is 100 characters.
        """
        t = (title or "").strip()
        n = len(t)
        issues, advisories, good = [], [], []

        # Platform hard limit vs advisory feed limits
        if n > HARD_LIMIT:
            issues.append(f"{n} characters exceeds YouTube's platform hard limit of {HARD_LIMIT}")
        elif n > DESKTOP_LIMIT:
            advisories.append(f"{n} characters: desktop search results cut near {DESKTOP_LIMIT} characters")
        else:
            good.append(f"{n} characters, safely within desktop limit")

        if n > MOBILE_LIMIT:
            head = t[:MOBILE_LIMIT].rsplit(" ", 1)[0]
            advisories.append(f"Mobile feed truncates near '{head}...'; ensure the core hook is in the first 40 chars")

        # All-caps ratio check
        words_list = t.split()
        caps = [w for w in words_list if len(w) > 2 and w.isupper()]
        if len(caps) > 2:
            advisories.append(f"{len(caps)} all-caps words may trigger algorithm suppression (limit to 1-2 words)")
        elif caps:
            good.append(f"{len(caps)} all-caps word for visual punch")

        # Vague word check
        vague_found = [w for w in cls.words(t) if w in VAGUE_WORDS]
        if vague_found:
            advisories.append(f"Contains vague word(s) ({', '.join(sorted(set(vague_found)))}); replace with concrete details")

        # Concrete numbers check
        nums = re.findall(r"\d[\d,.]*%?", t)
        if nums:
            good.append(f"Carries concrete figure ({', '.join(nums[:3])})")
        else:
            advisories.append("No number or timeframe found; concrete numbers boost click-through rate")

        # Thumbnail synergy check
        if thumbnail_text:
            tw = set(cls.words(t)) - STOP_WORDS
            hw = set(cls.words(thumbnail_text)) - STOP_WORDS
            shared = tw & hw
            if shared:
                advisories.append(
                    f"Thumbnail text duplicates title on '{', '.join(sorted(shared))}'; "
                    "thumbnail should complement what title cannot say"
                )
            else:
                good.append("Thumbnail and title carry distinct complementary text")

            thumb_word_count = len(cls.words(thumbnail_text))
            if thumb_word_count > 3:
                advisories.append(f"{thumb_word_count} words on thumbnail; 3 words is maximum at mobile feed size")

        score = max(0, min(100, 100 - 20 * len(issues) - 8 * len(advisories) + 5 * len(good)))

        return {
            "title": t,
            "chars": n,
            "score": score,
            "is_valid": len(issues) == 0,
            "issues": issues,
            "advisories": advisories,
            "good": good,
            "is_optimized": score >= 75 and len(issues) == 0,
        }

    # Backward compatibility alias
    lint_packaging = lint_title

    # -------------------------------------------------------------------------
    # 3. yt-edit: Non-Destructive Advisory Dead-Air & Retake Analysis
    # -------------------------------------------------------------------------
    @classmethod
    def analyze_dead_air(
        cls,
        cues: List[Dict[str, Any]] | List[Tuple[float, float, str]],
        floor: float = 1.2,
    ) -> Dict[str, Any]:
        """Scans transcript cues for dead air gaps, filler-only segments, and speech retakes.

        ADVISORY ONLY: Does not delete or cut footage blindly. Returns an Edit Decision List
        (EDL) for creator preview, preserving dramatic pauses and setup beats.
        """
        # Normalize cues to (start, end, text) tuples
        normalized_cues: List[Tuple[float, float, str]] = []
        for c in cues:
            if isinstance(c, (list, tuple)) and len(c) >= 3:
                normalized_cues.append((float(c[0]), float(c[1]), str(c[2]).strip()))
            elif isinstance(c, dict):
                s = float(c.get("start_sec", c.get("start", 0.0)))
                e = float(c.get("end_sec", c.get("end", 0.0)))
                t = str(c.get("text", "")).strip()
                normalized_cues.append((s, e, t))

        if not normalized_cues:
            return {"total_cuts": 0, "advisory_cuts": [], "total_removable_sec": 0.0}

        cuts: List[Dict[str, Any]] = []
        total_duration = normalized_cues[-1][1] - normalized_cues[0][0]

        for i, (s, e, t) in enumerate(normalized_cues):
            # Check 1: Filler-only cues ("um", "uh", "so yeah")
            if FILLER_ONLY.match(t):
                cuts.append({
                    "kind": "FILLER",
                    "start": round(s, 2),
                    "end": round(e, 2),
                    "duration": round(e - s, 2),
                    "why": f"Filler only: '{t[:40]}'",
                    "advisory": "Candidate for removal; verify non-verbal facial reaction before cutting."
                })

            # Check 2: Silence gaps between cues longer than floor
            if i > 0:
                prev_end = normalized_cues[i - 1][1]
                gap = s - prev_end
                if gap > floor:
                    keep = floor / 2.0
                    cut_s = round(prev_end + keep, 2)
                    cut_e = round(s - keep, 2)
                    if cut_e > cut_s:
                        cuts.append({
                            "kind": "DEAD_AIR",
                            "start": cut_s,
                            "end": cut_e,
                            "duration": round(cut_e - cut_s, 2),
                            "why": f"{gap:.2f}s pause between dialogue",
                            "advisory": "Advisory pause: keep if building dramatic tension or punchline suspense."
                        })

            # Check 3: Sentence restarts (retakes)
            if t.strip() and not FILLER_ONLY.match(t):
                j = i - 1
                while j >= 0 and (FILLER_ONLY.match(normalized_cues[j][2]) or not normalized_cues[j][2].strip()):
                    j -= 1
                if j >= 0:
                    a1 = cls.words(normalized_cues[j][2])[:5]
                    b1 = cls.words(t)[:5]
                    if len(a1) >= 3 and a1 == b1:
                        cuts.append({
                            "kind": "RESTART",
                            "start": round(normalized_cues[j][0], 2),
                            "end": round(normalized_cues[j][1], 2),
                            "duration": round(normalized_cues[j][1] - normalized_cues[j][0], 2),
                            "why": f"Restart of sentence: '{' '.join(a1)}'",
                            "advisory": "First take appears abandoned; second take retained."
                        })

        cuts.sort(key=lambda x: x["start"])
        removable_sec = sum(c["duration"] for c in cuts)

        return {
            "total_cues": len(normalized_cues),
            "total_cuts": len(cuts),
            "total_removable_sec": round(removable_sec, 2),
            "estimated_trimmed_duration_sec": round(max(0.0, total_duration - removable_sec), 2),
            "advisory_cuts": cuts,
        }

    # -------------------------------------------------------------------------
    # 4. yt-viral: Swipe Outlier Multiple & Relative Lift Calculations
    # -------------------------------------------------------------------------
    @classmethod
    def calculate_viral_metrics(
        cls,
        views: float,
        channel_median_views: float,
        video_count: int = 4,
    ) -> Dict[str, Any]:
        """Calculates Outlier Multiple and Relative Lift with sample size validation.

        - Outlier Multiple = views / channel_median_views
        - Relative Lift = (views - channel_median_views) / channel_median_views
        """
        if video_count < 4:
            return {
                "valid": False,
                "warning": f"Insufficient sample size: {video_count} video(s) collected. Minimum 4 required to establish a valid median.",
                "outlier_multiple": 1.0,
                "relative_lift_pct": 0.0,
            }

        if channel_median_views <= 0:
            return {
                "valid": False,
                "warning": "Channel median views must be greater than zero.",
                "outlier_multiple": 1.0,
                "relative_lift_pct": 0.0,
            }

        multiple = views / channel_median_views
        relative_lift = (views - channel_median_views) / channel_median_views

        return {
            "valid": True,
            "views": int(views),
            "median_views": int(channel_median_views),
            "outlier_multiple": round(multiple, 2),
            "relative_lift_pct": round(relative_lift * 100.0, 1),
            "is_outlier": multiple >= 1.5,
            "is_mega_outlier": multiple >= 3.0,
        }

    @classmethod
    def classify_hook_formula(cls, text: str) -> str:
        """Classifies text against known high-retention hook formulas."""
        for formula in HOOK_FORMULAS:
            for pattern in formula["match"]:
                if re.search(pattern, text, re.I):
                    return formula["name"]
        return "Insight / Story Lead"

    # -------------------------------------------------------------------------
    # 5. yt-seo: Compliant Metadata Generation
    # -------------------------------------------------------------------------
    @classmethod
    def generate_seo_metadata(cls, topic: str, headline: str, channel_handle: str = "@AbhyodayaClips") -> Dict[str, Any]:
        """Generates high-CTR descriptions, hashtags, and targeted tags adhering to Section 11 SEO criteria."""
        clean_topic = topic.replace("#", "").strip()
        tags = [
            "Shorts",
            "YouTubeShorts",
            clean_topic.split()[0] if clean_topic else "Growth",
            "VideoTips",
            "CreatorEconomy",
        ]

        description = (
            f"{headline}\n\n"
            f"Here is the breakdown on {clean_topic}. Watch the full insight above.\n\n"
            f"Subscribe to {channel_handle} for daily high-impact clips and lessons.\n\n"
            f"#Shorts #{clean_topic.replace(' ', '')} #Creator"
        )

        return {
            "title": headline[:60],
            "description": description,
            "tags": tags[:15],
            "hashtags": ["#shorts", f"#{clean_topic.replace(' ', '')}", "#creator"][:5],
            "thumbnail_concept": {
                "badge_text": clean_topic[:14].upper(),
                "hook_phrase": "MUST WATCH",
                "recommended_colors": ["#183746", "#81E1DA", "#FFFFFF"],
            }
        }
