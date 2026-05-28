# Contributing

Thanks for helping improve YouTube Learning Scout.

## Development Setup

See `README.md` for local development setup. The short version is:

```bash
python -m venv .venv
pip install -e .
```

## Reporting Issues

When reporting a ranking issue, include:

- the command you ran
- the top result
- the video you expected to rank higher
- why the actual ranking felt wrong

Use `evaluation_notes.example.md` as the template for ranking-quality feedback.

## Tests

Tests are welcome. The first useful tests would cover duration parsing, scoring breakdowns, credibility notes, and report formatting.
