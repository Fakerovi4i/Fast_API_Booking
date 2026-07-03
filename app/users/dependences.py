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
from app.users.models import Users


def get_token(request: Request):
    token = request.cookies.get("booking_access_token")

    # ДОБАВЛЯЕМ ОТЛАДОЧНЫЙ ВЫВОД
    # print(f"=== ПОЛУЧЕНИЕ ТОКЕНА ИЗ COOKIE ===")
    # print(f"Токен есть: {bool(token)}")
    # if token:
        # print(f"Токен: {token[:50]}...")  # Показываем первые 50 символов
    # print(f"===================================")

    if not token:
        raise TokenAbsentException
    return token


async def get_current_user(token: str = Depends(get_token)):
    try:

        # ДОБАВЛЯЕМ ОТЛАДОЧНЫЙ ВЫВОД
        # print(f"=== ДЕКОДИРОВАНИЕ ТОКЕНА ===")
        # print(f"Токен для декодирования: {token[:50]}...")

        payload = jwt.decode(token, settings.SECRET_KEY, settings.ALGORITHM)

        # print(f"Декодированный payload: {payload}")
        # print(f"==============================")

    except JWTError as e:
        # print(f"ОШИБКА ДЕКОДИРОВАНИЯ: {e}")
        raise IncorrectTokenFormatException

    expire = payload.get("exp")
    now = datetime.now(timezone.utc).timestamp()

    # ДОБАВЛЯЕМ ОТЛАДОЧНЫЙ ВЫВОД
    # print(f"=== ПРОВЕРКА СРОКА ДЕЙСТВИЯ ===")
    # print(f"exp (из токена): {expire}")
    # print(f"Текущее время (timestamp): {now}")
    # print(f"Разница (сек): {expire - now if expire else 'N/A'}")
    # print(f"Токен истек: {expire and int(expire) < now}")
    # print(f"=================================")

    if not expire:
        # print("ОШИБКА: Нет поля exp")
        raise TokenExpiredException

    if int(expire) < now:
        raise TokenExpiredException

    user_id: str = payload.get("sub")
    # print(f"user_id из токена: {user_id}")

    if not user_id:
        print("ОШИБКА: Нет user_id в токене")
        raise UserNotFoundException

    user = await UserDAO.find_by_id(int(user_id))
    if not user:
        # print(f"ОШИБКА: Пользователь с id {user_id} не найден")
        raise UserNotFoundException

    # print(f"УСПЕХ: Пользователь {user.email} авторизован")
    return user


# async def get_current_admin_user(current_user: Users = Depends(get_current_user)):
#     # if current_user.role != "admin": #В базе нет, так что просто для понимния
#         # raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
#     return current_user