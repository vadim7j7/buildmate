"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables
from app.routers.todo_router import router as todo_router

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown.

    Creates database tables on startup.
    """
    await create_tables()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Todo API",
        description="A simple Todo application API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(todo_router, prefix="/api/v1")

    return app


app = create_app()
