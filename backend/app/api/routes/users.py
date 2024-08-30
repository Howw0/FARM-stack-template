from typing import Any
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException
from app.db import crud
from app.config import settings
from app.utils import generate_new_account_email, send_email
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core.security import get_password_hash, verify_password
from app.models import (
    Message,
    UpdatePassword,
    User,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)


router = APIRouter()


@router.get("/", dependencies=[Depends(get_current_active_superuser)], response_model=UsersPublic)
async def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """
    count = await User.count()
    users = await User.find(session=session, skip=skip, limit=limit).to_list()
    users_public = [UserPublic.model_validate(user.model_dump()) for user in users]
    return UsersPublic(data=users_public, count=count)


@router.post("/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic)
async def create_user(session: SessionDep, user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    user = await crud.read_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = await crud.create_user(session=session, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = await generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        await send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.patch("/me", response_model=UserPublic)
async def update_user_me(session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser) -> Any:
    """
    Update own user.
    """
    if user_in.email:
        existing_user = await crud.read_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    await current_user.set(expression=user_data, session=session)
    return current_user


@router.patch("/me/password", response_model=Message)
async def update_password_me(session: SessionDep, body: UpdatePassword, current_user: CurrentUser) -> Any:
    """
    Update own password.
    """
    if not await verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(status_code=400, detail="New password cannot be the same as the current one")
    hashed_password = await get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    await current_user.save(session=session)
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
async def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.delete("/me", response_model=Message)
async def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    await crud.delete_user(session=session, user=current_user)
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
async def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = await crud.read_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="The user with this email already exists in the system")
    user = await crud.create_user(session=session, user_create=user_in)
    return user


@router.get("/{user_id}", response_model=UserPublic)
async def read_user_by_id(session: SessionDep, user_id: PydanticObjectId, current_user: CurrentUser) -> Any:
    """
    Get a specific user by id.
    """
    user = await crud.read_user_by_id(session=session, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if not current_user.is_superuser and user.id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    return user


@router.patch("/{user_id}", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic)
async def update_user(session: SessionDep, user_id: PydanticObjectId, user_in: UserUpdate) -> Any:
    """
    Update a user.
    """
    user = await crud.read_user_by_id(session=session, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = await crud.read_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user = await crud.update_user(session=session, user=user, user_in=user_in)
    return user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
async def delete_user(session: SessionDep, user_id: PydanticObjectId, current_user: CurrentUser) -> Message:
    """
    Delete a user.
    """
    user = await crud.read_user_by_id(session=session, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    await crud.delete_user(session=session, user=user)
    return Message(message="User deleted successfully")
