---
name: youtube-learning-scout
description: Evaluate YouTube videos as learning resources for technical topics using the local YouTube Learning Scout CLI. Use when a user asks to find, rank, compare, or inspect YouTube tutorials/courses/videos for learning quality, beginner fit, practical depth, credibility, official-source preference, or bad-ranking evaluation notes.
---

# YouTube Learning Scout

## Overview

Use the local `youtube-learning-scout` command to search YouTube, rank videos by learning quality, and produce a Markdown report. Treat this as an evaluation workflow, not a general recommendation engine.

Use the repository directory where the user cloned `youtube-learning-scout` when you need to inspect source files, copy the skill, or update `evaluation_notes.md`.

## Workflow

1. Confirm the topic, learner level, and whether `--official-first` should be used. If unspecified, choose:
   - `--level beginner` for onboarding/tutorial queries.
   - `--level intermediate` for build/project queries.
   - `--official-first` for tools, APIs, SDKs, vendors, or official product workflows.

2. Check whether `YOUTUBE_API_KEY` is available before running. Do not ask the user to paste secrets into chat. If the key is missing, explain that it must be set as an environment variable.

3. Run the installed command:

```bash
youtube-learning-scout --topic "Claude Code skills" --max-results 10 --level beginner --official-first
```

4. Read the generated Markdown report from the `outputs/` folder relative to the current working directory.

5. Summarize the top recommendations with:
   - top result and why it ranked
   - warning signs
   - whether official-first changed the ranking
   - whether transcript/comment gaps weakened confidence

6. If rankings look wrong or debatable, append a case to `evaluation_notes.md` in the repo root. If that file does not exist, copy the structure from `evaluation_notes.example.md`.

Use this shape:

```text
Date:
Topic:
Command:
Expected useful video:
Actual top result:
Failure type:
Likely fix:
Notes:
```

## Good Defaults

Use these examples as patterns:

```bash
youtube-learning-scout --topic "Claude Code skills" --max-results 10 --level beginner --official-first
youtube-learning-scout --topic "Codex IDE extension tutorial" --max-results 10 --level beginner --official-first
youtube-learning-scout --topic "build RAG app with Python" --max-results 10 --level intermediate
```

## Interpretation Rules

- Do not treat the top score as absolute truth.
- Treat missing transcripts as lower confidence for implementation-depth claims.
- Treat comments as weak evidence; comments can be noisy or unavailable.
- Use `--official-first` as a heuristic, not proof of quality.
- Prefer recording repeated failure modes over making one-off scoring changes.
- If `OPENAI_API_KEY` is missing, that is fine. The CLI uses metadata-only fallback ranking; Codex/Claude can still inspect the report.

## Setup Help

If the command is missing, recommend `pipx` for normal users:

```bash
pipx install git+https://github.com/gongjiawei105/youtube-learning-scout.git
```

If `pipx` is not available, use a user install:

```bash
python -m pip install --user git+https://github.com/gongjiawei105/youtube-learning-scout.git
```

Set `YOUTUBE_API_KEY` locally.

macOS/Linux:

```bash
export YOUTUBE_API_KEY="your-youtube-api-key"
```

Windows PowerShell:

```powershell
$env:YOUTUBE_API_KEY="your-youtube-api-key"
```

Windows persistent:

```powershell
setx YOUTUBE_API_KEY "your-youtube-api-key"
```

Never write API keys into project files or skill files.
