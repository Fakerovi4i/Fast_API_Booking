import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis
from sqladmin import Admin
import sentry_sdk
from sqlalchemy import text

from app.admin.auth import authentication_backend
from app.admin.views import BookingsAdmin, HotelsAdmin, RoomsAdmin, UsersAdmin
from app.bookings.router import router as router_bookings
from app.config import settings
from app.database import engine
from app.hotels.router import router_admin_hotels, router_hotels
from app.images.router import router as router_images
from app.importer.router import router as router_importer
from app.logger import logger
from app.pages.router import router as router_pages
from app.users.router import router_auth, router_user

from app.exceptions import BookingException



# ====== Sentry =====
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    send_default_pii=True,
)


# === Lifespan ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Проверка БД
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
    except Exception as e:
        logger.critical(f"Database connection failed: {e}")


    logger.info("Starting application...", extra={"event": "startup"})
    redis = aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}", encoding="utf-8", decode_responses=True
    )
    FastAPICache.init(RedisBackend(redis), prefix="cache")
    logger.info("Application startup complete", extra={"event": "startup"})
    yield

    # Shutdown
    logger.info("Application shutdown initiated", extra={"event": "shutdown"})
    await redis.close()
    logger.info("Application shutdown complete", extra={"event": "shutdown"})


# === Создание приложения ===
app = FastAPI(
    default_response_class=ORJSONResponse,
    lifespan=lifespan
)

# === Глобальные обработчики исключений ===
@app.exception_handler(BookingException)
async def booking_exception_handler(request: Request, exc: BookingException):
    logger.error(
        f"ERROR: {exc.detail}",
        exc_info=True,
        extra={"path": request.url.path, "status_code": exc.status_code}
    )
    return ORJSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.critical(
        f"UNEXPECTED ERROR: {type(exc).__name__}: {exc}",
        extra={"path": request.url.path}
    )
    return ORJSONResponse(status_code=500, content={"detail": "INTERNAL SERVER ERROR"})





# === Админка ===
admin = Admin(app, engine=engine, authentication_backend=authentication_backend)
admin.add_view(UsersAdmin)
admin.add_view(HotelsAdmin)
admin.add_view(RoomsAdmin)
admin.add_view(BookingsAdmin)


# === Static files ===
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# === Routers ===
app.include_router(router_auth)
app.include_router(router_user)
app.include_router(router_bookings)
app.include_router(router_hotels)
app.include_router(router_admin_hotels)
app.include_router(router_pages)
app.include_router(router_images)
app.include_router(router_importer)


# === CORS ===
origins = ["http://localhost:3000"] # Разрешенные домены которые могут делать запросы
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type", "Authorization", "Set-Cookie",
        "Access-Control-Allow-Headers", "Access-Control-Allow-Origin",
        "Access-Control-Allow-Credentials"
    ]
)


# === Logger показывает время обработки запроса ===
@app.middleware("http")
async def log_request(request: Request, call_nex):
    start_time = time.time()
    response = await call_nex(request)
    process_time = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} {response.status_code}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),  # читаемые русские буквы
            "status_code": response.status_code,
            "process_time": round(process_time, 4),
        }
    )

    # Медленные запросы отдельно в WARNING
    if process_time > 1.0:
        logger.warning(
            "Slow request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "process_time": round(process_time, 4),
            }
        )

    return response


# === Тестовый эндпоинт для проверки кэша redis ===
@app.get("/test")
@cache(expire=60)
async def test():
    return {"message": "cached!"}