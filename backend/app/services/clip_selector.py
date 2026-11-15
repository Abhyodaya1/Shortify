"""AI Clip Selection, Content Understanding & Scoring Engine.
Implements the 6-parameter editorial evaluation and 21-formula hook validation specified in 01_SYSTEM_PROMPT.md.
"""

from __future__ import annotations
import os
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4

from .viral_clipper import ViralHookScorer
from .llm_provider import get_llm_provider
from .editorial_orchestrator import EditorialOrchestrator
from .youtube_intelligence_service import YouTubeIntelligenceService
from ..models.editorial_profile import EditorialProfile
from ..storage.profile_store import ProfileStore


class SmartClipSelector:
    """Discovers, scores, and packages 31-second and 45-second viral Shorts candidates."""

    # 6-dimension editorial heuristic weights from 01_SYSTEM_PROMPT.md Section 5
    WEIGHTS = {
        "hook": 0.20,
        "standalone_context": 0.20,
        "information_density": 0.20,
        "story_progression": 0.15,
        "interest": 0.10,
        "payoff": 0.15,
    }

    @classmethod
    async def discover_clips(
        cls,
        cues: List[Dict[str, Any]],
        video_title: str = "Source Video",
        duration_mode: str = "31s",  # "31s" or "45s"
        profile: Optional[EditorialProfile] = None,
    ) -> List[Dict[str, Any]]:
        """Identifies, scores, and ranks candidate clips targeting exact duration modes with payoff verification."""
        active_profile = profile or ProfileStore.get_active_profile()
        target_dur = 31.0 if duration_mode == "31s" else 45.0
        tolerance = active_profile.duration_tolerance_seconds

        min_dur = target_dur - tolerance
        max_dur = target_dur + tolerance

        if not cues:
            return []

        # 1. Discover all candidate spans matching the target duration window
        raw_candidates = cls._find_duration_targeted_spans(cues, target_dur, min_dur, max_dur)

        if not raw_candidates:
            # Fallback search with slightly wider boundary [target - 3.0, target + 3.0]
            raw_candidates = cls._find_duration_targeted_spans(cues, target_dur, target_dur - 3.0, target_dur + 3.0)

        if not raw_candidates:
            # Emergency fallback: slice from start up to target duration
            end_t = cues[0]["start_sec"] + target_dur
            subset = [c for c in cues if c["start_sec"] < end_t]
            if not subset:
                subset = cues[:min(len(cues), 10)]
            actual_dur = round(subset[-1]["end_sec"] - subset[0]["start_sec"], 2)
            raw_candidates.append({
                "start_sec": subset[0]["start_sec"],
                "end_sec": subset[-1]["end_sec"],
                "duration_sec": actual_dur,
                "spoken_text": " ".join(c["text"] for c in subset),
                "cues": subset,
                "sentence_complete": True,
            })

        # 2. Filter overlapping candidates (>10s overlap)
        filtered_candidates = cls._filter_overlapping(raw_candidates)

        # 3. Score all candidates with LLM + 21 Hook Formulas
        processed_clips = []
        llm = get_llm_provider()

        for idx, cand in enumerate(filtered_candidates):
            clip_id = str(uuid4())[:8]

            # A. Hook generation and headline evaluation via Roles 02 & 03
            try:
                hook_data = EditorialOrchestrator.generate_clip_strategy(
                    clip_id=clip_id,
                    transcript_text=cand["spoken_text"],
                    duration_seconds=cand["duration_sec"],
                    channel_niche=video_title,
                    target_audience="Short-form mobile viewers",
                )
            except Exception:
                hook_data = await cls._generate_and_evaluate_hooks(
                    cand["spoken_text"], video_title, cand["duration_sec"], llm, active_profile
                )

            # B. 6-parameter editorial scoring
            scores = cls._compute_editorial_scores(
                cand["spoken_text"],
                hook_data["best_hook"]["score"],
                hook_data["best_hook"]["formula_name"],
                cand["duration_sec"],
                target_dur,
                cand.get("sentence_complete", True),
            )

            # C. Hard Rejection Checks (01_SYSTEM_PROMPT.md Section 5)
            hard_rejections = cls._check_hard_rejections(
                cand, hook_data["best_hook"], scores["breakdown"], active_profile
            )

            if hard_rejections and active_profile.reject_misleading_hooks:
                human_review_required = True
            else:
                human_review_required = False

            # D. Content packaging
            clean_headline = hook_data.get("visual_headline", "").strip() or f"Key Insight #{idx + 1}"
            content_pkg = cls._generate_content_package(
                cand["spoken_text"],
                hook_data["best_hook"]["text"],
                video_title,
                visual_headline=clean_headline,
            )

            processed_clips.append({
                "clip_id": clip_id,
                "index": idx + 1,
                "duration_mode": duration_mode,
                "target_duration_seconds": int(target_dur),
                "start_sec": cand["start_sec"],
                "end_sec": cand["end_sec"],
                "duration_sec": cand["duration_sec"],
                "main_topic": content_pkg["topic"],
                "central_idea": content_pkg["central_idea"],
                "why_engaging": scores["why_engaging"],
                "opening_hook": hook_data["best_hook"]["text"],
                "hook_score": hook_data["best_hook"]["score"],
                "hook_verdict": hook_data["best_hook"]["verdict"],
                "hook_formula": hook_data["best_hook"]["formula_name"],
                "hook_weakest": hook_data["best_hook"]["weakest_link"],
                "hook_alternatives": hook_data["all_hooks"],
                "visual_headline": clean_headline,
                "headline_candidates": hook_data.get("headline_candidates", []),
                "key_hooks": hook_data.get("key_hooks", ["Bold Contrarian Claim", "Relatable Pain Point"]),
                "why_viral": hook_data.get("why_viral", scores["why_engaging"]),
                "engagement_score": scores["total_score"],
                "virality_score": scores["total_score"],
                "virality_breakdown": scores.get("virality_breakdown", hook_data.get("virality_breakdown", {
                    "hook_score": 23,
                    "engagement_score": 22,
                    "value_score": 24,
                    "shareability_score": 21,
                    "total_virality": scores["total_score"],
                })),
                "score_breakdown": scores["breakdown"],
                "hard_rejection_reasons": hard_rejections,
                "human_review_required": human_review_required,
                "title": f"#{idx + 1} {clean_headline}",
                "title_alternatives": content_pkg.get("title_alternatives", []),
                "title_lint_advisory": YouTubeIntelligenceService.lint_title(clean_headline),
                "dead_air_advisory": YouTubeIntelligenceService.analyze_dead_air(cand["cues"], floor=1.2),
                "description": content_pkg["description"],
                "hashtags": content_pkg["hashtags"],
                "tags": content_pkg.get("tags", []),
                "pinned_comment": content_pkg["pinned_comment"],
                "enable_opening_hook": False,  # Default clean start without prepended voiceover
                "subtitles": [
                    {
                        "start_rel_sec": round(float(c.get("start_sec", c.get("start", 0.0))) - cand["start_sec"], 2),
                        "end_rel_sec": round(float(c.get("end_sec", c.get("end", 0.0))) - cand["start_sec"], 2),
                        "text": c["text"],
                    }
                    for c in cand["cues"]
                ],
                "spoken_text": cand["spoken_text"],
                "profile_snapshot": active_profile.snapshot(),
            })

        # Apply dynamic shorts selection (virality_score > 60, top-5 fallback)
        selection_result = cls.apply_dynamic_selection(processed_clips)
        return selection_result["selected_clips"]

    @classmethod
    def apply_dynamic_selection(
        cls,
        candidates: List[Dict[str, Any]],
        virality_threshold: int = 60,
        fallback_top_k: int = 5,
    ) -> Dict[str, Any]:
        """Dynamically selects Shorts candidates based on virality threshold (> 60).

        Rules:
        1. Qualifying condition is strictly virality_score > 60 (score of 60 does NOT qualify).
        2. If qualifying candidates exist: select ALL qualifying candidates (no upper cap: 2, 3, 5, 8, 10...).
        3. If ZERO candidates exceed 60: select top 5 highest-scoring valid candidates (or all available if < 5).
        4. If even one candidate exceeds 60: select all exceeding 60 (never pad with lower-scoring candidates).
        5. Never fabricate clips or artificially inflate scores.
        6. Selection transparency: annotate each clip with virality_score, candidate_rank,
           passed_threshold, is_fallback, selection_reason, batch_message.
        """
        if not candidates:
            return {
                "selected_clips": [],
                "selection_mode": "empty",
                "batch_message": "No Shorts candidates found.",
                "qualifying_count": 0,
                "total_evaluated": 0,
                "is_fallback": False,
            }

        # Sort all evaluated candidates descending by virality_score (or engagement_score)
        sorted_candidates = sorted(
            candidates,
            key=lambda x: (
                float(x.get("virality_score", x.get("engagement_score", 0))),
                float(x.get("hook_score", 0))
            ),
            reverse=True,
        )

        # Assign 1-based candidate_rank across all evaluated candidates
        for rank_idx, cand in enumerate(sorted_candidates):
            cand["candidate_rank"] = rank_idx + 1

        # Strict condition: virality_score > 60 (score of 60 does NOT qualify)
        qualifying = [
            c for c in sorted_candidates
            if float(c.get("virality_score", c.get("engagement_score", 0))) > float(virality_threshold)
        ]

        if len(qualifying) > 0:
            selected = qualifying
            is_fallback = False
            selection_mode = "threshold"
            batch_message = f"Selected all {len(selected)} Shorts with virality scores above {virality_threshold}."
            for clip in selected:
                v_score = int(round(float(clip.get("virality_score", clip.get("engagement_score", 0)))))
                clip["passed_threshold"] = True
                clip["is_fallback"] = False
                clip["selection_reason"] = (
                    f"Virality score {v_score}/100 exceeds qualification threshold of {virality_threshold}."
                )
        else:
            selected = sorted_candidates[:min(fallback_top_k, len(sorted_candidates))]
            is_fallback = True
            selection_mode = "fallback"
            batch_message = f"No Shorts scored above {virality_threshold}. Showing the top {len(selected)} available candidates."
            for clip in selected:
                v_score = int(round(float(clip.get("virality_score", clip.get("engagement_score", 0)))))
                clip["passed_threshold"] = False
                clip["is_fallback"] = True
                clip["selection_reason"] = (
                    f"Top-{clip['candidate_rank']} fallback candidate (virality score {v_score}/100)."
                )

        # Re-index selected clips 1 to N and format titles
        for idx, clip in enumerate(selected):
            clip["index"] = idx + 1
            headline = (
                clip.get("visual_headline")
                or clip.get("headline")
                or clip.get("main_topic")
                or "Short"
            )
            clean_head = headline.strip('". ')
            clip["title"] = f"#{idx + 1} {clean_head}"
            clip["batch_message"] = batch_message
            clip["selection_mode"] = selection_mode
            clip["qualifying_count"] = len(qualifying)
            clip["total_evaluated_count"] = len(candidates)

        return {
            "selected_clips": selected,
            "selection_mode": selection_mode,
            "batch_message": batch_message,
            "qualifying_count": len(qualifying),
            "total_evaluated": len(candidates),
            "is_fallback": is_fallback,
        }

    @classmethod
    def _find_duration_targeted_spans(
        cls, cues: List[Dict[str, Any]], target_dur: float, min_dur: float, max_dur: float
    ) -> List[Dict[str, Any]]:
        """Finds candidate cue spans that end on natural sentence boundaries near target duration."""
        candidates = []

        for i in range(len(cues)):
            start_t = float(cues[i].get("start_sec", cues[i].get("start", 0.0)))
            span_text = []
            span_cues = []
            best_in_window = None
            min_dist_to_target = float("inf")

            for j in range(i, len(cues)):
                end_t = float(cues[j].get("end_sec", cues[j].get("end", 0.0)))
                dur = end_t - start_t
                span_text.append(cues[j]["text"])
                span_cues.append(cues[j])

                if dur > max_dur + 2.0:
                    break

                if min_dur <= dur <= max_dur:
                    dist = abs(dur - target_dur)
                    text_str = cues[j]["text"].strip()
                    # Bonus for ending on sentence terminator (. ! ?)
                    has_sentence_end = text_str.endswith((".", "!", "?"))
                    score_dist = dist - (0.75 if has_sentence_end else 0.0)

                    if score_dist < min_dist_to_target:
                        min_dist_to_target = score_dist
                        best_in_window = {
                            "start_sec": round(start_t, 2),
                            "end_sec": round(end_t, 2),
                            "duration_sec": round(dur, 2),
                            "spoken_text": " ".join(span_text),
                            "cues": list(span_cues),
                            "sentence_complete": has_sentence_end,
                        }

            if best_in_window:
                candidates.append(best_in_window)

        return candidates

    @classmethod
    async def _generate_and_evaluate_hooks(
        cls, span_text: str, video_title: str, duration_sec: float, llm: Any, profile: EditorialProfile
    ) -> Dict[str, Any]:
        """Generates up to 5 hook alternatives and validates them with the 21 viral hook formulas.
        Incorporates principles from yt-shorts, yt-retention, and voice guidelines.
        """
        hooks_generated: List[Dict[str, Any]] = []
        visual_headline = ""
        the_turn = ""

        # 1. Ask LLM for 4 diverse hook patterns + complementary visual headline + the turn
        prompt = (
            f"You are a master YouTube Shorts editor applying yt-shorts and yt-retention editorial principles.\n"
            f"Task: Extract a standout viral Short from this transcript slice ({duration_sec:.1f}s):\n"
            f"\"{span_text}\"\n\n"
            f"Video Topic: {video_title}\n\n"
            f"EDITORIAL RULES (yt-shorts & voice standards):\n"
            f"1. A Short must survive WITHOUT previous context. Craft a fresh, compelling opening line for mobile viewers.\n"
            f"2. Stop Hook Leak: The first 3 seconds must trigger immediate curiosity or an urgent takeaway.\n"
            f"3. Speak directly to ONE viewer ('you'). Never use banned clichés like 'unlock', 'game-changer', 'dive in', 'secret hack'.\n"
            f"4. Complementary Headline: The on-screen visual headline must use DIFFERENT words from the spoken hook.\n"
            f"5. Factual Grounding: Ground every hook strictly in what is actually spoken in this transcript.\n\n"
            f"Generate:\n"
            f"- 'visual_headline': 3-6 words, bold punchy title for on-screen badge\n"
            f"- 'the_turn': 1 sentence explaining what proves, complicates, or resolves the claim\n"
            f"- 'hooks': 4 diverse spoken hook alternatives (under 12 words each):\n"
            f"    1. Direct tension/mistake\n"
            f"    2. Contrarian flip\n"
            f"    3. Curiosity gap\n"
            f"    4. High-value educational promise\n\n"
            f"Return JSON:\n"
            f"{{\n"
            f"  \"visual_headline\": \"SHORT PUNCHY HEADLINE\",\n"
            f"  \"the_turn\": \"What complicates or proves the claim in this clip\",\n"
            f"  \"hooks\": [\n"
            f"    {{\"text\": \"...\", \"hook_type\": \"strong_direct\", \"promise\": \"...\"}},\n"
            f"    {{\"text\": \"...\", \"hook_type\": \"contrarian_flip\", \"promise\": \"...\"}},\n"
            f"    {{\"text\": \"...\", \"hook_type\": \"curiosity_gap\", \"promise\": \"...\"}},\n"
            f"    {{\"text\": \"...\", \"hook_type\": \"educational_promise\", \"promise\": \"...\"}}\n"
            f"  ]\n"
            f"}}"
        )

        try:
            res = await llm.generate_completion(
                prompt=prompt,
                system_instruction="You are an editorial quality director for YouTube Shorts. Return valid JSON only.",
                json_schema={"hooks": []},
            )
            if res.parsed_json:
                visual_headline = res.parsed_json.get("visual_headline", "").strip()
                the_turn = res.parsed_json.get("the_turn", "").strip()
                if "hooks" in res.parsed_json:
                    for item in res.parsed_json["hooks"]:
                        t = item.get("text", "").strip('".')
                        if t:
                            hooks_generated.append({
                                "text": t,
                                "hook_type": item.get("hook_type", "strong_direct"),
                                "promise": item.get("promise", ""),
                                "is_verbatim": t.lower() in span_text.lower(),
                            })
        except Exception:
            pass

        # Fallback intelligent heuristic hooks if LLM did not return candidates
        if not hooks_generated:
            sentences = [s.strip() for s in re.split(r'[.!?]', span_text) if len(s.strip()) > 12]
            core_line = sentences[0] if sentences else span_text[:70]
            core_line = re.sub(r'^(and|but|so|because|or)\s+', '', core_line, flags=re.IGNORECASE).strip()

            clean_snippet = " ".join(core_line.split()[:8])
            visual_headline = f"{video_title[:28].upper()}"

            hooks_generated = [
                {
                    "text": f"Here is what happens when you understand this: {clean_snippet}",
                    "hook_type": "curiosity_gap",
                    "promise": "Reveals the key insight from the video",
                    "is_verbatim": False,
                },
                {
                    "text": f"Why standard advice about {video_title[:30]} doesn't work",
                    "hook_type": "contrarian_flip",
                    "promise": "Challenges common assumptions",
                    "is_verbatim": False,
                },
                {
                    "text": clean_snippet,
                    "hook_type": "strong_direct",
                    "promise": "Direct spoken evidence",
                    "is_verbatim": True,
                },
            ]

        # 2. Score every candidate with the 21-formula hookscore engine
        scored_hooks = []
        for h in hooks_generated:
            score_data = ViralHookScorer.score_hook(h["text"])
            scored_hooks.append({
                "text": h["text"],
                "hook_type": h.get("hook_type", "strong_direct"),
                "is_verbatim": h.get("is_verbatim", False),
                "promise": h.get("promise", ""),
                "score": score_data["overall_score"],
                "verdict": score_data["verdict"],
                "formula_name": score_data["formula_name"],
                "weakest_link": score_data["weakest"],
                "properties": score_data.get("properties", score_data.get("metrics", {})),
                "risk_flags": [] if h.get("is_verbatim") else ["editorial_overlay_badge"],
            })

        best = max(scored_hooks, key=lambda x: x["score"])
        return {
            "best_hook": best,
            "all_hooks": scored_hooks,
            "visual_headline": visual_headline,
            "the_turn": the_turn,
        }

    @classmethod
    def _compute_editorial_scores(
        cls,
        text: str,
        hook_score: int,
        hook_formula: str,
        actual_dur: float,
        target_dur: float,
        sentence_complete: bool,
    ) -> Dict[str, Any]:
        """Calculates 6-dimension weighted score according to 01_SYSTEM_PROMPT.md Section 5."""
        words = text.lower().split()
        num_count = len(re.findall(r"\b\d+\b", text))
        q_count = text.count("?")

        # 1. Hook potential (0-100)
        s_hook = hook_score

        # 2. Standalone context (0-100)
        first_word = words[0] if words else ""
        s_context = 90 if first_word not in {"and", "also", "then", "which", "plus", "so"} else 45
        if not sentence_complete:
            s_context = max(30, s_context - 25)

        # 3. Value / Information density (0-100)
        unique_word_ratio = len(set(words)) / max(1, len(words))
        s_density = min(100, int(35 + num_count * 12 + unique_word_ratio * 40))

        # 4. Story progression (0-100)
        narrative_markers = {"because", "how", "when", "why", "after", "started", "learned", "realized"}
        prog_hits = sum(1 for w in words if w in narrative_markers)
        s_story = min(100, 45 + prog_hits * 15)

        # 5. Emotional or intellectual interest (0-100)
        interest_words = {"never", "fatal", "secret", "destroy", "crazy", "huge", "shocking", "changed", "mistake"}
        interest_hits = sum(1 for w in words if w in interest_words)
        s_interest = min(100, 40 + interest_hits * 18 + (15 if q_count > 0 else 0))

        # 6. Payoff / ending quality (0-100)
        last_phrase = text.strip().split(".")[-1].strip() if "." in text else text.strip()
        payoff_words = {"result", "solution", "now", "works", "success", "truth", "means", "better"}
        payoff_hits = sum(1 for w in last_phrase.lower().split() if w in payoff_words)
        s_payoff = min(100, 50 + (25 if sentence_complete else 0) + payoff_hits * 15)

        # Duration adherence penalty
        dur_diff = abs(actual_dur - target_dur)
        dur_penalty = min(20, int(dur_diff * 6))

        weighted_total = int(round(
            s_hook * cls.WEIGHTS["hook"]
            + s_context * cls.WEIGHTS["standalone_context"]
            + s_density * cls.WEIGHTS["information_density"]
            + s_story * cls.WEIGHTS["story_progression"]
            + s_interest * cls.WEIGHTS["interest"]
            + s_payoff * cls.WEIGHTS["payoff"]
        )) - dur_penalty

        weighted_total = max(10, min(100, weighted_total))

        # 4-Vector Virality Breakdown (0-25 each: Hook, Engagement, Value, Shareability)
        v_hook = max(5, min(25, int(round((s_hook / 100.0) * 25))))
        v_eng = max(5, min(25, int(round(((s_story * 0.5 + s_interest * 0.5) / 100.0) * 25))))
        v_val = max(5, min(25, int(round(((s_density * 0.5 + s_context * 0.5) / 100.0) * 25))))
        v_share = max(5, min(25, int(round((s_payoff / 100.0) * 25))))
        v_total = max(10, min(100, v_hook + v_eng + v_val + v_share - min(10, dur_penalty)))

        why_engaging = (
            f"Strong hook ({s_hook}/100) under formula '{hook_formula}' with standalone clarity ({s_context}/100) "
            f"and complete payoff ({s_payoff}/100). Duration variance is {dur_diff:.1f}s from {target_dur}s target."
        )

        return {
            "total_score": v_total,
            "why_engaging": why_engaging,
            "virality_breakdown": {
                "hook_score": v_hook,
                "engagement_score": v_eng,
                "value_score": v_val,
                "shareability_score": v_share,
                "total_virality": v_total,
            },
            "breakdown": {
                "hook": s_hook,
                "standalone_context": s_context,
                "information_density": s_density,
                "story_progression": s_story,
                "interest": s_interest,
                "payoff": s_payoff,
                "duration_penalty": dur_penalty,
            },
        }

    @staticmethod
    def _check_hard_rejections(
        cand: Dict[str, Any], hook: Dict[str, Any], breakdown: Dict[str, int], profile: EditorialProfile
    ) -> List[str]:
        """Evaluates hard rejection conditions from 01_SYSTEM_PROMPT.md Section 5."""
        rejections = []
        if breakdown.get("standalone_context", 100) < 40:
            rejections.append("Incomplete context or broken opening clause")
        if breakdown.get("payoff", 100) < 40:
            rejections.append("No clear ending payoff or abruptly truncated thought")
        if hook.get("score", 100) < 35:
            rejections.append("Opening hook potential is below editorial threshold")
        if not cand.get("sentence_complete", True) and profile.require_contextual_payoff:
            rejections.append("Segment cuts off mid-sentence")
        return rejections

    @staticmethod
    def _generate_content_package(
        text: str, hook: str, video_title: str, visual_headline: Optional[str] = None
    ) -> Dict[str, Any]:
        """Derives clean YouTube packaging: SEO title, description, tags, hashtags, and pinned comment."""
        clean_hook = hook.strip('".')
        topic_words = text.split()[:6]
        topic = " ".join(topic_words)
        central_idea = text[:120].strip() + "..."
        clean_h = visual_headline.strip('\".,') if visual_headline else clean_hook

        # Synthesize professional creator metadata eliminating raw transcript repetitions
        synth = YouTubeIntelligenceService.synthesize_metadata(
            text=text,
            hook=clean_h or clean_hook,
            video_title=video_title or topic,
        )

        title = f"{synth['title']} | #Shorts" if not synth['title'].endswith("#Shorts") else synth['title']
        if len(title) > 90:
            title = f"{title[:75]}... #Shorts"

        pinned_comment = f"What is your biggest takeaway from this? Let us know in the comments!"

        return {
            "topic": topic,
            "central_idea": central_idea,
            "title": title,
            "title_alternatives": synth.get("titles", []),
            "description": synth.get("description", ""),
            "hashtags": synth.get("hashtags", []),
            "tags": synth.get("tags", []),
            "pinned_comment": pinned_comment,
            "metadata_warnings": synth.get("metadata_warnings", []),
            "rationale": synth.get("rationale", ""),
        }

    @staticmethod
    def _filter_overlapping(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensures selected clips do not overlap by more than 10 seconds."""
        filtered = []
        for cand in candidates:
            overlap = False
            for existing in filtered:
                # Overlap condition: neither clip starts >10s after existing ends
                if not (cand["end_sec"] <= existing["start_sec"] + 10 or cand["start_sec"] >= existing["end_sec"] - 10):
                    overlap = True
                    break
            if not overlap:
                filtered.append(cand)
        return filtered or candidates
