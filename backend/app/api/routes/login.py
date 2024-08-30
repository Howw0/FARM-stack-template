from datetime import timedelta
from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.db import crud
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core import security
from app.config import settings
from app.core.security import get_password_hash
from app.models import Message, NewPassword, Token, UserPublic
from app.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)


router = APIRouter()


@router.post("/login/access-token")
async def login_access_token(session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = await crud.authenticate(session=session, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(access_token=await security.create_access_token(user.id, expires_delta=access_token_expires))


@router.post("/login/test-token", response_model=UserPublic)
async def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}")
async def recover_password(session: SessionDep, email: str) -> Message:
    """
    Password Recovery
    """
    user = await crud.read_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    password_reset_token = await generate_password_reset_token(email=email)
    email_data = await generate_reset_password_email(email_to=user.email, email=email, token=password_reset_token)
    await send_email(
        email_to=user.email, 
        subject=email_data.subject, 
        html_content=email_data.html_content
    )
    return Message(message="Password recovery email sent")


@router.post("/reset-password/")
async def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """
    Reset password
    """
    email = await verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = await crud.read_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    user.hashed_password = await get_password_hash(password=body.new_password)
    await user.save()
    return Message(message="Password updated successfully")


@router.post(
    "/password-recovery-html-content/{email}", 
    dependencies=[Depends(get_current_active_superuser)], 
    response_class=HTMLResponse
)
async def recover_password_html_content(session: SessionDep, email: str) -> Any:
    """
    HTML Content for Password Recovery
    """
    user = await crud.read_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = await generate_password_reset_token(email=email)
    email_data = await generate_reset_password_email(
        email_to=user.email, 
        email=email, 
        token=password_reset_token
    )
    return HTMLResponse(content=email_data.html_content, headers={"subject:": email_data.subject})