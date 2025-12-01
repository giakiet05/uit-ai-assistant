from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional

from ..models.user_model import User
from .base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """
        Get a user by email.
        """
        statement = select(self.model).filter(self.model.email == email)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

# Create a singleton instance of the repository
user_repository = UserRepository(User)
