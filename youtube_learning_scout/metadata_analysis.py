from __future__ import annotations

import re
from datetime import datetime, timezone

from .config import HYPE_TERMS, IMPLEMENTATION_STEP_TERMS, OFFICIAL_CHANNEL_NAMES


ISO_DURATION_PATTERN = re.compile(
    r"PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?"
)


def parse_iso8601_duration(duration: str) -> int:
    match = ISO_DURATION_PATTERN.fullmatch(duration or "")
    if not match:
        return 0

    parts = {name: int(value or 0) for name, value in match.groupdict().items()}
    return parts["hours"] * 3600 + parts["minutes"] * 60 + parts["seconds"]


def format_duration(seconds: int) -> str:
    if seconds <= 0:
        return "unknown"

    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def years_since_upload(published_at: str) -> float:
    if not published_at:
        return 999.0

    published = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return max((now - published).days / 365.25, 0.0)


def comment_signal(comments: list[str]) -> str:
    if not comments:
        return "No top comments available."

    joined = " ".join(comment.lower() for comment in comments)
    positive_terms = ["worked", "helped", "clear", "thanks", "useful", "finally", "understand"]
    negative_terms = ["outdated", "error", "doesn't work", "not work", "confusing", "broken"]

    positive_hits = sum(term in joined for term in positive_terms)
    negative_hits = sum(term in joined for term in negative_terms)

    if positive_hits > negative_hits:
        return "Top comments include signs that learners found it useful."
    if negative_hits > positive_hits:
        return "Top comments include warnings or implementation issues."
    return "Top comments are mixed or mostly neutral."


def topic_terms(topic: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-z0-9]+", topic.lower())
        if len(term) > 2 and term not in {"how", "the", "and", "for", "with"}
    }


def credibility_signal(video: dict, topic: str) -> dict:
    channel = video.get("channel_title", "").lower()
    title = video.get("title", "").lower()
    description = video.get("description", "").lower()
    transcript = (video.get("transcript") or "").lower()
    age_years = video.get("age_years", 999.0)
    visible_text = f"{title} {description}"

    score = 0.0
    notes = []

    if any(name in channel for name in OFFICIAL_CHANNEL_NAMES):
        score += 3.0
        notes.append("Channel matches the configured official/high-credibility list.")

    channel_terms = set(re.findall(r"[a-z0-9]+", channel))
    overlap = topic_terms(topic) & channel_terms
    if overlap:
        score += 1.0
        notes.append("Channel name overlaps with the topic.")

    if age_years <= 1:
        score += 1.0
        notes.append("Recently uploaded.")
    elif age_years > 3:
        notes.append("Older upload; check whether tools or APIs have changed.")

    implementation_hits = sum(term in transcript for term in IMPLEMENTATION_STEP_TERMS)
    if implementation_hits >= 3:
        score += 1.5
        notes.append("Transcript appears to include concrete implementation steps.")
    elif transcript:
        notes.append("Transcript found, but implementation detail signal is limited.")
    else:
        notes.append("Transcript unavailable, so implementation credibility is harder to verify.")

    hype_hits = [term for term in HYPE_TERMS if term in visible_text]
    if hype_hits:
        score -= 1.0
        notes.append("Title or description contains hype language.")
    else:
        score += 0.5
        notes.append("Low hype language in title and description.")

    return {
        "score": round(max(0.0, min(score, 6.0)), 1),
        "notes": notes[:4],
        "is_official_like": score >= 3.0,
    }


def score_breakdown(video: dict, level: str) -> dict:
    age_years = video.get("age_years", 999.0)
    duration_seconds = video.get("duration_seconds", 0)
    view_count = video.get("view_count", 0)
    has_transcript = bool(video.get("transcript"))
    title = video.get("title", "").lower()
    description = video.get("description", "").lower()
    text = f"{title} {description}"

    practical_usefulness = 5.0
    if any(term in text for term in ["project", "build", "tutorial", "hands-on", "roadmap"]):
        practical_usefulness += 1.5
    if view_count >= 100_000:
        practical_usefulness += 0.5

    beginner_friendliness = 5.0
    if any(term in text for term in ["beginner", "zero", "from scratch", "learn", "roadmap"]):
        beginner_friendliness += 1.5
    if level == "advanced" and any(term in text for term in ["beginner", "zero", "basics"]):
        beginner_friendliness -= 1.0
    if level == "beginner" and any(term in text for term in ["advanced", "expert", "deep dive"]):
        beginner_friendliness -= 1.5

    freshness = 5.0
    if age_years <= 1:
        freshness += 2.0
    elif age_years <= 2:
        freshness += 1.0
    elif age_years > 4:
        freshness -= 2.0

    implementation_depth = 5.0
    if 8 * 60 <= duration_seconds <= 45 * 60:
        implementation_depth += 1.0
    elif duration_seconds >= 45 * 60:
        implementation_depth += 1.5
    elif duration_seconds < 3 * 60:
        implementation_depth -= 2.0
    if has_transcript:
        implementation_depth += 0.5

    hype_penalty = 0.0
    if any(term in text for term in HYPE_TERMS):
        hype_penalty += 2.0
    if duration_seconds < 3 * 60:
        hype_penalty += 0.75

    comments = video.get("comments_signal", "")
    comment_signal_score = 5.0
    if "useful" in comments or "found it useful" in comments:
        comment_signal_score += 1.0
    elif "warnings" in comments or "issues" in comments:
        comment_signal_score -= 1.5

    raw_score = (
        practical_usefulness
        + beginner_friendliness
        + freshness
        + implementation_depth
        + comment_signal_score
        - hype_penalty
    ) / 5

    return {
        "practical_usefulness": round(max(1.0, min(practical_usefulness, 10.0)), 1),
        "beginner_friendliness": round(max(1.0, min(beginner_friendliness, 10.0)), 1),
        "freshness": round(max(1.0, min(freshness, 10.0)), 1),
        "implementation_depth": round(max(1.0, min(implementation_depth, 10.0)), 1),
        "hype_penalty": round(hype_penalty, 1),
        "comment_signal": round(max(1.0, min(comment_signal_score, 10.0)), 1),
        "overall": round(max(1.0, min(raw_score, 10.0)), 1),
    }


def metadata_score(video: dict, level: str) -> float:
    """A simple non-LLM prior. The LLM can override it with better reasoning."""
    return score_breakdown(video, level)["overall"]


def enrich_videos(videos: list[dict], level: str = "beginner", topic: str = "") -> list[dict]:
    enriched = []

    for video in videos:
        duration_seconds = parse_iso8601_duration(video.get("duration_iso", ""))
        enriched_video = {
            **video,
            "duration_seconds": duration_seconds,
            "duration_text": format_duration(duration_seconds),
            "age_years": round(years_since_upload(video.get("published_at", "")), 2),
            "comments_signal": comment_signal(video.get("top_comments", [])),
        }
        enriched_video["credibility"] = credibility_signal(enriched_video, topic)
        enriched_video["score_breakdown"] = score_breakdown(enriched_video, level)
        enriched_video["metadata_score"] = metadata_score(enriched_video, level)
        enriched.append(enriched_video)

    return enriched
