"""Authentication Service."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.auth import Token, UserLogin, UserRegister


class AuthService:
    """Handles authentication and registration business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register(self, user_in: UserRegister, role: str = "USER") -> User:
        """Register a new user account."""
        existing = self.user_repo.get_by_email(user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )

        hashed_password = get_password_hash(user_in.password)
        user = self.user_repo.create(
            name=user_in.name,
            email=user_in.email,
            password_hash=hashed_password,
            role=role,
        )
        logger.info(f"User registered successfully: {user.email} (ID: {user.id})")
        return user

    def authenticate(self, login_in: UserLogin) -> Token:
        """Authenticate user credentials and return JWT access token."""
        user = self.user_repo.get_by_email(login_in.email)
        if not user or not verify_password(login_in.password, user.password_hash):
            logger.warning(f"Failed login attempt for email: {login_in.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(subject=user.id, role=user.role)
        logger.info(f"User authenticated: {user.email} (Role: {user.role})")

        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
        )
