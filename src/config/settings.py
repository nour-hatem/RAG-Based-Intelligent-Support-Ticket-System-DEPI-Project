from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    groq_api_key: str
    model_name: str = "llama-3.1-8b-instant"
    embed_model: str = "all-MiniLM-L6-v2"
    top_k: int = 5
    eval_sample_size: int = 250

    faiss_index_path: Path = Path("faiss/faiss.index")
    train_csv_path: Path = Path("data/processed/train.csv")
    test_csv_path: Path = Path("data/processed/test.csv")

settings = Settings()