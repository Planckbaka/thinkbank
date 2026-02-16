"""
ThinkBank AI Service Configuration
Environment-based settings with Pydantic.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_user: str = Field(default="thinkbank", alias="DB_USER")
    db_password: str = Field(default="thinkbank123", alias="DB_PASSWORD")
    db_name: str = Field(default="thinkbank", alias="DB_NAME")

    # Redis
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0)

    # MinIO
    minio_endpoint: str = Field(default="localhost:9000", alias="MINIO_ENDPOINT")
    minio_user: str = Field(default="minioadmin", alias="MINIO_USER")
    minio_password: str = Field(default="minioadmin123", alias="MINIO_PASSWORD")
    minio_bucket: str = Field(default="thinkbank-assets")
    minio_secure: bool = Field(default=False)

    # gRPC Server
    grpc_host: str = Field(default="0.0.0.0")
    grpc_port: int = Field(default=50051, alias="AI_GRPC_PORT")

    # LLM Configuration (RTX 4070 8GB VRAM optimized)
    vllm_model: str = Field(
        default="Qwen/Qwen3-VL-8B-Instruct-GPTQ-Int4",
        alias="VLLM_MODEL"
    )
    gpu_memory_utilization: float = Field(
        default=0.8,
        alias="GPU_MEMORY_UTILIZATION"
    )
    max_model_len: int = Field(default=4096)

    # Embedding Models (CPU)
    text_embedding_model: str = Field(
        default="BAAI/bge-m3"
    )
    image_embedding_model: str = Field(
        default="sentence-transformers/clip-ViT-B-32"
    )

    # Vision Captioning Model (CPU/Offload)
    vision_model: str = Field(
        default="HuggingFaceTB/SmolVLM-500M-Instruct"
    )

    # Processing
    max_workers: int = Field(default=2)
    task_queue_name: str = Field(default="thinkbank:tasks")

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
settings = Settings()
