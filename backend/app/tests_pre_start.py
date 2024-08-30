import logging
import asyncio
from app.config import logger
from app.db import init_db, get_session


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Initializing service")
    async for session in get_session():
        await init_db(session=session)
    logger.info("Service finished initializing")


if __name__ == "__main__":
    asyncio.run(main())