import json
import urllib.request

from app.config import settings


def cdp_status() -> dict:
    if not settings.bot_cdp_url:
        return {"configured": False, "ok": False}
    try:
        with urllib.request.urlopen(f"{settings.bot_cdp_url}/json/version", timeout=2) as res:
            return {"configured": True, "ok": True, "data": json.loads(res.read())}
    except Exception as exc:
        return {"configured": True, "ok": False, "error": str(exc)}
