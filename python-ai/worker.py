#!/usr/bin/env python3
"""
ThinkBank AI Worker - Entry Point
Starts the Redis worker for async asset processing
"""

import sys
import asyncio
from loguru import logger

from workers.asset_processor import AssetProcessor


def main():
    """Main entry point."""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    )

    logger.info("Starting ThinkBank AI Worker...")

    processor = AssetProcessor()
    try:
        asyncio.run(processor.run())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")


if __name__ == "__main__":
    main()
