# Evaluation Notes

Use this file to collect bad or surprising rankings. Do not tune the scoring or prompt from one example unless the failure is obvious. Look for repeated patterns across 10-20 cases.

## Evaluation Loop

```text
run -> inspect bad ranking -> identify failure mode -> adjust scoring/prompt -> rerun
```

## Cases

### Case 1

```text
Date: 2026-05-28
Topic: Claude Code skills
Command: python main.py --topic "Claude Code skills" --max-results 10 --level beginner --official-first
Expected useful video: Ideally an official Anthropic video or a clear beginner walkthrough with setup and concrete examples.
Actual top result: I Tried 100+ Claude Code Skills. These 6 Are The Best
Failure type: Possible hype/popularity over practical beginner instruction.
Likely fix: Strengthen hype penalty for titles with patterns like "100+", "1%", "master 95%", "lasts forever"; reward terms like "beginner", "setup", "tutorial", and "walkthrough" when supported by metadata/transcripts.
Notes: YouTube API worked. All 10 transcripts were unavailable, so ranking relied on metadata and comments. OPENAI_API_KEY was not set, so this used metadata-only fallback ranking. Official-first did not find an official-looking source among the retrieved videos.
```

### Case 2

```text
Date: 2026-05-28
Topic: Codex IDE extension tutorial
Command: python main.py --topic "Codex IDE extension tutorial" --max-results 10 --level beginner --official-first
Expected useful video: Official OpenAI overview or a clear beginner VS Code/Codex setup tutorial.
Actual top result: OpenAI Codex in your code editor
Failure type: Tradeoff/validation case: official-first correctly promoted the official source even though some community videos had higher metadata learning scores.
Likely fix: No immediate fix. If humans prefer the community tutorial after watching, reduce the official-first boost or require stronger practical/tutorial signals for official videos.
Notes: YouTube API worked. All 10 transcripts were unavailable, so implementation depth was hard to verify. The official OpenAI video had a high credibility score but only moderate practical/implementation scores.
```

### Case 3

```text
Date: 2026-05-28
Topic: build RAG app with Python
Command: python main.py --topic "build RAG app with Python" --max-results 10 --level intermediate
Expected useful video: A practical intermediate walkthrough with enough duration and specificity to build a working RAG app.
Actual top result: How to Build a Production-Ready RAG AI Agent in Python (Step-by-Step)
Failure type: No obvious failure; top result looks aligned with the query and learner level.
Likely fix: No immediate fix. If humans prefer the freeCodeCamp/LangChain engineer video, consider whether long-form conceptual rigor should be a separate ranking dimension instead of one scalar score.
Notes: YouTube API worked. All 10 transcripts were unavailable. The freeCodeCamp video ranked 4th despite high credibility and depth, mostly because it was older and official-first was not enabled.
```

## Common Failure Types

- Over-promoted official video
- Over-promoted popular but shallow video
- Under-ranked practical implementation video
- Outdated content ranked too high
- Hype language not penalized enough
- Beginner level mismatch
- Advanced level mismatch
- Transcript/comment signal misleading or unavailable
