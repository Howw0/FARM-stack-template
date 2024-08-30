import random
import string
from motor.motor_asyncio import AsyncIOMotorClientSession
from httpx import AsyncClient
from app.db import crud
from app.models import Item, ItemCreate, User, UserCreate, UserUpdate
from app.config import settings


async def create_random_item(session: AsyncIOMotorClientSession) -> Item:
    user = await create_random_user(session)
    assert user is not None
    title = await random_lower_string()
    description = await random_lower_string()
    item_in = ItemCreate(title=title, description=description)
    return await crud.create_item(session=session, user=user, item_in=item_in)


async def user_authentication_headers(client: AsyncClient, email: str, password: str) -> dict[str, str]:
    data = {"username": email, "password": password}
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


async def create_random_user(session: AsyncIOMotorClientSession) -> User:
    email = await random_email()
    password = await random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await crud.create_user(session=session, user_create=user_in)
    return user


async def authentication_token_from_email(client: AsyncClient, email: str, session: AsyncIOMotorClientSession) -> dict[str, str]:
    """
    Return a valid token for the user with given email.

    If the user doesn't exist it is created first.
    """
    password = await random_lower_string()
    user = await crud.read_user_by_email(session=session, email=email)
    if not user:
        user_in_create = UserCreate(email=email, password=password)
        user = await crud.create_user(session=session, user_create=user_in_create)
    else:
        user_in_update = UserUpdate(password=password)
        if not user.id:
            raise Exception("User id not set")
        user = await crud.update_user(session=session, user=user, user_in=user_in_update)
    return await user_authentication_headers(client=client, email=email, password=password)


async def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


async def random_email() -> str:
    return f"{await random_lower_string()}@{await random_lower_string()}.com"


async def get_superuser_token_headers(client: AsyncClient) -> dict[str, str]:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers

