import sentry_sdk
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.db import get_session, init_db
from app.api import api_router


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async for session in get_session():
        await init_db(session=session)
    yield


app = FastAPI(title=settings.PROJECT_NAME, 
              openapi_url=f"{settings.API_V1_STR}/openapi.json",
              generate_unique_id_function=custom_generate_unique_id,
              lifespan=lifespan
              )


if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.include_router(router=api_router, prefix=settings.API_V1_STR)