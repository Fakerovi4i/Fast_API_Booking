from typing import Optional

from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.config import settings
from app.logger import logger
from app.users.auth import authenticate_user, create_access_token
from app.users.dependences import get_current_user


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:

        form = await request.form()
        email, password = form.get("username"), form.get("password")

        try:
            logger.info(f"Попытка входа: {email}")
            user = await authenticate_user(email, password)
        except Exception as e:
            logger.error(f"Ошибка при вызове authenticate_user: {e}", exc_info=True)
            return False

        if not user:
            logger.info(f"Неудачный вход: {email}")
            return False

        try:
            logger.info(f"Успешный вход: {email}")
            access_token = create_access_token({"sub": str(user.id)})
        except Exception as e:
            logger.error(f"Ошибка при создании access token: {e}", exc_info=True)
            return False

        request.session.update({"token": access_token})
        return True


    async def logout(self, request: Request) -> bool:
        request.session.clear()
        logger.info("Выход пользователя")
        return True

    async def authenticate(self, request: Request) -> Optional[RedirectResponse]:
        token = request.session.get("token")
        if not token:
            return RedirectResponse(request.url_for("admin:login"), status_code=302)

        try:
            logger.info("Проверка авторизации пользователя")
            user = await get_current_user(token)
        except Exception as e:
            logger.error(f"Ошибка при проверке авторизации: {e}", exc_info=True)
            return RedirectResponse(request.url_for("admin:login"), status_code=302)

        if not user:
            logger.info("Неудачная проверка авторизации пользователя")
            return RedirectResponse(request.url_for("admin:login"), status_code=302)

        return None



authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)





