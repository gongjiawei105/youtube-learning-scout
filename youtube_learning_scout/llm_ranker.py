from __future__ import annotations

import json
import os
from typing import Any


DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def _video_payload(video: dict) -> dict:
    transcript = video.get("transcript") or ""
    comments = video.get("top_comments") or []

    return {
        "video_id": video["video_id"],
        "title": video["title"],
        "channel": video["channel_title"],
        "published_at": video["published_at"],
        "views": video.get("view_count", 0),
        "duration": video.get("duration_text", "unknown"),
        "metadata_score": video.get("metadata_score"),
        "score_breakdown": video.get("score_breakdown", {}),
        "credibility": video.get("credibility", {}),
        "comments_signal": video.get("comments_signal"),
        "transcript_excerpt": transcript[:2500],
        "top_comments": comments[:5],
    }


def _rank_sort_key(video: dict, official_first: bool) -> float:
    score = float(video.get("learning_score", video.get("metadata_score", 0)))
    if official_first:
        score += float(video.get("credibility", {}).get("score", 0)) * 0.35
    return score


def _has_official_like_video(videos: list[dict]) -> bool:
    return any(video.get("credibility", {}).get("is_official_like") for video in videos)


def _fallback_rank(
    videos: list[dict],
    official_first: bool = False,
    fallback_reason: str = "OPENAI_API_KEY was not set.",
) -> list[dict]:
    use_official_boost = official_first and _has_official_like_video(videos)
    ranked = sorted(videos, key=lambda video: _rank_sort_key(video, use_official_boost), reverse=True)
    for video in ranked:
        breakdown = video.get("score_breakdown", {})
        video["learning_score"] = video.get("metadata_score", 5.0)
        video["why_recommended"] = [
            f"Ranked with metadata-only fallback because {fallback_reason}",
            f"Practical usefulness: {breakdown.get('practical_usefulness', 'n/a')}/10.",
            f"Implementation depth: {breakdown.get('implementation_depth', 'n/a')}/10.",
            video.get("comments_signal", "No comment signal available."),
        ]
        video["warning_signs"] = _metadata_warnings(video)
        video["reasoning"] = video["why_recommended"]
    return ranked


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


def _parse_rankings(content: str) -> list[dict[str, Any]]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM did not return valid JSON: {content[:500]}") from exc

    if not isinstance(data, list):
        raise ValueError("LLM ranking response must be a JSON list.")

    return data


def rank_videos(
    topic: str,
    videos: list[dict],
    level: str = "beginner",
    official_first: bool = False,
) -> list[dict]:
    """Rank videos with an LLM when available, otherwise use metadata fallback."""
    if not os.getenv("OPENAI_API_KEY"):
        print("Note: OPENAI_API_KEY is not set. Using metadata-only fallback ranking.")
        return _fallback_rank(videos, official_first=official_first)

    try:
        from openai import OpenAI
    except ImportError:
        print("Note: OpenAI package is not installed. Using metadata-only fallback ranking.")
        return _fallback_rank(
            videos,
            official_first=official_first,
            fallback_reason="the OpenAI package is not installed.",
        )

    client = OpenAI()
    payload = [_video_payload(video) for video in videos]

    try:
        response = client.responses.create(
            model=DEFAULT_MODEL,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert technical learning evaluator. Rank YouTube videos by learning "
                        "quality, not popularity. Reward practical usefulness, beginner friendliness, "
                        "implementation depth, current information, and evidence from comments that learners "
                        "successfully applied the tutorial. Penalize hype, vague career advice, outdated content, "
                        "and shallow motivational content. Adjust your judgment for the requested learner level."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Topic: {topic}\n\n"
                        f"Learner level: {level}\n\n"
                        f"Official-first preference: {official_first}\n\n"
                        "Return ONLY JSON. The JSON must be a list of objects with keys: "
                        "video_id, learning_score, why_recommended, warning_signs. "
                        "learning_score must be 1-10. why_recommended must be a list of 2-4 concise "
                        "evidence-based bullets. warning_signs must be a list of 1-3 concise bullets.\n\n"
                        f"Videos:\n{json.dumps(payload, indent=2)}"
                    ),
                },
            ],
        )
        rankings = _parse_rankings(response.output_text)
    except Exception as exc:
        print(f"Note: LLM ranking failed ({exc}). Using metadata-only fallback ranking.")
        return _fallback_rank(
            videos,
            official_first=official_first,
            fallback_reason="LLM ranking failed.",
        )
    ranking_by_id = {item["video_id"]: item for item in rankings}

    ranked_videos = []
    for video in videos:
        ranking = ranking_by_id.get(video["video_id"])
        if not ranking:
            ranked_videos.append(
                {
                    **video,
                    "learning_score": video.get("metadata_score", 5),
                    "why_recommended": [
                        "LLM did not return a ranking for this video; using metadata fallback.",
                        video.get("comments_signal", "No comment signal available."),
                    ],
                    "warning_signs": _metadata_warnings(video),
                    "reasoning": ["LLM did not return a ranking for this video; using metadata fallback."],
                }
            )
            continue
        ranked_videos.append(
            {
                **video,
                "learning_score": ranking.get("learning_score", video.get("metadata_score", 5)),
                "why_recommended": ranking.get("why_recommended", ranking.get("reasoning", [])),
                "warning_signs": ranking.get("warning_signs", _metadata_warnings(video)),
                "reasoning": ranking.get("why_recommended", ranking.get("reasoning", [])),
            }
        )

    ranked_videos = sorted(ranked_videos, key=lambda video: float(video.get("learning_score", 0)), reverse=True)
    return _apply_official_first(ranked_videos, official_first)
