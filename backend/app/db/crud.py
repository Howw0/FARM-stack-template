from typing import Optional
from beanie import PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorClientSession
from app.core.security import get_password_hash, verify_password
from app.models import User, UserCreate, UserUpdate, Item, ItemCreate


async def create_user(session: AsyncIOMotorClientSession, user_create: UserCreate) -> User:
    user_data = user_create.model_dump(exclude_unset=True)
    if "password" in user_data:
        user_data["hashed_password"] = await get_password_hash(user_data.pop("password"))
    user = User.model_validate(user_data)
    await user.insert(session=session)
    return user


async def read_user_by_id(session: AsyncIOMotorClientSession, id: PydanticObjectId) -> Optional[User]:
    user = await User.get(document_id=id, session=session)
    return user


async def read_user_by_email(session: AsyncIOMotorClientSession, email: str) -> Optional[User]:
    user = await User.find_one(User.email == email, session=session)
    return user


async def update_user(session: AsyncIOMotorClientSession, user: User, user_in: UserUpdate) -> User:
    user_data = user_in.model_dump(exclude_unset=True)
    if "password" in user_data:
        user_data["hashed_password"] = await get_password_hash(user_data.pop("password"))
    await user.set(expression=user_data, session=session)
    return user


async def delete_user(session: AsyncIOMotorClientSession, user: User) -> None:
    await user.delete(session=session)
    return


async def authenticate(session: AsyncIOMotorClientSession, email: str, password: str) -> Optional[User]:
    user = await read_user_by_email(session=session, email=email)
    if not user:
        return None
    if not await verify_password(password, user.hashed_password):
        return None
    return user


async def create_item(session: AsyncIOMotorClientSession, user: User, item_in: ItemCreate) -> Item:
    item_data = item_in.model_dump(exclude_unset=True)
    item_data["owner_id"] = user.id
    item_data["owner"] = user
    item = Item.model_validate(item_data)
    item = await item.insert(session=session)
    return item