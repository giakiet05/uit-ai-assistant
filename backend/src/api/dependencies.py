from typing import Generator, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from .repositories.user_repository import user_repository
from .dtos.auth_dto import TokenPayload
from .models.user_model import User
from .auth import security
from ..shared.config.settings import settings

# This is the scheme that will be used to get the token from the request
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api.API_V1_STR}/login/access-token"
)

# Dependency to get a database session for a single request
async def get_db() -> Generator[AsyncSession, None, None]:
    """
    FastAPI dependency that provides a SQLAlchemy asynchronous session.
    """
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)], 
    token: Annotated[str, Depends(reusable_oauth2)]
) -> User:
    """
    Dependency to get the current user from the JWT token.
    """
    try:
        payload = jwt.decode(
            token, settings.auth.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        ) from e
        
    if token_data.sub is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
        
    user = await user_repository.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user