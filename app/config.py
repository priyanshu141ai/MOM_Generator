from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MOM Bot"
    database_url: str = "sqlite:///./mom_bot.db"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    mail_from: str = ""
    bot_display_name: str = "MOM Recorder Bot"
    recordings_dir: str = "./recordings"
    ffmpeg_bin: str = "ffmpeg"
    ffmpeg_audio_input: str = ""
    bot_headless: bool = False
    bot_browser_profile: str = "./browser-profile"
    bot_browser_channel: str = "chrome"
    bot_chrome_profile_directory: str = ""
    bot_cdp_url: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
