from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession
from beanie import init_beanie
from typing import AsyncGenerator
from app.config import settings, logger
from app.models import User, Item, UserCreate
from . import crud


async def get_session() -> AsyncGenerator[AsyncIOMotorClientSession, None]:
    client = AsyncIOMotorClient(settings.DB_URL)
    try:
        await init_beanie(database=client[settings.DB_DATABASE], document_models=[Item, User])
        async with await client.start_session() as session:
            yield session
    finally:
        client.close()


async def init_db(session: AsyncIOMotorClientSession) -> None:
    logger.info("Waiting for db startup.")
    user = await User.find_one(User.email == settings.FIRST_SUPERUSER)
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = await crud.create_user(session=session, user_create=user_in)
    logger.info("Db startup complete.")
