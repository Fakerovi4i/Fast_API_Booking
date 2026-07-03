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

from app.admin.auth import authentication_backend
from app.admin.views import BookingsAdmin, HotelsAdmin, RoomsAdmin, UsersAdmin
from app.bookings.router import router as router_bookings
from app.config import settings
from app.database import engine
from app.hotels.router import router_admin_hotels, router_hotels
from app.images.router import router as router_images
from app.hotels.importer.router import router as router_importer
# from app.logger import logger
from app.pages.router import router as router_pages
from app.users.router import router_auth, router_user


# === Lifespan ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    redis = aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}", encoding="utf-8", decode_responses=True
    )
    FastAPICache.init(RedisBackend(redis), prefix="cache")
    yield
    # Shutdown
    await redis.close()


# === Создание приложения (ОДИН раз!) ===
app = FastAPI(
    default_response_class=ORJSONResponse,
    lifespan=lifespan
)


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
origins = ["http://localhost:3000"]



# ====== Sentry =====
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    send_default_pii=True,
)

# ==== LOGGER =====
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
#     allow_headers=[
#         "Content-Type", "Authorization", "Set-Cookie",
#         "Access-Control-Allow-Headers", "Access-Control-Allow-Origin",
#         "Access-Control-Allow-Credentials"
#     ]
# )

# @app.middleware("http")
# async def log_request(request: Request, call_nex):
#     start_time = time.time()
#     response = await call_nex(request)
#     process_time = time.time() - start_time
#     logger.info("Request handling time", extra={
#         "process_time": round(process_time, 4)
#     })
#     return response




# === Тестовый эндпоинт ===
@app.get("/test")
@cache(expire=60)
async def test():
    return {"message": "cached!"}