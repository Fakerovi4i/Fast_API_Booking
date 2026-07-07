"""
ПРИМЕР ДЛЯ ДИНАМИЧЕСКИХ ДАННЫХ:
    class BookingException(HTTPException):
        def __init__(self, status_code: int = 500, detail: str = ""):
            super().__init__(status_code=status_code, detail=detail)

    class UserNotFoundException(BookingException):
        def __init__(self, user_id: int = None):
            detail = f"Пользователь с id {user_id} не найден" if user_id else "Пользователь не найден"
            super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
"""

from fastapi import HTTPException, status

class BookingException(HTTPException):
    status_code = 500
    detail = ""

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)

class BookingNotFoundException(BookingException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Бронь не найдена"

class BookingNotBelongsToUserException(BookingException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Бронь не принадлежит пользователю"


class UserAlreadyExistsException(BookingException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Пользователь уже существует"

class IncorrectEmailOrPasswordException(BookingException):
    status_code=status.HTTP_401_UNAUTHORIZED
    detail="Неверный email или пароль"


class TokenExpiredException(BookingException):
    status_code=status.HTTP_401_UNAUTHORIZED
    detail="Token Истёк"

class TokenAbsentException(BookingException):
    status_code=status.HTTP_401_UNAUTHORIZED
    detail="Token отсутствует"

class IncorrectTokenFormatException(BookingException):
    status_code=status.HTTP_401_UNAUTHORIZED
    detail="Неверный формат token"

class UserNotFoundException(BookingException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Пользователь не найден"

class RoomCannotBeBookedException(BookingException):
    status_code=status.HTTP_409_CONFLICT
    detail="Нет свободных комнат"


class HotelAlreadyExistsException(BookingException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Отель уже существует"

class WrongDateException(BookingException):
    status_code=status.HTTP_400_BAD_REQUEST
    detail = "Дата заезда должна быть раньше даты выезда"

class HotelNotFoundException(BookingException):
        status_code = status.HTTP_404_NOT_FOUND
        detail = "Отель не найден"

class DatabaseErrorException(BookingException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Внутренняя ошибка базы данных"


