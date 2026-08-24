"""Authentication endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    summary="Register a new user",
    description=(
        "Create a new user account with a CUSTOMER, AGENT, or ADMIN role. "
        "Passwords are hashed with Argon2 and never stored in plaintext."
    ),
    responses={
        201: {"description": "User created successfully"},
        409: {"description": "Email already registered"},
    },
)
async def register(
    data: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    service = AuthService(db)
    user = await service.register(data)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and obtain JWT tokens",
    description="Authenticate with email and password. Returns access + refresh tokens.",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
    },
)
async def login(
    data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    service = AuthService(db)
    return await service.login(data)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Use a valid refresh token to obtain a new access + refresh token pair.",
    responses={
        200: {"description": "Tokens refreshed"},
        401: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh_token(
    data: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    service = AuthService(db)
    return await service.refresh(data.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns the profile of the currently authenticated user.",
    responses={
        200: {"description": "Current user profile"},
        401: {"description": "Not authenticated"},
    },
)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)
