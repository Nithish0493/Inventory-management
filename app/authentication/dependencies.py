import uuid
import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session


from security import decode_access_token
from tests.database_models import User
from app.database import get_db
from tests.database_models import User

bearer_scheme = HTTPBearer(auto_error=False)



# -------------------------
# Get current authenticated user
# -------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )
    token = credentials.credentials
    
    try:
        payload = decode_access_token(token)

        user_id = uuid.UUID(payload["sub"])

    except (jwt.InvalidTokenError, ValueError, KeyError):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    user_status = getattr(user.status, "value", user.status)

    if user_status != "active":
        raise HTTPException(
            status_code=403,
            detail="Your account is inactive"
        )

    return user


# -------------------------
# Role authorization
# -------------------------

def require_roles(*allowed_roles):

    def role_checker(
        current_user: User = Depends(get_current_user)
    ):

        user_role = getattr(current_user.role,"value",current_user.role)

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to perform this action"
            )

        return current_user

    return role_checker