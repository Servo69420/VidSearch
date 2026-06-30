from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/vidsearch"
    OPENROUTER_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    FFMPEG_PATH: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
