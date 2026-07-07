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
            logger.info(f"TRYING TO LOGIN ADMIN: {email}")
            user = await authenticate_user(email, password)
        except Exception as e:
            logger.error(f"AUTH ERROR: {e}", exc_info=True)
            return False

        if not user:
            logger.info(f"AUTH ADMIN ERROR NO USER: {email}")
            return False

        try:
            logger.info(f"ADMIN LOGIN SUCCESS: {email}")
            access_token = create_access_token({"sub": str(user.id)})
        except Exception as e:
            logger.error(f"ADMIN AUTH ERROR CREATE ACCESS TOKEN: {e}", exc_info=True)
            return False

        request.session.update({"token": access_token})
        return True


    async def logout(self, request: Request) -> bool:
        request.session.clear()
        logger.info("ADMIN LOGOUT")
        return True

    async def authenticate(self, request: Request) -> Optional[RedirectResponse]:
        try:
            token = request.session.get("token")
            if not token:
                logger.info("NO TOKEN IN SESSION")
                return RedirectResponse(request.url_for("admin:login"), status_code=302)
            user = await get_current_user(token)
            if not user:
                logger.info("ADMIN AUTH ERROR NO USER")
                return RedirectResponse(request.url_for("admin:login"), status_code=302)
        except Exception as e:
            logger.error(f"ADMIN AUTH ERROR: {e}", exc_info=True)
            return RedirectResponse(request.url_for("admin:login"), status_code=302)

        return None

authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)





