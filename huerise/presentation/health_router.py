from typing import Literal

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


health_router = APIRouter(tags=["health"], route_class=DishkaRoute)


@health_router.get("/health", response_model=HealthResponse, operation_id="health")
async def health() -> HealthResponse:
    return HealthResponse()


@health_router.get("/ready", response_model=HealthResponse, operation_id="readiness")
async def readiness(engine: FromDishka[AsyncEngine]) -> HealthResponse:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from error

    return HealthResponse()
