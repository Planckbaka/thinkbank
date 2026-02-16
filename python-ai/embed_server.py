"""
ThinkBank AI Service - HTTP Embed API
Lightweight FastAPI endpoint for query embedding.
Called by Go backend for vector search.
"""

import sys
import threading
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from loguru import logger

from core.embeddings import get_text_embedder

app = FastAPI(title="ThinkBank Embed API", docs_url=None, redoc_url=None)


class EmbedRequest(BaseModel):
    text: str


class EmbedResponse(BaseModel):
    vector: List[float]
    dimensions: int


@app.post("/api/embed", response_model=EmbedResponse)
async def embed_text(req: EmbedRequest):
    """Embed a text query into a 1024-dim BGE-M3 vector."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Empty text")

    try:
        embedder = get_text_embedder()
        vector = embedder.embed_single(req.text.strip())
        return EmbedResponse(vector=vector, dimensions=len(vector))
    except Exception as e:
        logger.error(f"Embed error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}


def start_embed_server(host: str = "0.0.0.0", port: int = 50052):
    """Start the embed HTTP server in a background thread."""
    logger.info(f"Starting embed HTTP server on {host}:{port}")
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    return thread


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    uvicorn.run(app, host="0.0.0.0", port=50052)
