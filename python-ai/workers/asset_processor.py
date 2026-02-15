"""
ThinkBank AI Service - Redis Worker
Consumes asset processing tasks from Redis queue
"""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Optional

import redis.asyncio as aioredis
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.config import settings


class AssetProcessor:
    """Processes assets from the Redis queue."""

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.db_engine = None
        self.minio_client = None

    async def initialize(self):
        """Initialize connections."""
        # Redis connection
        self.redis = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("Redis connection established")

        # Database connection (async)
        db_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
        self.db_engine = create_async_engine(db_url, echo=False)
        logger.info("Database connection established")

        # MinIO client
        from minio import Minio
        self.minio_client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_user,
            secret_key=settings.minio_password,
            secure=settings.minio_secure
        )
        logger.info("MinIO connection established")

    async def close(self):
        """Close connections."""
        if self.redis:
            await self.redis.close()
        if self.db_engine:
            await self.db_engine.dispose()

    async def run(self):
        """Main worker loop."""
        await self.initialize()

        logger.info(f"Starting worker, listening on queue: {settings.task_queue_name}")

        try:
            while True:
                try:
                    # Block on queue
                    result = await self.redis.brpop(settings.task_queue_name, timeout=5)
                    if result:
                        _, asset_id = result
                        logger.info(f"Received task for asset: {asset_id}")
                        await self.process_asset(asset_id)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in worker loop: {e}")
                    await asyncio.sleep(1)
        finally:
            await self.close()

    async def process_asset(self, asset_id: str):
        """Process a single asset."""
        async with AsyncSession(self.db_engine) as session:
            try:
                # Update status to PROCESSING
                await session.execute(
                    text("UPDATE assets SET processing_status = 'PROCESSING' WHERE id = :id"),
                    {"id": asset_id}
                )
                await session.commit()

                # Get asset info
                result = await session.execute(
                    text("SELECT bucket_name, object_name, mime_type FROM assets WHERE id = :id"),
                    {"id": asset_id}
                )
                row = result.fetchone()

                if not row:
                    logger.error(f"Asset not found: {asset_id}")
                    return

                bucket_name, object_name, mime_type = row

                # Download file from MinIO
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    self.minio_client.fget_object(bucket_name, object_name, tmp.name)
                    tmp_path = tmp.name

                try:
                    # Route to appropriate processor
                    if mime_type.startswith("image/"):
                        await self._process_image(session, asset_id, tmp_path)
                    elif mime_type == "application/pdf":
                        await self._process_document(session, asset_id, tmp_path)
                    elif mime_type.startswith("text/"):
                        await self._process_text(session, asset_id, tmp_path)
                    else:
                        logger.warning(f"Unsupported mime type: {mime_type}")

                    # Update status to COMPLETED
                    await session.execute(
                        text("UPDATE assets SET processing_status = 'COMPLETED' WHERE id = :id"),
                        {"id": asset_id}
                    )
                    await session.commit()
                    logger.info(f"Asset processed successfully: {asset_id}")

                finally:
                    # Cleanup temp file
                    Path(tmp_path).unlink(missing_ok=True)

            except Exception as e:
                logger.error(f"Failed to process asset {asset_id}: {e}")
                await session.execute(
                    text("UPDATE assets SET processing_status = 'FAILED' WHERE id = :id"),
                    {"id": asset_id}
                )
                await session.commit()

    async def _process_image(self, session, asset_id: str, file_path: str):
        """Process an image file."""
        from PIL import Image
        from core.vision import get_vision_model
        from core.embeddings import get_image_embedder

        logger.info(f"Processing image: {asset_id}")

        # Load image
        image = Image.open(file_path).convert("RGB")

        # Generate caption
        vision_model = get_vision_model()
        caption = vision_model.caption(image)
        logger.info(f"Generated caption: {caption[:100]}...")

        # Generate embedding
        embedder = get_image_embedder()
        embedding = embedder.embed_pil(image)

        # Update database
        await session.execute(
            text("UPDATE assets SET caption = :caption WHERE id = :id"),
            {"caption": caption, "id": asset_id}
        )

        # Store embedding (convert to string for pgvector)
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        await session.execute(
            text("""
                INSERT INTO asset_embeddings (asset_id, visual_vector)
                VALUES (:id, :vector::vector)
                ON CONFLICT (asset_id) DO UPDATE SET visual_vector = :vector::vector
            """),
            {"id": asset_id, "vector": embedding_str}
        )
        await session.commit()

    async def _process_document(self, session, asset_id: str, file_path: str):
        """Process a PDF document."""
        logger.info(f"Processing document: {asset_id}")

        # TODO: Implement PDF parsing with Docling
        # For now, extract basic text
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()

            # Generate embedding
            from core.embeddings import get_text_embedder
            embedder = get_text_embedder()
            embedding = embedder.embed_single(text[:8000])  # Limit text length

            # Update database
            await session.execute(
                text("UPDATE assets SET content_text = :text, caption = :caption WHERE id = :id"),
                {"text": text, "caption": text[:500], "id": asset_id}
            )

            # Store embedding
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            await session.execute(
                text("""
                    INSERT INTO asset_embeddings (asset_id, semantic_vector)
                    VALUES (:id, :vector::vector)
                    ON CONFLICT (asset_id) DO UPDATE SET semantic_vector = :vector::vector
                """),
                {"id": asset_id, "vector": embedding_str}
            )
            await session.commit()

        except ImportError:
            logger.warning("PyMuPDF not available, skipping document processing")

    async def _process_text(self, session, asset_id: str, file_path: str):
        """Process a text file."""
        logger.info(f"Processing text: {asset_id}")

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Generate embedding
        from core.embeddings import get_text_embedder
        embedder = get_text_embedder()
        embedding = embedder.embed_single(text[:8000])

        # Update database
        await session.execute(
            text("UPDATE assets SET content_text = :text, caption = :caption WHERE id = :id"),
            {"text": text, "caption": text[:500], "id": asset_id}
        )

        # Store embedding
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        await session.execute(
            text("""
                INSERT INTO asset_embeddings (asset_id, semantic_vector)
                VALUES (:id, :vector::vector)
                ON CONFLICT (asset_id) DO UPDATE SET semantic_vector = :vector::vector
            """),
            {"id": asset_id, "vector": embedding_str}
        )
        await session.commit()


async def main():
    """Main entry point."""
    processor = AssetProcessor()
    await processor.run()


if __name__ == "__main__":
    asyncio.run(main())
