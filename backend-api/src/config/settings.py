from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    # Groq / embedding
    groq_api_key: str
    model_name: str = "llama-3.1-8b-instant"
    embed_model: str = "all-MiniLM-L6-v2"
    top_k: int = 5
    eval_sample_size: int = 250

    # Data paths
    faiss_index_path: Path = Path("faiss/faiss.index")
    train_csv_path: Path = Path("data/processed/train.csv")
    test_csv_path: Path = Path("data/processed/test.csv")

    # API / server
    api_key: str                                                        # required, no default
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS - origins allowed to call this API from a browser (the frontend).
    # JSON array in .env, e.g. CORS_ALLOW_ORIGINS=["http://localhost:5500","https://your-azure-url"]
    cors_allow_origins: list[str] = ["*"]
    # Abstention
    confidence_threshold: float = 0.55

    # Cross-encoder re-ranking
    rerank_enabled: bool = False
    rerank_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    rerank_top_k: int = 5

settings = Settings()
