# Prompt Caching Protocol

All Claude API requests must utilize Prompt Caching to minimize latency and costs.

## Implementation
Insert `cache_control: {"type": "ephemeral"}` at strategic breakpoints in the message array:
- After system instructions.
- After large context blocks (e.g., project structure, lengthy files).
- After the preceding turn in long conversations.
