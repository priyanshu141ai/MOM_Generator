import asyncio
from pathlib import Path

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from app.config import settings


async def join_google_meet(url: str, duration_sec: int = 60):
    async with async_playwright() as p:
        cdp = await cdp_context(p)
        if cdp:
            browser, context = cdp
            page = await context.new_page()
            await drive_meet_page(page, url, duration_sec)
            await browser.close()
            return

        Path(settings.bot_browser_profile).mkdir(parents=True, exist_ok=True)
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=settings.bot_browser_profile,
            channel=settings.bot_browser_channel,
            headless=settings.bot_headless,
            args=chrome_args(),
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()
        await drive_meet_page(page, url, duration_sec)
        await browser.close()


async def diagnose_google_meet(url: str) -> dict:
    async with async_playwright() as p:
        cdp = await cdp_context(p)
        if not cdp:
            raise RuntimeError("Chrome debug is not reachable. Run scripts/start_chrome_debug.ps1")
        browser, context = cdp
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeoutError:
            pass
        await page.wait_for_timeout(2500)
        await dismiss_prejoin(page)
        await save_debug(page)
        body = await page.locator("body").inner_text(timeout=3000)
        buttons = await page.locator("button").evaluate_all("(els) => els.map((e) => e.innerText || e.ariaLabel || '').filter(Boolean)")
        await page.close()
        await browser.close()
        return {"state": meet_state(body), "buttons": buttons[:30], "debug_screenshot": f"{settings.bot_debug_dir}/last_meet.png"}


async def open_google_login():
    async with async_playwright() as p:
        Path(settings.bot_browser_profile).mkdir(parents=True, exist_ok=True)
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=settings.bot_browser_profile,
            channel=settings.bot_browser_channel,
            headless=False,
            args=chrome_args(login=True),
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()
        await page.goto("https://accounts.google.com/", wait_until="domcontentloaded")
        await page.wait_for_timeout(300000)
        await browser.close()


def chrome_args(login: bool = False) -> list[str]:
    args = ["--disable-notifications"]
    if not login:
        args.append("--use-fake-ui-for-media-stream")
    if settings.bot_chrome_profile_directory:
        args.append(f"--profile-directory={settings.bot_chrome_profile_directory}")
    return args


async def cdp_context(p):
    if not settings.bot_cdp_url:
        return None
    try:
        browser = await p.chromium.connect_over_cdp(settings.bot_cdp_url, timeout=5000)
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        return browser, context
    except Exception:
        return None


async def drive_meet_page(page, url: str, duration_sec: int):
    await page.goto(url, wait_until="domcontentloaded")
    try:
        await page.wait_for_load_state("networkidle", timeout=15000)
    except PlaywrightTimeoutError:
        pass
    await page.wait_for_timeout(2500)
    await dismiss_prejoin(page)
    clicked = await click_first(page, ["Ask to join", "Join now", "Continue", "Continue without microphone and camera"])
    await page.wait_for_timeout(2500)
    await save_debug(page)
    body = await page.locator("body").inner_text(timeout=3000)
    state = meet_state(body)
    if not clicked and state == "prejoin":
        raise RuntimeError("Meet join button was visible but could not be clicked")
    if state == "blocked":
        raise RuntimeError("Google Meet blocked join. Invite/admit bot account or use Chrome debug profile.")
    if state == "waiting_for_admission":
        raise RuntimeError("Bot is waiting for host admission. Admit it from host account.")
    await asyncio.sleep(duration_sec)


async def dismiss_prejoin(page):
    for label in ["Turn off microphone", "Turn off camera"]:
        try:
            btn = page.get_by_label(label, exact=False).first
            if await btn.count():
                await btn.click(timeout=1000)
        except Exception:
            pass


async def click_first(page, texts: list[str]) -> bool:
    for text in texts:
        try:
            await page.get_by_role("button", name=text, exact=False).last.click(timeout=5000)
            return True
        except Exception:
            pass
        try:
            await page.get_by_text(text, exact=False).last.click(timeout=3000)
            return True
        except Exception:
            pass
    return False


async def click_if_visible(page, text: str, timeout: int = 1000) -> bool:
    try:
        button = page.get_by_role("button", name=text, exact=False).last
        if await button.count():
            await button.click(timeout=timeout)
            await page.wait_for_timeout(500)
            return True
    except Exception:
        return False
    return False


async def blocked(page) -> bool:
    text = await page.locator("body").inner_text(timeout=3000)
    return meet_state(text) == "blocked"


def meet_state(text: str) -> str:
    lower = text.lower()
    if any(x in lower for x in ["can't join this video call", "not allowed to join", "returning to home screen"]):
        return "blocked"
    if any(x in lower for x in [
        "asking to be let in",
        "you'll join the call when someone lets you in",
        "waiting to be let in",
        "please wait until a meeting host brings you into the call",
    ]):
        return "waiting_for_admission"
    if any(x in lower for x in ["ask to join", "join now", "ready to join"]):
        return "prejoin"
    if any(x in lower for x in ["leave call", "meeting details", "people", "chat with everyone"]):
        return "joined_or_in_call_ui"
    return "unknown"


async def save_debug(page):
    Path(settings.bot_debug_dir).mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=str(Path(settings.bot_debug_dir) / "last_meet.png"), full_page=True)
