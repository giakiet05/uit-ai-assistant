from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from .. import dependencies
from ..auth import security
from ..repositories.user_repository import user_repository
from ..dtos import auth_dto

router = APIRouter()

@router.post("/login/access-token", response_model=auth_dto.AuthResponse)
async def login_access_token(
    db: Annotated[AsyncSession, Depends(dependencies.get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = await user_repository.get_by_email(db, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=400, detail="Incorrect email or password"
        )
    
    # Create access and refresh tokens
    access_token = security.create_access_token(subject=user.id)
    # TODO: Implement refresh token creation and storage
    refresh_token = "dummy_refresh_token_for_now"

    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
