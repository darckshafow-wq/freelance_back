from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Freelance Platform Backend"
    API_V1_STR: str = "/api/v1"

    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY: str = "YOUR_SUPER_SECRET_KEY_HERE_PLEASE_CHANGE_IN_PROD"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    CORS_ORIGINS: str | list[str] = ["*"]

    # Database
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "mohamed"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "freelance_db"

    # SMTP / notifications
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    # Accept either a list or a comma-separated string in the environment
    ADMIN_EMAILS: list[str] | str = []

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def cors_origins(self) -> list[str]:
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return self.CORS_ORIGINS

settings = Settings()

# Normalize ADMIN_EMAILS so other modules can always rely on a list[str]
if isinstance(settings.ADMIN_EMAILS, str):
    # allow comma-separated env like ADMIN_EMAILS=admin@ex.com,ops@ex.com
    settings.ADMIN_EMAILS = [e.strip() for e in settings.ADMIN_EMAILS.split(",") if e.strip()]
