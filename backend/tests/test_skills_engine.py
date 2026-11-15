"""Tests for Unified YouTube Creator Skills Engine (Task 7).
Verifies hook scoring (yt-script), advisory title linting (yt-package),
dead-air & retake analysis (yt-edit), and viral outlier math (yt-viral).
"""

import pytest
from backend.app.services.youtube_intelligence_service import YouTubeIntelligenceService


class TestHookScoringSkill:
    """Verifies 5-property hook evaluation from yt-script/hookscore.py."""

    def test_strong_viral_hook_scores_high(self):
        hook = "Why do you waste 3 hours editing daily? Stop before you lose your channel."
        result = YouTubeIntelligenceService.score_hook(hook)
        assert result["score"] >= 70
        assert "specificity" in result["metrics"]
        assert "direct_address" in result["metrics"]
        assert "stakes" in result["metrics"]
        assert "curiosity_gap" in result["metrics"]
        assert "brevity" in result["metrics"]
        assert result["metrics"]["direct_address"] >= 70
        assert result["metrics"]["stakes"] >= 60

    def test_vague_empty_hook_scores_low(self):
        hook = "Actually basically guys welcome back today we have something really incredible."
        result = YouTubeIntelligenceService.score_hook(hook)
        assert result["score"] < 50
        assert len(result["issues"]) > 0


class TestTitleLintingSkill:
    """Verifies advisory heuristics from yt-package/title.py."""

    def test_title_within_limits_is_optimized(self):
        title = "3 Editing Hacks That Save 2 Hours"
        lint = YouTubeIntelligenceService.lint_title(title)
        assert lint["is_valid"] is True
        assert lint["chars"] <= 60
        assert lint["score"] >= 75

    def test_title_over_60_chars_is_valid_with_advisory(self):
        """Titles between 61 and 100 chars must provide advisory warnings but remain VALID."""
        title = "The Secret Psychological Reason Why Most Creators Completely Fail to Grow on YouTube in 2026"
        lint = YouTubeIntelligenceService.lint_title(title)
        assert 60 < lint["chars"] <= 100
        assert lint["is_valid"] is True  # Non-blocking advisory!
        assert any("desktop" in adv for adv in lint["advisories"])
        assert any("Mobile" in adv for adv in lint["advisories"])

    def test_title_over_100_chars_is_invalid(self):
        """Titles over 100 characters exceed platform hard limit and must be flagged invalid."""
        title = "A" * 105
        lint = YouTubeIntelligenceService.lint_title(title)
        assert lint["is_valid"] is False
        assert any("exceeds YouTube's platform hard limit" in issue for issue in lint["issues"])

    def test_thumbnail_synergy_flags_duplicate_text(self):
        title = "How to Double Your YouTube Views"
        thumbnail = "Double Your YouTube Views"
        lint = YouTubeIntelligenceService.lint_title(title, thumbnail_text=thumbnail)
        assert any("duplicates title" in adv for adv in lint["advisories"])


class TestDeadAirAnalysisSkill:
    """Verifies advisory silence and retake scanning from yt-edit/deadair.py."""

    def test_detects_dead_air_and_filler(self):
        cues = [
            {"start_sec": 0.0, "end_sec": 2.0, "text": "Here is the first point."},
            {"start_sec": 3.8, "end_sec": 4.5, "text": "um, basically"},  # 1.8s gap + filler
            {"start_sec": 4.6, "end_sec": 6.0, "text": "This is what you need to know."},
        ]
        result = YouTubeIntelligenceService.analyze_dead_air(cues, floor=1.2)
        assert result["total_cuts"] >= 2
        kinds = [c["kind"] for c in result["advisory_cuts"]]
        assert "DEAD_AIR" in kinds
        assert "FILLER" in kinds
        assert result["total_removable_sec"] > 0

    def test_detects_sentence_restart(self):
        cues = [
            {"start_sec": 0.0, "end_sec": 1.5, "text": "If you want to grow on YouTube"},
            {"start_sec": 1.6, "end_sec": 3.5, "text": "If you want to grow on TikTok today"},
        ]
        result = YouTubeIntelligenceService.analyze_dead_air(cues, floor=1.2)
        kinds = [c["kind"] for c in result["advisory_cuts"]]
        assert "RESTART" in kinds


class TestViralSwipeMetricsSkill:
    """Verifies outlier multiple and relative lift calculations from yt-viral/swipe.py."""

    def test_outlier_multiple_and_relative_lift(self):
        # 300,000 views on a channel with 100,000 median views
        metrics = YouTubeIntelligenceService.calculate_viral_metrics(
            views=300_000,
            channel_median_views=100_000,
            video_count=10,
        )
        assert metrics["valid"] is True
        assert metrics["outlier_multiple"] == 3.0
        assert metrics["relative_lift_pct"] == 200.0
        assert metrics["is_outlier"] is True
        assert metrics["is_mega_outlier"] is True

    def test_thin_channel_warning_on_under_4_videos(self):
        metrics = YouTubeIntelligenceService.calculate_viral_metrics(
            views=50_000,
            channel_median_views=25_000,
            video_count=2,  # Too few videos
        )
        assert metrics["valid"] is False
        assert "Insufficient sample size" in metrics["warning"]

    def test_hook_formula_classification(self):
        assert YouTubeIntelligenceService.classify_hook_formula("Stop making this mistake") == "Negative Constraint"
        assert YouTubeIntelligenceService.classify_hook_formula("The secret nobody talks about") == "Curiosity Gap"
        assert YouTubeIntelligenceService.classify_hook_formula("I tried this for 30 days") == "Specific Number / Timeline"


class TestTrendingAndAudioIntelligenceSkill:
    """Tests for Stage C compliant audio recommendations and content trends."""

    def test_audio_trend_recommendation_compliance(self):
        result = YouTubeIntelligenceService.recommend_trending_audio(
            niche="AI Technology",
            mood="energetic",
            pacing="fast",
        )
        assert result["target_mood"] == "energetic"
        assert len(result["recommended_tracks"]) >= 3
        # Ensure royalty free track supports direct insertion
        rf_track = next(t for t in result["recommended_tracks"] if "YouTube Audio Library" in t["artist"])
        assert rf_track["auto_insertion_supported"] is True
        # Ensure commercial track requires manual mobile selection workflow
        comm_track = next(t for t in result["recommended_tracks"] if not t["auto_insertion_supported"])
        assert "manual_workflow_instructions" in comm_track
        assert "compliance_notice" in result

    def test_content_trends_analysis(self):
        trends = YouTubeIntelligenceService.analyze_trending_topics("creator economy")
        assert len(trends["recommended_formats"]) >= 2
        assert any("Split-Screen" in f["format_name"] for f in trends["recommended_formats"])
        assert len(trends["top_hashtags"]) >= 3
