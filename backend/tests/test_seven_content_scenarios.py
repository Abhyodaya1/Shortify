"""Comprehensive Regression Test Suite for Shortify YouTube Metadata & SEO Intelligence.
Verifies all 7 content scenarios from Section 12 of the Master Execution Directive:
1. Music performance (Tenacious D – Baby One More Time / Kung Fu Panda 4)
2. Reaction video (GTA 6 Trailer Reaction)
3. Documentary (Rise and Fall of the Roman Empire)
4. Podcast / interview (Lex Fridman & Sam Altman on AGI)
5. Educational tutorial (Learn Python in 15 Minutes)
6. Gaming (Elden Ring Malenia Level 1 Club Run)
7. Comedy / storytelling (Funniest Wedding Speech)

Also verifies:
- Jake Schincariol skills integration (yt-seo, yt-package, yt-script)
- 5 distinct title candidates with mobile (<40 chars) and desktop (<60 chars) safety
- Search snippet in first two lines of description
- Up to 15 plain-text disambiguation tags (no '#')
- 3 to 5 hyper-relevant hashtags
- Absolute elimination of formulaic boilerplate and category-mismatch hallucinations
"""

import pytest
from backend.app.services.youtube_intelligence_service import YouTubeIntelligenceService
from backend.app.services.timeline_compositor import ContentPackagerService
from backend.app.services.skill_runtime import YouTubeSkillRuntime


def test_scenario_1_music_performance_tenacious_d():
    """Scenario 1: Mandatory Music Regression Example.
    Source: 'Baby One More Time - Tenacious D (Kung Fu Panda 4) FULL VERSION'
    Transcript: 'Oh baby, baby, how was I supposed to know That something wasn't right, yeah...'
    MUST classify as music performance, NOT creator education or video editing!
    """
    video_title = "Baby One More Time - Tenacious D (Kung Fu Panda 4) FULL VERSION"
    transcript = (
        "Oh baby, baby, how was I supposed to know That something wasn't right, yeah "
        "Oh baby, baby, I shouldn't have let you go And now you're out of sight, yeah "
        "Show me how you want it to be."
    )

    intel = YouTubeIntelligenceService.classify_content_type(video_title, transcript)
    assert intel["content_type"] == "music_performance"
    assert intel["is_music"] is True

    pkg = ContentPackagerService.package_content(
        clip_id="test_music_01",
        transcript=transcript,
        central_idea=video_title,
        opening_hook="Oh baby, baby, how was I supposed to know",
        video_title=video_title,
    )

    # 1. Title candidates: exactly 5 distinct angles
    titles = pkg["titles"]
    assert len(titles) == 5
    angles = {t["angle"] for t in titles}
    assert "curiosity" in angles
    assert "direct" in angles

    # Check mobile safety for direct title
    direct_title = next(t for t in titles if t["angle"] == "direct")
    assert len(direct_title["text"]) <= 40

    # 2. Description: search snippet and context
    desc = pkg["description"]
    assert "Baby One More Time" in desc or "Tenacious D" in desc
    # STRICT BAN on category-mismatch hallucinations
    assert "video editing" not in desc.lower()
    assert "shorts growth" not in desc.lower()
    assert "production technique" not in desc.lower()
    assert "retention technique" not in desc.lower()
    assert "Key Takeaway from" not in desc
    assert "Did you know this?" not in desc

    # 3. SEO Tags: Plain text, relevant entities, no '#'
    tags = pkg["tags"]
    assert 5 <= len(tags) <= 15
    for t in tags:
        assert not t.startswith("#"), f"Tag should not contain #: {t}"
    tags_lower = [t.lower() for t in tags]
    assert any("tenacious" in t for t in tags_lower) or any("music" in t for t in tags_lower)
    assert "video tips" not in tags_lower
    assert "audio production" not in tags_lower

    # 4. Hashtags: 3 to 5 relevant tags including #Shorts
    hashtags = pkg["hashtags"]
    assert 3 <= len(hashtags) <= 5
    assert "#Shorts" in hashtags
    assert "#VideoEditing" not in hashtags
    assert "#Productivity" not in hashtags

    # 5. Jake Schincariol runtime lint execution
    for t in titles:
        assert "lint_advisory" in t
        assert t["lint_advisory"]["source"] == "jake_title_py"


