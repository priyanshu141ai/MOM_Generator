import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

from app.config import settings


async def join_google_meet(url: str, duration_sec: int = 60):
    async with async_playwright() as p:
        if settings.bot_cdp_url:
            browser = await p.chromium.connect_over_cdp(settings.bot_cdp_url)
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
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
    await page.wait_for_timeout(3000)
    for text in ["Continue without microphone and camera", "Ask to join", "Join now"]:
        try:
            await page.get_by_text(text, exact=False).click(timeout=4000)
            await page.wait_for_timeout(1500)
        except Exception:
            pass
    await asyncio.sleep(duration_sec)
