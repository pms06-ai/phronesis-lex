"""
Authentication module for Phronesis LEX FastAPI backend.
Simple JWT-based authentication for single-user setup.
"""
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel


# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))

# Single user credentials (for personal use)
# Set these in environment variables or they'll be auto-generated
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer(auto_error=False)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class User(BaseModel):
    username: str
    is_active: bool = True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, datetime]:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expire


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user."""
    if username != ADMIN_USERNAME:
        return None

    # If no password hash is set, generate one and print it
    global ADMIN_PASSWORD_HASH
    if not ADMIN_PASSWORD_HASH:
        # First time setup - use a default password
        default_password = os.getenv("ADMIN_PASSWORD", "phronesis2024")
        ADMIN_PASSWORD_HASH = get_password_hash(default_password)
        print(f"\n{'='*60}")
        print("FIRST TIME SETUP - Authentication Configured")
        print(f"Username: {ADMIN_USERNAME}")
        print(f"Password: {default_password}")
        print("Set ADMIN_PASSWORD_HASH env var with the hash below for production:")
        print(f"ADMIN_PASSWORD_HASH={ADMIN_PASSWORD_HASH}")
        print(f"{'='*60}\n")

    if not verify_password(password, ADMIN_PASSWORD_HASH):
        return None

    return User(username=username)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """
    Get current authenticated user from JWT token.

    For personal use, this can be disabled by setting AUTH_DISABLED=true
    """
    # Allow disabling auth for local development
    if os.getenv("AUTH_DISABLED", "").lower() == "true":
        return User(username="local_user")

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(username=username)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token_data.username != ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return User(username=token_data.username)


# Optional dependency for endpoints that can work without auth
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if os.getenv("AUTH_DISABLED", "").lower() == "true":
        return User(username="local_user")

    if credentials is None:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