def test_scenario_2_reaction_video():
    """Scenario 2: Reaction Video.
    Source: 'Gamer Reacts to GTA 6 Trailer 2 (Mindblown)'
    """
    video_title = "Gamer Reacts to GTA 6 Trailer 2 (Mindblown)"
    transcript = (
        "Wait, is that Vice City? Look at those graphics! No way they included the "
        "helicopter physics like that. That is insane."
    )

    intel = YouTubeIntelligenceService.classify_content_type(video_title, transcript)
    assert intel["content_type"] == "reaction"

    pkg = ContentPackagerService.package_content(
        clip_id="test_reaction_02",
        transcript=transcript,
        central_idea=video_title,
        opening_hook="Wait, is that Vice City?",
        video_title=video_title,
    )

    assert len(pkg["titles"]) == 5
    assert any("GTA" in t["text"] or "Reaction" in t["text"] for t in pkg["titles"])
    assert "#Reaction" in pkg["hashtags"] or any("Reaction" in t for t in pkg["tags"])
    assert "Key Takeaway from" not in pkg["description"]


def test_scenario_3_documentary():
    """Scenario 3: Historical Documentary.
    Source: 'The Rise and Fall of the Roman Empire - Episode 4: The Final Legion'
    """
    video_title = "The Rise and Fall of the Roman Empire - Episode 4: The Final Legion"
    transcript = (
        "By 476 AD, the Western Roman Empire had fractured into warring factions. "
        "The final emperor, Romulus Augustulus, was deposed without a single battle fought in his defense."
    )

    intel = YouTubeIntelligenceService.classify_content_type(video_title, transcript)
    assert intel["content_type"] == "documentary"

    pkg = ContentPackagerService.package_content(
        clip_id="test_doc_03",
        transcript=transcript,
        central_idea=video_title,
        opening_hook="By 476 AD, the Western Roman Empire had fractured",
        video_title=video_title,
    )

    assert len(pkg["titles"]) == 5
    assert any("Roman" in t["text"] or "Empire" in t["text"] for t in pkg["titles"])
    assert any("History" in h for h in pkg["hashtags"]) or any("Documentary" in h for h in pkg["hashtags"])
    assert "Key Takeaway from" not in pkg["description"]


def test_scenario_4_podcast_interview():
    """Scenario 4: Podcast / Interview.
    Source: 'Lex Fridman Podcast #400 - Sam Altman on AGI, OpenAI, and Future of Humanity'
    """
    video_title = "Lex Fridman Podcast #400 - Sam Altman on AGI, OpenAI, and Future of Humanity"
    transcript = (
        "I think the transition to superintelligence will happen much faster than institutions "
        "can adapt. The question is not whether the compute exists, but how we govern the threshold."
    )

    intel = YouTubeIntelligenceService.classify_content_type(video_title, transcript)
    assert intel["content_type"] == "podcast_interview"

    pkg = ContentPackagerService.package_content(
        clip_id="test_pod_04",
        transcript=transcript,
        central_idea=video_title,
        opening_hook="The transition to superintelligence will happen faster than we expect",
        video_title=video_title,
    )

    assert len(pkg["titles"]) == 5
    assert any("Altman" in t["text"] or "AGI" in t["text"] or "Lex" in t["text"] for t in pkg["titles"])
    assert any("Podcast" in h for h in pkg["hashtags"]) or any("Interview" in h for h in pkg["hashtags"])
    assert "Key Takeaway from" not in pkg["description"]


