import pytest
from unittest.mock import patch
from httpx import AsyncClient
from beanie import PydanticObjectId
from app.config import settings
from app.db import crud, get_session
from app.models import UserCreate
from app.core.security import verify_password
from app.tests.utils import random_email, random_lower_string


@pytest.mark.asyncio
async def test_get_users_superuser_me(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    r = await client.get(f"{settings.API_V1_STR}/users/me", headers=superuser_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"]
    assert current_user["email"] == settings.FIRST_SUPERUSER


@pytest.mark.asyncio
async def test_get_users_normal_user_me(client: AsyncClient, normal_user_token_headers: dict[str, str]) -> None:
    r = await client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"] is False
    assert current_user["email"] == settings.EMAIL_TEST_USER


@pytest.mark.asyncio
async def test_create_user_new_email(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    with (
        patch("app.utils.send_email", return_value=None),
        patch("app.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("app.config.settings.SMTP_USER", "admin@example.com"),
    ):
        email = await random_email()
        password = await random_lower_string()
        data = {
            "email": email, 
            "password": password
        }
        r = await client.post(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            json=data,
        )
        assert 200 <= r.status_code < 300
        created_user = r.json()
        user = None
        async for session in get_session():
            user = await crud.read_user_by_email(session=session, email=email)
        assert user
        assert user.email == created_user["email"]


@pytest.mark.asyncio
async def test_get_existing_user(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    email = await random_email()
    password = await random_lower_string()
    user_in = UserCreate(email=email, password=password)
    async for session in get_session():
        user = await crud.create_user(session=session, user_create=user_in)
    r = await client.get(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
    )
    assert 200 <= r.status_code < 300
    api_user = r.json()
    existing_user = None
    async for session in get_session():
        existing_user = await crud.read_user_by_email(session=session, email=email)
    assert existing_user
    assert existing_user.email == api_user["email"]


@pytest.mark.asyncio
async def test_get_existing_user_current_user(client: AsyncClient) -> None:
    email = await random_email()
    password = await random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = None
    async for session in get_session():
        user = await crud.create_user(session=session, user_create=user_in)
    login_data = {
        "username": email,
        "password": password,
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}

    r = await client.get(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=headers,
    )
    assert 200 <= r.status_code < 300
    api_user = r.json()
    existing_user = None
    async for session in get_session():
        existing_user = await crud.read_user_by_email(session=session, email=email)
    assert existing_user
    assert existing_user.email == api_user["email"]


@pytest.mark.asyncio
async def test_get_existing_user_permissions_error(client: AsyncClient, normal_user_token_headers: dict[str, str]) -> None:
    email = await random_email()
    password = await random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = None
    async for session in get_session():
        user = await crud.create_user(session=session, user_create=user_in)
    r = await client.get(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403
    assert r.json() == {"detail": "The user doesn't have enough privileges"}


@pytest.mark.asyncio
async def test_create_user_existing_email(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    email = await random_email()
    password = await random_lower_string()
    user_in = UserCreate(email=email, password=password)
    async for session in get_session():
        await crud.create_user(session=session, user_create=user_in)
    data = {
        "email": email, 
        "password": password
    }
    r = await client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json=data,
    )
    created_user = r.json()
    assert r.status_code == 400
    assert "_id" not in created_user


@pytest.mark.asyncio
async def test_create_user_by_normal_user(client: AsyncClient, normal_user_token_headers: dict[str, str]) -> None:
    email = await random_email()
    password = await random_lower_string()
    data = {
        "username": email, 
        "password": password
    }
    r = await client.post(
        f"{settings.API_V1_STR}/users/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_retrieve_users(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    email = await random_email()
    email2 = await random_email()
    password = await random_lower_string()
    password2 = await random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user_in2 = UserCreate(email=email2, password=password2)
    async for session in get_session():
        await crud.create_user(session=session, user_create=user_in)
        await crud.create_user(session=session, user_create=user_in2)

    r = await client.get(f"{settings.API_V1_STR}/users/", headers=superuser_token_headers)
    all_users = r.json()

    assert len(all_users["data"]) > 1
    assert "count" in all_users
    for item in all_users["data"]:
        assert "email" in item


@pytest.mark.asyncio
async def test_update_user_me(client: AsyncClient, normal_user_token_headers: dict[str, str]) -> None:
    full_name = "Updated Name"
    email = await random_email()
    data = {
        "full_name": full_name, 
        "email": email
    }
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["email"] == email
    assert updated_user["full_name"] == full_name

    user = None
    async for session in get_session():
        user = await crud.read_user_by_email(session=session, email=email)
    assert user
    assert user.email == email
    assert user.full_name == full_name


@pytest.mark.asyncio
async def test_update_password_me(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    new_password = await random_lower_string()
    data = {
        "current_password": settings.FIRST_SUPERUSER_PASSWORD,
        "new_password": new_password,
    }
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["message"] == "Password updated successfully"

    user = None
    async for session in get_session():
        user = await crud.read_user_by_email(session=session, email=settings.FIRST_SUPERUSER)
    assert user
    assert user.email == settings.FIRST_SUPERUSER
    assert await verify_password(new_password, user.hashed_password)

    # Revert to the old password to keep consistency in test
    old_data = {
        "current_password": new_password,
        "new_password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json=old_data,
    )
    assert r.status_code == 200

    async for session in get_session():
        user = await crud.read_user_by_id(session=session, id=user.id)
    assert await verify_password(settings.FIRST_SUPERUSER_PASSWORD, user.hashed_password)


@pytest.mark.asyncio
async def test_update_password_me_incorrect_password(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    new_password = await random_lower_string()
    data = {
        "current_password": new_password, 
        "new_password": new_password
    }
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 400
    updated_user = r.json()
    assert updated_user["detail"] == "Incorrect password"


@pytest.mark.asyncio
async def test_update_user_me_email_exists(client: AsyncClient, normal_user_token_headers: dict[str, str]) -> None:
    email = await random_email()
    password = await random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = None
    async for session in get_session():
        user = await crud.create_user(session=session, user_create=user_in)

    data = {"email": user.email}
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "User with this email already exists"


@pytest.mark.asyncio
async def test_update_password_me_same_password_error(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    data = {
        "current_password": settings.FIRST_SUPERUSER_PASSWORD,
        "new_password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 400
    updated_user = r.json()
    assert (
        updated_user["detail"] == "New password cannot be the same as the current one"
    )


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient) -> None:
    email = await random_email()
    password = await random_lower_string()
    full_name = await random_lower_string()
    data = {"email": email, "password": password, "full_name": full_name}
    r = await client.post(
        f"{settings.API_V1_STR}/users/signup",
        json=data,
    )
    assert r.status_code == 200
    created_user = r.json()
    assert created_user["email"] == email
    assert created_user["full_name"] == full_name

    user= None
    async for session in get_session():
        user = await crud.read_user_by_email(session=session, email=email)
    assert user
    assert user.email == email
    assert user.full_name == full_name
    assert await verify_password(password, user.hashed_password)


@pytest.mark.asyncio
async def test_register_user_already_exists_error(client: AsyncClient) -> None:
    password = await random_lower_string()
    full_name = await random_lower_string()
    data = {
        "email": settings.FIRST_SUPERUSER,
        "password": password,
        "full_name": full_name,
    }
    r = await client.post(
        f"{settings.API_V1_STR}/users/signup",
        json=data,
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "The user with this email already exists in the system"


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    email = await random_email()
    password = await random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = None
    async for session in get_session():
        user = await crud.create_user(session=session, user_create=user_in)

    data = {"full_name": "Updated_full_name"}
    r = await client.patch(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200
    updated_user = r.json()

    assert updated_user["full_name"] == "Updated_full_name"
    async for session in get_session():
        user = await crud.read_user_by_email(session=session, email=email)
    assert user
    assert user.full_name == "Updated_full_name"


@pytest.mark.asyncio
async def test_update_user_not_exists(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    data = {"full_name": "Updated_full_name"}
    r = await client.patch(
        f"{settings.API_V1_STR}/users/{PydanticObjectId()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "The user with this id does not exist in the system"


@pytest.mark.asyncio
async def test_update_user_email_exists(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    email = await random_email()
    email2 = await random_email()
    password = await random_lower_string()
    password2 = await random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user_in2 = UserCreate(email=email2, password=password2)
    user = None
    user2 = None
    async for session in get_session():
        user = await crud.create_user(session=session, user_create=user_in)
        user2 = await crud.create_user(session=session, user_create=user_in2)

    data = {"email": user2.email}
    r = await client.patch(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "User with this email already exists"


@pytest.mark.asyncio
async def test_delete_user_me(client: AsyncClient) -> None:
    email = await random_email()
    password = await random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = None
    async for session in get_session():
        user = await crud.create_user(session=session, user_create=user_in)

    login_data = {
        "username": email,
        "password": password,
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}

    r = await client.delete(
        f"{settings.API_V1_STR}/users/me",
        headers=headers,
    )
    assert r.status_code == 200
    deleted_user = r.json()
    assert deleted_user["message"] == "User deleted successfully"
    result = None
    async for session in get_session():
        result = await crud.read_user_by_id(session=session, id=user.id)
    assert result is None


@pytest.mark.asyncio
async def test_delete_user_me_as_superuser(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    r = await client.delete(
        f"{settings.API_V1_STR}/users/me",
        headers=superuser_token_headers,
    )
    assert r.status_code == 403
    response = r.json()
    assert response["detail"] == "Super users are not allowed to delete themselves"


@pytest.mark.asyncio
async def test_delete_user_super_user(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    email = await random_email()
    password = await random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = None
    async for session in get_session():
        user = await crud.create_user(session=session, user_create=user_in)
    r = await client.delete(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    deleted_user = r.json()
    assert deleted_user["message"] == "User deleted successfully"
    result = None
    async for session in get_session():
        result = await crud.read_user_by_id(session=session, id=user.id)
    assert result is None


@pytest.mark.asyncio
async def test_delete_user_not_found(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    r = await client.delete(
        f"{settings.API_V1_STR}/users/{PydanticObjectId()}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_delete_user_current_super_user_error(client: AsyncClient, superuser_token_headers: dict[str, str]) -> None:
    super_user = None
    async for session in get_session():
        super_user = await crud.read_user_by_email(session=session, email=settings.FIRST_SUPERUSER)
    assert super_user

    r = await client.delete(
        f"{settings.API_V1_STR}/users/{super_user.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Super users are not allowed to delete themselves"


@pytest.mark.asyncio
async def test_delete_user_without_privileges(client: AsyncClient, normal_user_token_headers: dict[str, str]) -> None:
    email = await random_email()
    password = await random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = None
    async for session in get_session():
        user = await crud.create_user(session=session, user_create=user_in)

    r = await client.delete(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "The user doesn't have enough privileges"
