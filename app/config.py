import os
from pydantic import BaseModel


class Settings(BaseModel):
    # Web
    DEBUG: bool = bool(int(os.getenv("DEBUG", "1")))

    # Spring Boot DB
    DB_URL: str | None = os.getenv("DB_URL")
    USE_DUMMY_LOGS: bool = bool(int(os.getenv("USE_DUMMY_LOGS", "1")))
    LOG_TABLE: str = os.getenv("LOG_TABLE", "logs")
    COL_TIMESTAMP: str = os.getenv("COL_TIMESTAMP", "timestamp")
    COL_LEVEL: str = os.getenv("COL_LEVEL", "level")
    COL_LOGGER: str = os.getenv("COL_LOGGER", "logger")
    COL_MESSAGE: str = os.getenv("COL_MESSAGE", "message")
    COL_CORRELATION_ID: str = os.getenv("COL_CORRELATION_ID", "correlation_id")

    # Codebase scanning
    JAVA_CODE_PATH: str = os.getenv("JAVA_CODE_PATH", "./spring-app/")
    # More permissive default: captures logger.xxx(...) across lines and any arg style
    # Matches: logger.info("..."); log.error("... {}", var); etc.
    LOG_REGEX: str = os.getenv(
        "LOG_REGEX",
        r"\.(info|error|warn|debug|trace)\s*\((?:.|\n)*?\)"
    )
    CONTEXT_WINDOW: int = int(os.getenv("CONTEXT_WINDOW", "20"))
    FILE_EXTS: list[str] = os.getenv("FILE_EXTS", ".java,.kt").split(",")
    EXCLUDE_DIRS: list[str] = os.getenv("EXCLUDE_DIRS", ".git,node_modules,build,target,out,dist").split(",")

    # Vector DB
    CHROMA_DIR: str = os.getenv("CHROMA_DIR", "./data/chroma")
    CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "log_context")

    # Embeddings
    USE_OPENAI_EMBEDDINGS: bool = bool(int(os.getenv("USE_OPENAI_EMBEDDINGS", "0")))
    USE_OLLAMA_EMBEDDINGS: bool = bool(int(os.getenv("USE_OLLAMA_EMBEDDINGS", "1")))
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: str | None = os.getenv("OPENAI_BASE_URL")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    ST_EMBEDDING_MODEL: str = os.getenv("ST_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_EMBEDDING_MODEL: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

    # LLM
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    REQUIRE_LLM: bool = bool(int(os.getenv("REQUIRE_LLM", "1")))


settings = Settings()
