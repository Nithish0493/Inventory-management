import uuid

from sqlalchemy import select, update
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from tests.database_models import User, RefreshToken
from auth import LoginRequest, TokenResponse
from security import REFRESH_TOKEN_EXPIRE_DAYS
from dependencies import get_db
from security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    get_refresh_token_expiry,
)

import os


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# Set COOKIE_SECURE=false for local HTTP development.
# Set COOKIE_SECURE=true in production with HTTPS.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

COOKIE_NAME = "refresh_token"
COOKIE_PATH = "/auth"


def set_refresh_cookie(response: Response, token: str):

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=COOKIE_PATH
    )


def clear_refresh_cookie(response: Response):

    response.delete_cookie(
        key=COOKIE_NAME,
        path=COOKIE_PATH,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax"
    )


def refresh_error(status_code: int, detail: str):

    result = JSONResponse(
        status_code=status_code,
        content={"detail": detail},
    )

    clear_refresh_cookie(result)

    return result


# -------------------------
# 1. LOGIN
# -------------------------

@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):

    # Find user by login_id
    user = db.query(User).filter(
        User.login_id == data.login_id
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid login ID or password"
        )

    # Verify password
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid login ID or password"
        )

    user_status = getattr(user.status, "value", user.status)

    # Check account status
    if user_status != "active":
        raise HTTPException(
            status_code=403,
            detail="Your account is inactive"
        )

    # Generate access token
    access_token = create_access_token(
        str(user.user_id)
    )

    # Generate opaque refresh token
    refresh_token = create_refresh_token()

    # Generate a new session ID for this login
    session_id = uuid.uuid4()

    # Store only the hash
    token_record = RefreshToken(
        session_id=session_id,
        user_id=user.user_id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=get_refresh_token_expiry()
    )

    db.add(token_record)
    db.commit()

    # Send actual refresh token in HttpOnly cookie
    set_refresh_cookie(response, refresh_token)

    return TokenResponse(
        access_token=access_token
    )


# -------------------------
# 2. REFRESH ACCESS TOKEN
# -------------------------

@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):

    old_refresh_token = request.cookies.get(COOKIE_NAME)

    if not old_refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Refresh token missing"
        )

    old_hash = hash_refresh_token(old_refresh_token)

    # Lock the token row while processing rotation
    old_record = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == old_hash)
        .with_for_update()
    )

    if old_record is None:
        return refresh_error(
            401,
            "Invalid refresh token",
        )   

    now = datetime.now(timezone.utc)

    # Detect reuse of an already-used or revoked token
    if old_record.revoked_at is not None:

        # Revoke all remaining tokens in this session
        db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.session_id == old_record.session_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )

        db.commit()

        return refresh_error(
            401,
            "Refresh token reuse detected. Please log in again.",
        )

    # Check expiry
    if old_record.expires_at <= now:

        old_record.revoked_at = now
        db.commit()

        return refresh_error(
            401,
            "Refresh token expired. Please log in again.",
        )


    # Check user status
    
    user = db.get(User, old_record.user_id)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    user_status = getattr(user.status, "value", user.status)


    if user_status != "active":
        db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.session_id == old_record.session_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )

        db.commit()

        return refresh_error(
            403,
            "Your account is inactive",
        )

    # Generate new refresh token
    new_refresh_token = create_refresh_token()

    new_record = RefreshToken(
        session_id=old_record.session_id,
        user_id=old_record.user_id,
        token_hash=hash_refresh_token(new_refresh_token),
        expires_at=get_refresh_token_expiry()
    )
    # Mark old token as used
    old_record.revoked_at = now
    db.add(new_record)

    # Generate new access JWT
    new_access_token = create_access_token(
        str(user.user_id)
    )

    db.commit()

    # Replace the refresh cookie
    set_refresh_cookie(response, new_refresh_token)

    return TokenResponse(
        access_token=new_access_token
    )


# -------------------------
# 3. LOGOUT
# -------------------------

@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):

    refresh_token = request.cookies.get(COOKIE_NAME)

    if refresh_token:

        token_hash = hash_refresh_token(refresh_token)

        record = db.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash
            )
        )


        if record is not None:

            now = datetime.now(timezone.utc)

            # Revoke all tokens belonging to this login session
            db.execute(
                update(RefreshToken)
                .where(
                    RefreshToken.session_id == record.session_id,
                    RefreshToken.revoked_at.is_(None),
                )
                .values(revoked_at=now)
            )

            db.commit()

    clear_refresh_cookie(response)

    return {
        "message": "Logged out successfully"
    }