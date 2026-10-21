import os
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User

SESSION_USER_ID_KEY = "user_id"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_session_secret() -> str:
    return os.environ.get("SESSION_SECRET", "fake-content-detection-dev-secret-change-in-production")


def login_user(request: Request, user: User) -> None:
    request.session[SESSION_USER_ID_KEY] = user.id


def logout_user(request: Request) -> None:
    request.session.clear()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    user_id: Optional[int] = request.session.get(SESSION_USER_ID_KEY)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user