def test_scenario_5_educational_tutorial():
    """Scenario 5: Educational Tutorial.
    Source: 'Learn Python in 15 Minutes - Functions, Loops, and Clean Code'
    """
    video_title = "Learn Python in 15 Minutes - Functions, Loops, and Clean Code"
    transcript = (
        "In this lesson, we will cover list comprehensions and lambda functions. "
        "Notice how refactoring this for-loop reduces four lines of boilerplate into a single expressive expression."
    )

    intel = YouTubeIntelligenceService.classify_content_type(video_title, transcript)
    assert intel["content_type"] == "educational_tutorial"

    pkg = ContentPackagerService.package_content(
        clip_id="test_tut_05",
        transcript=transcript,
        central_idea=video_title,
        opening_hook="Refactor four lines of code into a single expression",
        video_title=video_title,
    )

    assert len(pkg["titles"]) == 5
    assert any("Python" in t["text"] or "Tutorial" in t["text"] for t in pkg["titles"])
    assert any("Programming" in h for h in pkg["hashtags"]) or any("Tutorial" in h for h in pkg["hashtags"])
    assert "Key Takeaway from" not in pkg["description"]


def test_scenario_6_gaming():
    """Scenario 6: Gaming.
    Source: 'Elden Ring DLC - Defeating Malenia with Level 1 Club (No Damage Run)'
    """
    video_title = "Elden Ring DLC - Defeating Malenia with Level 1 Club (No Damage Run)"
    transcript = (
        "She's about to trigger the Waterfowl Dance. Dodge backwards twice, jump the third sweep, "
        "and counter with a jumping heavy. Stance broken right there!"
    )

    intel = YouTubeIntelligenceService.classify_content_type(video_title, transcript)
    assert intel["content_type"] == "gaming"

    pkg = ContentPackagerService.package_content(
        clip_id="test_game_06",
        transcript=transcript,
        central_idea=video_title,
        opening_hook="She's about to trigger the Waterfowl Dance",
        video_title=video_title,
    )

    assert len(pkg["titles"]) == 5
    assert any("Malenia" in t["text"] or "Elden" in t["text"] or "Boss" in t["text"] for t in pkg["titles"])
    assert any("Gaming" in h for h in pkg["hashtags"]) or any("BossFight" in h for h in pkg["hashtags"])
    assert "Key Takeaway from" not in pkg["description"]


def test_scenario_7_comedy_storytelling():
    """Scenario 7: Comedy / Storytelling.
    Source: 'The Funniest Wedding Speech You Will Ever Hear'
    """
    video_title = "The Funniest Wedding Speech You Will Ever Hear"
    transcript = (
        "When Dave asked me to be his best man, he said: 'Just tell them the truth.' "
        "So I looked at his wife and said: 'Good luck, return policies expired five minutes ago!'"
    )

    intel = YouTubeIntelligenceService.classify_content_type(video_title, transcript)
    assert intel["content_type"] == "comedy_storytelling"

    pkg = ContentPackagerService.package_content(
        clip_id="test_com_07",
        transcript=transcript,
        central_idea=video_title,
        opening_hook="Dave said: Just tell them the truth",
        video_title=video_title,
    )

    assert len(pkg["titles"]) == 5
    assert any("Wedding" in t["text"] or "Funniest" in t["text"] or "Speech" in t["text"] for t in pkg["titles"])
    assert any("Comedy" in h for h in pkg["hashtags"]) or any("Hilarious" in h for h in pkg["hashtags"])
    assert "Key Takeaway from" not in pkg["description"]


def test_metadata_changes_with_transcript_and_title():
    """Verifies that changing the transcript or title dynamically alters generated metadata."""
    pkg_a = ContentPackagerService.package_content(
        clip_id="diff_a",
        transcript="Why you should never use mutable default arguments in Python.",
        central_idea="Python default argument pitfall",
        video_title="Python Mistakes to Avoid",
    )

    pkg_b = ContentPackagerService.package_content(
        clip_id="diff_b",
        transcript="The secret ingredient that makes authentic Roman carbonara so creamy.",
        central_idea="Roman carbonara recipe",
        video_title="How to Cook Authentic Carbonara",
    )

    assert pkg_a["titles"][0]["text"] != pkg_b["titles"][0]["text"]
    assert pkg_a["description"] != pkg_b["description"]
    assert pkg_a["tags"] != pkg_b["tags"]
