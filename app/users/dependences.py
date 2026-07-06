"""
В реальном продакшене обязательно!!
async def get_current_admin_user(current_user: Users = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return current_user
"""

from datetime import datetime, timezone

from fastapi import Request, Depends
from jose import jwt, JWTError

from app.config import settings
from app.exceptions import (
    TokenExpiredException,
    TokenAbsentException,
    IncorrectTokenFormatException,
    UserNotFoundException
)

from app.users.dao import UserDAO


def get_token(request: Request):
    token = request.cookies.get("booking_access_token")

    if not token:
        raise TokenAbsentException
    return token


async def get_current_user(token: str = Depends(get_token)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, settings.ALGORITHM)

    except JWTError as e:
        raise IncorrectTokenFormatException

    expire = payload.get("exp")
    now = datetime.now(timezone.utc).timestamp()

    if not expire:
        raise TokenExpiredException

    if int(expire) < now:
        raise TokenExpiredException

    user_id: str = payload.get("sub")

    if not user_id:
        raise UserNotFoundException

    user = await UserDAO.find_by_id(int(user_id))
    if not user:
        raise UserNotFoundException

    return user

