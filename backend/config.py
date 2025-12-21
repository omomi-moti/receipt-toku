from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- e-Stat API 設定 ---
    ESTAT_APP_ID: str = ""
    ESTAT_BASE_URL: str = "https://api.e-stat.go.jp/rest/3.0/app/json"

    # --- Gemini Vision API 設定 ---
    GEMINI_API_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/models"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-flash-latest"
    GEMINI_MODEL_FALLBACK: str = "gemini-1.5-pro"

    # --- Supabase 設定 ---
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # Pydantic Settings の設定
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
