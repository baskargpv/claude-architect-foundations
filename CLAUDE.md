# Project rules
- Python 3.11+, Anthropic SDK. Every demo runs offline in mock mode
  and live when ANTHROPIC_API_KEY is set.
- Each task folder: README.md (theory, exam trap, code walkthrough),
  good_example.py, anti_pattern.py, and a test file.
- good_example.py implements the lesson's Build Exercise step by step;
  anti_pattern.py has one runnable function per Exam Trap on the lesson.
- All domains, including Domain 3, are Python programs. Domain 3 programs
  may generate and validate config files (CLAUDE.md, .claude/, YAML, shell).
- MCP tools use the real `mcp` package (in-process server); Agent SDK
  concepts (allowed_tools, agents, hooks) are SDK-shaped but run on the
  Messages API.
- Label "exam answer" vs "current docs" wherever they differ.
- One domain per commit batch; never commit secrets or .env.
- Source of truth for content: https://claudecertificationguide.com/learn
  (one lesson per task; link it from each task README, paraphrase, don't copy).
