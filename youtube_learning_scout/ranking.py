from __future__ import annotations


def _rank_sort_key(video: dict, official_first: bool) -> float:
    score = float(video.get("learning_score", video.get("metadata_score", 0)))
    if official_first:
        score += float(video.get("credibility", {}).get("score", 0)) * 0.35
    return score


def _has_official_like_video(videos: list[dict]) -> bool:
    return any(video.get("credibility", {}).get("is_official_like") for video in videos)


def _metadata_warnings(video: dict) -> list[str]:
    warnings = []
    breakdown = video.get("score_breakdown", {})

    if video.get("age_years", 0) > 3:
        warnings.append("May be outdated for fast-moving technical topics.")
    if not video.get("transcript"):
        warnings.append("Transcript unavailable, so content depth is harder to verify.")
    if breakdown.get("hype_penalty", 0) > 0:
        warnings.append("Title or description contains possible hype signals.")
    if video.get("duration_seconds", 0) < 3 * 60:
        warnings.append("Very short video; may be shallow.")

    return warnings or ["No major warning signs from metadata."]


def _why_recommended(video: dict) -> list[str]:
    breakdown = video.get("score_breakdown", {})
    reasons = [
        f"Practical usefulness {breakdown.get('practical_usefulness', 'n/a')}/10, "
        f"implementation depth {breakdown.get('implementation_depth', 'n/a')}/10.",
        f"Freshness {breakdown.get('freshness', 'n/a')}/10 "
        f"(uploaded about {video.get('age_years', 'n/a')} years ago).",
    ]

    credibility_notes = video.get("credibility", {}).get("notes", [])
    if credibility_notes:
        reasons.append(credibility_notes[0])

    reasons.append(video.get("comments_signal", "No comment signal available."))
    return reasons


def _apply_official_first(ranked_videos: list[dict], official_first: bool) -> list[dict]:
    if not official_first:
        return ranked_videos

    if not _has_official_like_video(ranked_videos):
        for video in ranked_videos:
            notes = video.setdefault("credibility", {}).setdefault("notes", [])
            fallback_note = "No official-looking video found; using normal learning-quality ranking."
            if fallback_note not in notes:
                notes.append(fallback_note)
        return ranked_videos

    return sorted(ranked_videos, key=lambda video: _rank_sort_key(video, True), reverse=True)


def rank_videos(
    topic: str,
    videos: list[dict],
    level: str = "beginner",
    official_first: bool = False,
) -> list[dict]:
    """Rank videos deterministically from metadata signals.

    This engine does no AI inference. It computes transparent metadata scores and
    surfaces raw signals (transcript excerpt, top comments, score breakdown,
    credibility notes) in the report. The qualitative ranking and final judgment
    are meant to be done by the agent reading the report (Claude Code, Codex, etc.),
    which avoids paid API calls and keeps the engine free and reproducible.
    """
    use_official_boost = official_first and _has_official_like_video(videos)
    ranked = sorted(videos, key=lambda video: _rank_sort_key(video, use_official_boost), reverse=True)

    for video in ranked:
        video["learning_score"] = video.get("metadata_score", 5.0)
        video["why_recommended"] = _why_recommended(video)
        video["warning_signs"] = _metadata_warnings(video)
        video["reasoning"] = video["why_recommended"]

    return _apply_official_first(ranked, official_first)
