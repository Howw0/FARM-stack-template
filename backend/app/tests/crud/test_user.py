import pytest
from fastapi.encoders import jsonable_encoder
from motor.motor_asyncio import AsyncIOMotorClientSession
from app.db import crud
from app.models import UserCreate, UserUpdate
from app.core.security import verify_password
from app.tests.utils import random_email, random_lower_string

@pytest.mark.asyncio
async def test_create_user(session: AsyncIOMotorClientSession) -> None:
    email = await random_email()
    password = await random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await crud.create_user(session=session, user_create=user_in)
    assert user.email == email
    assert hasattr(user, "hashed_password")


@pytest.mark.asyncio
async def test_authenticate_user(session: AsyncIOMotorClientSession) -> None:
    email = await random_email()
    password = await random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await crud.create_user(session=session, user_create=user_in)
    authenticated_user = await crud.authenticate(session=session, email=email, password=password)
    assert authenticated_user
    assert user.email == authenticated_user.email


@pytest.mark.asyncio
async def test_not_authenticate_user(session: AsyncIOMotorClientSession) -> None:
    email = await random_email()
    password = await random_lower_string()
    user = await crud.authenticate(session=session, email=email, password=password)
    assert user is None


@pytest.mark.asyncio
async def test_check_if_user_is_active(session: AsyncIOMotorClientSession) -> None:
    email = await random_email()
    password = await random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await crud.create_user(session=session, user_create=user_in)
    assert user.is_active is True


@pytest.mark.asyncio
async def test_check_if_user_is_active_inactive(session: AsyncIOMotorClientSession) -> None:
    email = await random_email()
    password = await random_lower_string()
    user_in = UserCreate(email=email, password=password, disabled=True)
    user = await crud.create_user(session=session, user_create=user_in)
    assert user.is_active


@pytest.mark.asyncio
async def test_check_if_user_is_superuser(session: AsyncIOMotorClientSession) -> None:
    email = await random_email()
    password = await random_lower_string()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = await crud.create_user(session=session, user_create=user_in)
    assert user.is_superuser is True


@pytest.mark.asyncio
async def test_check_if_user_is_superuser_normal_user(session: AsyncIOMotorClientSession) -> None:
    username = await random_email()
    password = await random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = await crud.create_user(session=session, user_create=user_in)
    assert user.is_superuser is False


@pytest.mark.asyncio
async def test_get_user(session: AsyncIOMotorClientSession) -> None:
    password = await random_lower_string()
    username = await random_email()
    user_in = UserCreate(email=username, password=password, is_superuser=True)
    user = await crud.create_user(session=session, user_create=user_in)
    user_2 = await crud.read_user_by_id(session=session, id=user.id)
    assert user_2
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


@pytest.mark.asyncio
async def test_update_user(session: AsyncIOMotorClientSession) -> None:
    password = await random_lower_string()
    email = await random_email()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = await crud.create_user(session=session, user_create=user_in)
    new_password = await random_lower_string()
    user_in_update = UserUpdate(password=new_password, is_superuser=True)
    if user.id is not None:
        await crud.update_user(session=session, user=user, user_in=user_in_update)
    user_2 = await crud.read_user_by_id(session=session, id=user.id)
    assert user_2
    assert user.email == user_2.email
    assert await verify_password(new_password, user_2.hashed_password)
