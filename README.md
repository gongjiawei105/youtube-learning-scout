# YouTube Learning Scout

A small Python CLI that searches YouTube for technical learning topics and ranks videos by learning quality.

This is not a general recommendation engine. It is an AI-assisted learning quality evaluator with an explicit human review loop.

## Quick Start

Install from GitHub:

```bash
pip install git+https://github.com/gongjiawei105/youtube-learning-scout.git
```

Set your YouTube Data API key.

macOS/Linux:

```bash
export YOUTUBE_API_KEY="your-youtube-api-key"
```

Windows PowerShell:

```powershell
$env:YOUTUBE_API_KEY="your-youtube-api-key"
```

Run:

```bash
youtube-learning-scout --topic "build RAG app with Python" --level intermediate
```

The command prints the top 5 ranked videos and saves a Markdown report to `outputs/` relative to the current working directory.

## Install as a Claude Code Skill

This repo includes a portable Claude Code skill wrapper at:

```text
skills/youtube-learning-scout/SKILL.md
```

Install it into your personal Claude Code skills folder.

macOS/Linux:

```bash
mkdir -p ~/.claude/skills
cp -r skills/youtube-learning-scout ~/.claude/skills/
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force $env:USERPROFILE\.claude\skills
Copy-Item -Recurse skills\youtube-learning-scout $env:USERPROFILE\.claude\skills\
```

Restart Claude Code, then ask:

```text
Use YouTube Learning Scout to find beginner videos for Claude Code skills.
```

Claude should run the local CLI, inspect the generated Markdown report, and help update `evaluation_notes.md` when rankings look wrong.

## What It Does

- Searches YouTube for a topic
- Retrieves video metadata
- Attempts to collect transcripts
- Attempts to collect top comments
- Scores practical usefulness, beginner friendliness, freshness, implementation depth, hype penalty, comment signal, and credibility
- Supports `--official-first` to prefer official/high-credibility sources when available
- Prints the top 5 ranked videos in the terminal
- Saves a Markdown report to `outputs/`

## Local Development

From a local clone:

```bash
python -m venv .venv
pip install -e .
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

Optional LLM ranking:

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

If `OPENAI_API_KEY` is not set, the tool still runs using metadata-only fallback ranking. This is the recommended MVP workflow when you plan to inspect reports with Codex or Claude Code.

Optional settings:

```bash
export OPENAI_MODEL="gpt-4.1-mini"
export YLS_INCLUDE_COMMENTS="true"
export YLS_INCLUDE_TRANSCRIPTS="true"
```

## Usage

```bash
youtube-learning-scout --topic "learn python fast" --max-results 10 --level beginner
```

```bash
youtube-learning-scout --topic "build rag apps with python" --max-results 8 --level intermediate
```

```bash
youtube-learning-scout --topic "advanced pytorch optimization" --max-results 12 --level advanced
```

Prefer official or high-credibility sources when available:

```bash
youtube-learning-scout --topic "Claude Code skills" --max-results 10 --level beginner --official-first
```

Options:

- `--topic`: YouTube search topic
- `--max-results`: number of videos to retrieve before ranking
- `--level`: `beginner`, `intermediate`, or `advanced`
- `--official-first`: nudges the ranking toward official or high-credibility channels when credible matches are available

## Report Fields

Each ranked video includes:

- Why recommended
- Warning signs
- Practical usefulness score
- Beginner friendliness score
- Freshness score
- Implementation depth score
- Hype penalty
- Comment signal score, when comments are available
- Credibility notes

## Sample Output

Fake example data:

```text
YouTube Learning Scout
=======================
Topic: Claude Code skills
Level: beginner
Official-first: True
Generated: 2026-05-28 03:10 UTC
Showing top 2 of 10 ranked videos

1. Claude Code for Beginners: Build a Small Tool
   Score: 8.2/10
   Channel: Anthropic
   Published: 2026-03-14
   Views: 128,400
   Duration: 18m 42s
   Transcript: available
   URL: https://www.youtube.com/watch?v=example1
   Comments: Top comments include signs that learners found it useful.
   Why recommended:
   - Official-looking channel with a recent upload.
   - Transcript includes setup, command-line usage, and implementation steps.
   Warning signs:
   - Assumes some comfort with terminal commands.
```

## Credibility Checks

The `--official-first` option uses a small configurable list in `youtube_learning_scout/config.py` plus simple heuristics:

- Official/high-credibility channel match
- Channel name relevance to the topic
- Recent upload date
- Transcript contains concrete implementation steps
- Low hype language in the title and description

If no official-looking video is found, the tool keeps the normal learning-quality ranking and notes the fallback in the report.

## Evaluation Workflow

Use `evaluation_notes.md` to record bad or surprising recommendations. This file is ignored by git so personal evaluation history is not committed by accident.

Start from the template:

```bash
cp evaluation_notes.example.md evaluation_notes.md
```

Record cases like:

```text
Topic:
Expected useful video:
Actual top result:
Failure type:
Likely fix:
```

The best improvements should come from repeated failure modes, not from adding features blindly.

## Project Structure

```text
youtube-learning-scout/
|-- youtube_learning_scout/
|   |-- __init__.py
|   |-- main.py
|   |-- youtube_search.py
|   |-- metadata_analysis.py
|   |-- llm_ranker.py
|   `-- config.py
|-- skills/
|   `-- youtube-learning-scout/
|       `-- SKILL.md
|-- prompts/
|   `-- ranking_prompt.md
|-- evaluation_notes.example.md
|-- pyproject.toml
|-- requirements.txt
|-- LICENSE
|-- CONTRIBUTING.md
`-- README.md
```

## Known Limitations

- YouTube metadata is imperfect and can be missing, stale, or misleading.
- Comments and transcripts may be unavailable, disabled, blocked, or incomplete.
- Popularity is not the same as learning quality.
- `--official-first` is only a heuristic, not proof that a video is authoritative or best for learning.

## Notes

- YouTube comments may be disabled for some videos.
- Transcripts may not exist or may be blocked.
- Transcript lookup uses `youtube-transcript-api` and fails gracefully.
- The YouTube Data API has quotas.
- The code is intentionally small and easy to modify.
