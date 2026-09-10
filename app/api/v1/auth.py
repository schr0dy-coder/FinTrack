"""Authentication API Endpoints."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register_user(
    user_in: UserRegister,
    db: Session = Depends(get_db),
) -> User:
    """Register a new customer account with name, email, and password."""
    auth_service = AuthService(db)
    return auth_service.register(user_in, role="USER")


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate and receive JWT access token",
)
async def login(
    request: Request,
    db: Session = Depends(get_db),
) -> Token:
    """
    Authenticate with email and password.
    Supports both JSON body and OAuth2 form-urlencoded submissions.
    """
    auth_service = AuthService(db)
    content_type = request.headers.get("content-type", "")

    if "application/x-www-form-urlencoded" in content_type:
        form_data = await request.form()
        username = str(form_data.get("username", ""))
        password = str(form_data.get("password", ""))
        login_in = UserLogin(email=username, password=password)
    else:
        json_data = await request.json()
        login_in = UserLogin(**json_data)

    return auth_service.authenticate(login_in)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """Retrieve details of the currently authenticated user."""
    return current_user
