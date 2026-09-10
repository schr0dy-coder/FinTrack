"""User Repository."""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Handles persistence operations for users."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.lower().strip())
        return self.db.scalars(stmt).first()

    def create(self, name: str, email: str, password_hash: str, role: str = "USER") -> User:
        user = User(
            name=name.strip(),
            email=email.lower().strip(),
            password_hash=password_hash,
            role=role.upper(),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        stmt = select(User).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count(self) -> int:
        stmt = select(func.count(User.id))
        return self.db.scalar(stmt) or 0
