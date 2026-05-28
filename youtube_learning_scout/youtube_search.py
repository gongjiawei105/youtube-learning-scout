from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


@dataclass
class YouTubeConfig:
    api_key: str
    include_comments: bool = True
    include_transcripts: bool = True
    max_comments: int = 5


def _get_config() -> YouTubeConfig:
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing YOUTUBE_API_KEY. Create a YouTube Data API key and set it as an environment variable."
        )

    return YouTubeConfig(
        api_key=api_key,
        include_comments=os.getenv("YLS_INCLUDE_COMMENTS", "true").lower() == "true",
        include_transcripts=os.getenv("YLS_INCLUDE_TRANSCRIPTS", "true").lower() == "true",
    )


def _youtube_client(api_key: str) -> Any:
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError("Missing dependency: run `pip install -r requirements.txt`.") from exc

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=api_key)


def _search_video_ids(youtube: Any, topic: str, max_results: int) -> list[str]:
    response = (
        youtube.search()
        .list(
            q=topic,
            part="id",
            type="video",
            maxResults=max_results,
            order="relevance",
            safeSearch="moderate",
        )
        .execute()
    )

    return [item["id"]["videoId"] for item in response.get("items", [])]


def _fetch_video_details(youtube: Any, video_ids: list[str]) -> list[dict]:
    if not video_ids:
        return []

    response = (
        youtube.videos()
        .list(
            id=",".join(video_ids),
            part="snippet,contentDetails,statistics",
        )
        .execute()
    )

    videos = []
    for item in response.get("items", []):
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})
        video_id = item["id"]

        videos.append(
            {
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "published_at": snippet.get("publishedAt", ""),
                "duration_iso": content_details.get("duration", ""),
                "view_count": int(statistics.get("viewCount", 0)),
                "like_count": int(statistics.get("likeCount", 0)),
                "comment_count": int(statistics.get("commentCount", 0)),
            }
        )

    return videos


def _fetch_transcript(video_id: str, max_chars: int = 6000) -> str | None:
    try:
        from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi
    except Exception:
        return None

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
    except (NoTranscriptFound, TranscriptsDisabled):
        return None
    except Exception:
        return None

    text = " ".join(segment.get("text", "") for segment in transcript)
    return text[:max_chars]


def _fetch_top_comments(youtube: Any, video_id: str, max_comments: int) -> list[str]:
    try:
        response = (
            youtube.commentThreads()
            .list(
                videoId=video_id,
                part="snippet",
                maxResults=max_comments,
                order="relevance",
                textFormat="plainText",
            )
            .execute()
        )
    except Exception:
        return []

    comments = []
    for item in response.get("items", []):
        snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
        text = snippet.get("textDisplay", "").strip()
        if text:
            comments.append(text[:800])

    return comments


def search_youtube(topic: str, max_results: int = 10) -> list[dict]:
    """Search YouTube and return video metadata plus optional transcripts/comments."""
    config = _get_config()
    youtube = _youtube_client(config.api_key)

    video_ids = _search_video_ids(youtube, topic, max_results)
    videos = _fetch_video_details(youtube, video_ids)

    for video in videos:
        video_id = video["video_id"]
        video["transcript"] = _fetch_transcript(video_id) if config.include_transcripts else None
        video["transcript_status"] = "available" if video["transcript"] else "unavailable"
        video["top_comments"] = (
            _fetch_top_comments(youtube, video_id, config.max_comments) if config.include_comments else []
        )

    return videos
