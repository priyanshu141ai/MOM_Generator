import re
import json
import urllib.request
from app.config import settings


def generate_mom(title: str, transcript: str) -> str:
    # Try using Gemini API if key is available
    api_key = settings.gemini_api_key
    if not api_key:
        import os
        api_key = os.environ.get("GEMINI_API_KEY", "")

    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            prompt = (
                f"You are an AI meeting assistant. Generate a professional Minutes of Meeting (MOM) "
                f"for the meeting titled '{title}'. Use markdown formatting. Provide the following sections:\n"
                f"1. Overview & Summary (a nice narrative of the meeting)\n"
                f"2. Key Decisions (bullet points of agreed items)\n"
                f"3. Action Items (formatted as: - Owner: [Name] | Task: [Task] | Due: [Date])\n"
                f"4. Risks & Blockers (any concerns raised)\n"
                f"5. Follow-ups (topics to verify or clarify later)\n\n"
                f"Meeting Transcript:\n{transcript}"
            )
            req = urllib.request.Request(
                url,
                data=json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            pass  # Fallback to local heuristic

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
