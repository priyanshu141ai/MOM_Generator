import asyncio
from pathlib import Path

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from app.config import settings


async def join_google_meet(url: str, duration_sec: int = 60):
    async with async_playwright() as p:
        if settings.bot_cdp_url:
            try:
                browser = await p.chromium.connect_over_cdp(settings.bot_cdp_url, timeout=5000)
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
                page = await context.new_page()
                await drive_meet_page(page, url, duration_sec)
                await browser.close()
                return
            except Exception:
                if settings.bot_headless:
                    raise

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


async def drive_meet_page(page, url: str, duration_sec: int):
    await page.goto(url, wait_until="domcontentloaded")
    try:
        await page.wait_for_load_state("networkidle", timeout=15000)
    except PlaywrightTimeoutError:
        pass
    await page.wait_for_timeout(2500)
    await dismiss_prejoin(page)
    await click_first(page, ["Ask to join", "Join now", "Continue", "Continue without microphone and camera"])
    await page.wait_for_timeout(2500)
    await save_debug(page)
    if await blocked(page):
        raise RuntimeError("Google Meet blocked join. Invite/admit bot account or use Chrome debug profile.")
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
            await page.get_by_text(text, exact=False).last.click(timeout=5000)
            return True
        except Exception:
            pass
        try:
            await page.get_by_role("button", name=text, exact=False).last.click(timeout=3000)
            return True
        except Exception:
            pass
    return False


async def blocked(page) -> bool:
    text = await page.locator("body").inner_text(timeout=3000)
    blocked_phrases = ["can't join this video call", "not allowed to join", "returning to home screen"]
    return any(x in text.lower() for x in blocked_phrases)


async def save_debug(page):
    Path(settings.bot_debug_dir).mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=str(Path(settings.bot_debug_dir) / "last_meet.png"), full_page=True)
