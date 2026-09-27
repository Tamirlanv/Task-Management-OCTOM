from typing import cast

from fastapi import APIRouter, Request, Response
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.pool import QueuePool

from app.core.metrics import Metrics

router = APIRouter()


@router.get("/metrics", include_in_schema=False)
async def metrics(request: Request) -> Response:
    counters = cast(Metrics, request.app.state.metrics)
    engine = cast(AsyncEngine, request.app.state.engine)
    pool = cast(QueuePool, engine.pool)
    return Response(
        counters.render(pool.checkedout(), pool.size()),
        media_type="text/plain; version=0.0.4",
    )
