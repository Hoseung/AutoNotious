from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    openai_api_key: str
    model: str = "gpt-4o-mini"
    chat_temperature: float = 0.7
    chat_top_p: float = 1.0
    summary_temperature: float = 0.3
    summary_top_p: float = 1.0
    litellm_url: str = "http://localhost:4000/v1/chat/completions"
    database_url: str = "sqlite:///./app.db"
    notion_api_key: Optional[str] = None
    notion_parent_page_id: Optional[str] = None
    max_context_tokens: int = 5000
    
    class Config:
        env_file = ".env"


settings = Settings()