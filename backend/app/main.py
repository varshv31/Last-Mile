"""Last-Mile Delivery Tracker — FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup / shutdown hooks."""
    # Future: initialise connection pools, schedulers, etc.
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Production-style REST API for a Last-Mile Delivery Tracker platform.\n\n"
            "## Authentication\n"
            "Use the `/api/v1/auth/login` endpoint to obtain a JWT access token, "
            "then click the **Authorize** button above and enter `Bearer <your-token>`.\n\n"
            "## Rate Calculation\n"
            "Call `POST /api/v1/orders/calculate` first to get a full price breakdown. "
            "Then call `POST /api/v1/orders` to confirm and create the order."
        ),
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    is_dev = settings.ENVIRONMENT == "development"
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_origin_regex=r"https?://.*:\d+" if is_dev else None,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handlers
    register_exception_handlers(app)

    # API routes
    app.include_router(api_v1_router)

    # Health check
    @app.get("/health", tags=["Health"], summary="Health check")
    async def health() -> dict:
        return {"status": "ok", "version": settings.APP_VERSION}

    # Custom OpenAPI schema with JWT security definition
    def custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter: Bearer <access_token>",
            }
        }
        for path in schema.get("paths", {}).values():
            for operation in path.values():
                if "security" not in operation:
                    operation["security"] = [{"BearerAuth": []}]
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]

    return app


app = create_app()
