import re


def generate_mom(title: str, transcript: str) -> str:
    lines = [x.strip() for x in transcript.splitlines() if x.strip()]
    utterances = [clean_line(x) for x in lines]
    utterances = [x for x in utterances if x]

    summary = summarize(utterances)
    decisions = pick(utterances, r"\b(decided|decision|approved|final|agreed|confirmed)\b")
    risks = pick(utterances, r"\b(risk|blocker|blocked|issue|problem|delay|concern|dependency)\b")
    followups = pick(utterances, r"\b(check|confirm|clarify|follow up|verify|review)\b")
    actions = action_items(utterances)

    return f"""# MOM: {title}

## Summary
{summary}

## Key Points
{bullet(utterances[:8])}

## Decisions
{bullet(decisions[:8])}

## Action Items
{bullet(actions[:12])}

## Risks / Blockers
{bullet(risks[:8])}

## Follow-ups
{bullet(followups[:8])}
"""


def bullet(items):
    return "\n".join(f"- {x}" for x in items) if items else "- None"


def clean_line(line: str) -> str:
    line = re.sub(r"^\d+(\.\d+)?-\d+(\.\d+)?:\s*", "", line)
    return re.sub(r"\s+", " ", line).strip()


def speaker(line: str) -> str:
    m = re.match(r"^([^:]{2,40}):\s*(.+)$", line)
    return m.group(1).strip() if m else "Unassigned"


def pick(lines: list[str], pattern: str) -> list[str]:
    return [x for x in lines if re.search(pattern, x, re.I)]


def summarize(lines: list[str]) -> str:
    if not lines:
        return "No transcript provided."
    joined = " ".join(lines)
    if len(joined) <= 700:
        return joined
    return joined[:700].rsplit(" ", 1)[0] + "..."


def action_items(lines: list[str]) -> list[str]:
    patterns = r"\b(i will|we will|will|need to|needs to|todo|action|assign|take care|by tomorrow|by friday|deadline)\b"
    items = []
    for line in lines:
        if re.search(patterns, line, re.I):
            owner = speaker(line)
            task = re.sub(r"^[^:]{2,40}:\s*", "", line)
            due = due_date(task)
            items.append(f"Owner: {owner} | Task: {task} | Due: {due}")
    return items


def due_date(text: str) -> str:
    m = re.search(r"\b(by\s+\w+|tomorrow|today|next week|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", text, re.I)
    return m.group(1) if m else "Not specified"
