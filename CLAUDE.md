# Project rules
- Python 3.11+, Anthropic SDK. Every demo runs offline in mock mode
  and live when ANTHROPIC_API_KEY is set.
- Each task folder: README.md (theory, exam trap, code walkthrough),
  good_example.py, anti_pattern.py, and a test file.
- Domain 3 is config-heavy: build demo configs, YAML and shell scripts
  instead of Python where that fits the concept.
- Label "exam answer" vs "current docs" wherever they differ.
- One domain per commit batch; never commit secrets or .env.
- Source of truth for content: notes/CCA_Foundations-Study_notes.pdf
