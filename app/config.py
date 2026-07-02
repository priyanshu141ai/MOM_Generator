from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MOM Bot"
    database_url: str = "sqlite:///./mom_bot.db"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    mail_from: str = ""
    mail_test_to: str = ""
    hf_token: str = ""
    bot_display_name: str = "MOM Recorder Bot"
    recordings_dir: str = "./recordings"
    ffmpeg_bin: str = "ffmpeg"
    ffmpeg_audio_input: str = ""
    bot_headless: bool = False
    bot_browser_profile: str = "./browser-profile"
    bot_browser_channel: str = "chrome"
    bot_chrome_profile_directory: str = ""
    bot_cdp_url: str = ""
    bot_debug_dir: str = "./bot-debug"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://127.0.0.1:8001/calendar/google/callback"
    google_token_file: str = "./google_token.json"
    google_oauth_state_file: str = "./google_oauth_state.txt"
    max_upload_mb: int = 100
    default_transcribe_model: str = "small"
    default_transcribe_language: str = "en"

    class Config:
        env_file = ".env"


settings = Settings()
