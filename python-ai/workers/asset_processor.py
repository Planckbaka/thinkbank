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

        await self._requeue_incomplete_assets()

    async def _requeue_incomplete_assets(self):
        """Recover tasks that were left in PENDING/PROCESSING when worker restarted."""
        async with AsyncSession(self.db_engine) as session:
            result = await session.execute(
                text("""
                    SELECT id::text
                    FROM assets
                    WHERE processing_status IN ('PENDING', 'PROCESSING')
                    ORDER BY created_at ASC
                """)
            )
            candidate_ids = [row[0] for row in result.fetchall()]

        if not candidate_ids:
            return

        queued_ids = set(await self.redis.lrange(settings.task_queue_name, 0, -1))
        requeued = 0
        for asset_id in candidate_ids:
            if asset_id in queued_ids:
                continue
            await self.redis.lpush(settings.task_queue_name, asset_id)
            requeued += 1

        if requeued > 0:
            logger.info(f"Recovered {requeued} incomplete assets into queue")

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
                logger.info(f"[{asset_id}] Marking status as PROCESSING")
                # Update status to PROCESSING
                await session.execute(
                    text("UPDATE assets SET processing_status = 'PROCESSING' WHERE id = :id"),
                    {"id": asset_id}
                )
                await session.commit()

                logger.info(f"[{asset_id}] Loading asset metadata")
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
                    logger.info(f"[{asset_id}] Downloading from MinIO: {bucket_name}/{object_name}")
                    self.minio_client.fget_object(bucket_name, object_name, tmp.name)
                    tmp_path = tmp.name

                try:
                    logger.info(f"[{asset_id}] Dispatching processor for mime={mime_type}")
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
                await session.rollback()
                await session.execute(
                    text("UPDATE assets SET processing_status = 'FAILED' WHERE id = :id"),
                    {"id": asset_id}
                )
                await session.commit()

    async def _process_image(self, session, asset_id: str, file_path: str):
        """Process an image file."""
        from PIL import Image
        from core.vision import get_vision_model
        from core.embeddings import get_image_embedder, get_text_embedder

        logger.info(f"Processing image: {asset_id}")

        # Load image
        image = Image.open(file_path).convert("RGB")

        # Generate caption from image.
        vision_model = get_vision_model()
        caption_en = vision_model.caption(
            image,
            prompt="Describe this image with key objects and actions.",
        )
        caption = caption_en

        # Add Chinese translation to improve Chinese keyword search ("女的", "猫", etc.).
        caption_zh = ""
        try:
            from core.llm import get_llm_service

            llm = get_llm_service()
            caption_zh = llm.generate(
                (
                    "Translate this image caption into concise Chinese. "
                    "Return only the Chinese sentence.\n\n"
                    f"Caption: {caption_en}"
                ),
                max_tokens=96,
                temperature=0.2,
                top_p=0.9,
            ).strip()

        except Exception as exc:
            logger.warning(f"Failed to translate image caption to Chinese: {exc}")

        if not caption_zh:
            lowered = caption_en.lower()
            keyword_map = {
                "女性": ("female", "woman", "girl", "lady"),
                "男性": ("male", "man", "boy", "gentleman"),
                "人物": ("person", "people", "character", "portrait"),
                "动漫": ("anime", "cartoon", "manga"),
                "舞台": ("stage", "performance", "concert"),
                "室内": ("indoor", "inside", "room"),
                "室外": ("outdoor", "outside"),
            }
            tags = [zh for zh, keys in keyword_map.items() if any(key in lowered for key in keys)]
            if tags:
                caption_zh = "，".join(tags)

        if caption_zh:
            caption = f"{caption_en} | 中文: {caption_zh}"

        # Validate and Classify
        try:
            category = vision_model.classify(image)
            logger.info(f"Classified image as: {category}")
        except Exception as e:
            logger.warning(f"Classification failed: {e}")
            category = "Other"

        # Update specific keywords based on category
        if category == "Document":
             caption += " | [Document]"
        elif category == "Screenshot":
             caption += " | [Screenshot]"

        logger.info(f"Generated caption: {caption[:120]}...")

        # Generate embeddings:
        # - visual_vector for image-image retrieval
        # - semantic_vector from caption for text-image retrieval
        visual_embedder = get_image_embedder()
        visual_embedding = visual_embedder.embed_pil(image)

        text_embedder = get_text_embedder()
        semantic_embedding = text_embedder.embed_single(caption[:2000])

        # Update database
        await session.execute(
            text("UPDATE assets SET caption = :caption, metadata = jsonb_set(metadata, '{category}', :category) WHERE id = :id"),
            {"caption": caption, "category": f'"{category}"', "id": asset_id}
        )

        # Store embeddings (convert to pgvector string literal)
        visual_embedding_str = "[" + ",".join(str(x) for x in visual_embedding) + "]"
        semantic_embedding_str = "[" + ",".join(str(x) for x in semantic_embedding) + "]"
        await session.execute(
            text("""
                INSERT INTO asset_embeddings (asset_id, semantic_vector, visual_vector)
                VALUES (:id, CAST(:semantic_vector AS vector), CAST(:visual_vector AS vector))
                ON CONFLICT (asset_id) DO UPDATE
                SET semantic_vector = CAST(:semantic_vector AS vector),
                    visual_vector = CAST(:visual_vector AS vector)
            """),
            {
                "id": asset_id,
                "semantic_vector": semantic_embedding_str,
                "visual_vector": visual_embedding_str,
            }
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
            # Update database with Document category
            await session.execute(
                text("UPDATE assets SET content_text = :text, caption = :caption, metadata = jsonb_set(metadata, '{category}', '\"Document\"') WHERE id = :id"),
                {"text": text, "caption": text[:500], "id": asset_id}
            )

            # Store embedding
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            await session.execute(
                text("""
                    INSERT INTO asset_embeddings (asset_id, semantic_vector)
                    VALUES (:id, CAST(:vector AS vector))
                    ON CONFLICT (asset_id) DO UPDATE SET semantic_vector = CAST(:vector AS vector)
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
                VALUES (:id, CAST(:vector AS vector))
                ON CONFLICT (asset_id) DO UPDATE SET semantic_vector = CAST(:vector AS vector)
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
