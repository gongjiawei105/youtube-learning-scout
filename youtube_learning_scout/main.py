from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from .metadata_analysis import enrich_videos
from .ranking import rank_videos
from .youtube_search import search_youtube


SAMPLE_TOPIC = "how to build AI skills"
MAX_RESULTS = 10
PRINT_LIMIT = 5
OUTPUT_DIR = Path("outputs")
LEVELS = ("beginner", "intermediate", "advanced")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank YouTube videos by learning quality.")
    parser.add_argument("--topic", default=SAMPLE_TOPIC, help="Learning topic to search for.")
    parser.add_argument("--max-results", type=int, default=MAX_RESULTS, help="Number of YouTube results to inspect.")
    parser.add_argument(
        "--level",
        choices=LEVELS,
        default="beginner",
        help="Learner level to optimize recommendations for.",
    )
    parser.add_argument(
        "--official-first",
        action="store_true",
        help="Prefer official or high-credibility channels when credible matches are available.",
    )
    return parser.parse_args()


def format_score_breakdown(video: dict, indent: str = "   ") -> list[str]:
    breakdown = video.get("score_breakdown", {})
    return [
        f"{indent}- Practical usefulness: {breakdown.get('practical_usefulness', 'n/a')}/10",
        f"{indent}- Beginner friendliness: {breakdown.get('beginner_friendliness', 'n/a')}/10",
        f"{indent}- Freshness: {breakdown.get('freshness', 'n/a')}/10",
        f"{indent}- Implementation depth: {breakdown.get('implementation_depth', 'n/a')}/10",
        f"{indent}- Hype penalty: {breakdown.get('hype_penalty', 'n/a')}",
        f"{indent}- Comment signal: {breakdown.get('comment_signal', 'n/a')}/10",
    ]


def format_credibility_notes(video: dict, indent: str = "   ") -> list[str]:
    credibility = video.get("credibility", {})
    score = credibility.get("score", "n/a")
    notes = credibility.get("notes", [])
    lines = [f"{indent}- Credibility score: {score}/6"]
    lines.extend(f"{indent}- {note}" for note in notes[:4])
    return lines


def format_raw_signals(video: dict, transcript_chars: int = 800, max_comments: int = 5) -> list[str]:
    """Raw, un-scored evidence the reading agent can use to form its own judgment."""
    lines: list[str] = []

    transcript = (video.get("transcript") or "").strip()
    lines.append("**Transcript excerpt:**")
    lines.append("")
    if transcript:
        excerpt = transcript[:transcript_chars].replace("\n", " ")
        suffix = "..." if len(transcript) > transcript_chars else ""
        lines.append(f"> {excerpt}{suffix}")
    else:
        lines.append("> Transcript unavailable.")
    lines.append("")

    comments = video.get("top_comments") or []
    lines.append("**Top comments:**")
    lines.append("")
    if comments:
        for comment in comments[:max_comments]:
            lines.append(f"- {comment.replace(chr(10), ' ')}")
    else:
        lines.append("- No top comments available.")

    return lines


def format_terminal_report(
    topic: str,
    level: str,
    ranked_videos: list[dict],
    official_first: bool = False,
    limit: int = PRINT_LIMIT,
) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    visible_videos = ranked_videos[:limit]
    lines = [
        "YouTube Learning Scout",
        "=" * 23,
        f"Topic: {topic}",
        f"Level: {level}",
        f"Official-first: {official_first}",
        f"Generated: {generated_at}",
        f"Showing top {len(visible_videos)} of {len(ranked_videos)} ranked videos",
        "",
    ]

    for index, video in enumerate(visible_videos, start=1):
        score = video.get("learning_score", "n/a")
        reasons = video.get("why_recommended", [])
        warnings = video.get("warning_signs", [])
        comments_signal = video.get("comments_signal", "No comment signal available.")
        transcript_status = video.get("transcript_status", "unknown")

        lines.extend(
            [
                f"{index}. {video['title']}",
                f"   Score: {score}/10",
                f"   Channel: {video['channel_title']}",
                f"   Published: {video['published_at'][:10]}",
                f"   Views: {video.get('view_count', 0):,}",
                f"   Duration: {video.get('duration_text', 'unknown')}",
                f"   Transcript: {transcript_status}",
                f"   URL: {video['url']}",
                f"   Comments: {comments_signal}",
                "   Why recommended:",
            ]
        )

        if reasons:
            for reason in reasons:
                lines.append(f"   - {reason}")
        else:
            lines.append("   - No recommendation reasoning returned.")

        lines.append("   Warning signs:")
        if warnings:
            for warning in warnings:
                lines.append(f"   - {warning}")
        else:
            lines.append("   - No warning signs returned.")

        lines.append("   Scoring explanation:")
        lines.extend(format_score_breakdown(video))
        lines.append("   Credibility notes:")
        lines.extend(format_credibility_notes(video))

        lines.append("")

    return "\n".join(lines)


