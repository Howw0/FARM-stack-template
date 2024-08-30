import pytest
from unittest.mock import patch
from httpx import AsyncClient
from app.config import settings
from app.db import crud, get_session
from app.utils import generate_password_reset_token
from app.core.security import verify_password
from app.tests.utils import random_email


@pytest.mark.asyncio
async def test_get_access_token(client: AsyncClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]


@pytest.mark.asyncio
async def test_get_access_token_incorrect_password(client: AsyncClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": "incorrect",
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_use_access_token(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    r = await client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers=superuser_token_headers,
    )
    result = r.json()
    assert r.status_code == 200
    assert "email" in result


@pytest.mark.asyncio
async def test_recovery_password(client: AsyncClient, normal_user_token_headers: dict[str, str]) -> None:
    with (
        patch("app.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("app.config.settings.SMTP_USER", "admin@example.com"),
    ):
        email = "test@example.com"
        r = await client.post(
            f"{settings.API_V1_STR}/password-recovery/{email}",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 200
        assert r.json() == {"message": "Password recovery email sent"}


@pytest.mark.asyncio
async def test_recovery_password_user_not_exits(client: AsyncClient, normal_user_token_headers: dict[str, str]) -> None:
    email = await random_email()
    r = await client.post(
        f"{settings.API_V1_STR}/password-recovery/{email}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_reset_password(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    token = await generate_password_reset_token(email=settings.FIRST_SUPERUSER)
    data = {
        "new_password": "changethis", 
        "token": token
    }
    r = await client.post(
        f"{settings.API_V1_STR}/reset-password/",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200
    assert r.json() == {"message": "Password updated successfully"}
    user = None
    async for session in get_session():
        user = await crud.read_user_by_email(session=session, email=settings.FIRST_SUPERUSER)
    assert user
    assert await verify_password(data["new_password"], user.hashed_password)


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    data = {
        "new_password": "changethis", 
        "token": "invalid"
    }
    r = await client.post(
        f"{settings.API_V1_STR}/reset-password/",
        headers=superuser_token_headers,
        json=data,
    )
    response = r.json()

    assert "detail" in response
    assert r.status_code == 400
    assert response["detail"] == "Invalid token"
