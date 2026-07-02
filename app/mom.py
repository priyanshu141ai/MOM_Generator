import re


def generate_mom(title: str, transcript: str) -> str:
    lines = [x.strip() for x in transcript.splitlines() if x.strip()]
    text = " ".join(lines)
    action_lines = [x for x in lines if re.search(r"\b(todo|action|will|need to|by )\b", x, re.I)]

    return f"""# MOM: {title}

## Summary
{text[:900] or "No transcript provided."}

## Key Points
{bullet(lines[:8])}

## Action Items
{bullet(action_lines[:10]) if action_lines else "- No clear action items found."}

## Decisions
- To be refined by LLM/local model in next step.

## Risks / Blockers
- Not detected in this basic version.
"""


def bullet(items):
    return "\n".join(f"- {x}" for x in items) if items else "- None"