def format_markdown_report(
    topic: str,
    level: str,
    ranked_videos: list[dict],
    official_first: bool = False,
) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# YouTube Learning Scout Report",
        "",
        f"- Topic: {topic}",
        f"- Level: {level}",
        f"- Official-first: {official_first}",
        f"- Generated: {generated_at}",
        f"- Videos ranked: {len(ranked_videos)}",
        "",
        "> Scores below come from a deterministic metadata heuristic, not from AI.",
        "> Use the **Raw Signals** (transcript excerpt + top comments) under each video to",
        "> form your own qualitative ranking. Treat the heuristic score as a prior, not a verdict.",
        "",
    ]

    for index, video in enumerate(ranked_videos, start=1):
        score = video.get("learning_score", "n/a")
        reasons = video.get("why_recommended", [])
        warnings = video.get("warning_signs", [])
        transcript_status = video.get("transcript_status", "unknown")

        lines.extend(
            [
                f"## {index}. {video['title']}",
                "",
                f"- Score: {score}/10",
                f"- Channel: {video['channel_title']}",
                f"- Published: {video['published_at'][:10]}",
                f"- Views: {video.get('view_count', 0):,}",
                f"- Duration: {video.get('duration_text', 'unknown')}",
                f"- Transcript: {transcript_status}",
                f"- URL: {video['url']}",
                f"- Comments: {video.get('comments_signal', 'No comment signal available.')}",
                "",
                "### Why Recommended",
                "",
            ]
        )

        lines.extend(f"- {reason}" for reason in reasons or ["No recommendation reasoning returned."])
        lines.extend(["", "### Warning Signs", ""])
        lines.extend(f"- {warning}" for warning in warnings or ["No warning signs returned."])
        lines.extend(["", "### Scoring Explanation", ""])
        lines.extend(format_score_breakdown(video, indent=""))
        lines.extend(["", "### Credibility Notes", ""])
        lines.extend(format_credibility_notes(video, indent=""))
        lines.extend(["", "### Raw Signals", ""])
        lines.extend(format_raw_signals(video))
        lines.append("")

    return "\n".join(lines)


def save_markdown_report(report: str, topic: str, level: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    slug = "".join(char if char.isalnum() else "_" for char in topic.lower()).strip("_")
    path = OUTPUT_DIR / f"{slug}_{level}_ranked_report.md"
    path.write_text(report, encoding="utf-8")
    return path


def main() -> None:
    args = parse_args()
    topic = args.topic.strip()
    max_results = max(1, args.max_results)
    level = args.level
    official_first = args.official_first

    if not topic:
        raise SystemExit("Error: --topic cannot be empty.")

    print(f"Searching YouTube for: {topic!r} ({level}, max {max_results}, official-first={official_first})")
    try:
        videos = search_youtube(topic=topic, max_results=max_results)
    except RuntimeError as exc:
        raise SystemExit(f"Error: {exc}") from exc

    if not videos:
        raise SystemExit(
            "Error: no videos found. Try a broader topic, check your YouTube API key, or reduce filters."
        )

    unavailable_transcripts = sum(1 for video in videos if video.get("transcript_status") == "unavailable")
    if unavailable_transcripts:
        print(
            f"Note: transcript unavailable for {unavailable_transcripts} of {len(videos)} videos; continuing."
        )

    print(f"Retrieved {len(videos)} videos. Analyzing metadata...")
    enriched_videos = enrich_videos(videos, level=level, topic=topic)

    print("Ranking videos...")
    ranked_videos = rank_videos(
        topic=topic,
        videos=enriched_videos,
        level=level,
        official_first=official_first,
    )

    terminal_report = format_terminal_report(
        topic=topic,
        level=level,
        ranked_videos=ranked_videos,
        official_first=official_first,
    )
    markdown_report = format_markdown_report(
        topic=topic,
        level=level,
        ranked_videos=ranked_videos,
        official_first=official_first,
    )
    output_path = save_markdown_report(markdown_report, topic, level)

    print()
    print(terminal_report)
    print(f"Saved report to: {output_path}")


if __name__ == "__main__":
    main()
