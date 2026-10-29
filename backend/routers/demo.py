import asyncio
import random

from fastapi import APIRouter, Response

from common.config import config

router = APIRouter(tags=["demo"])


@router.get("/get_method")
async def get_method():
    # с вероятностью GET_METHOD_FAIL_RATE возвращаем 500
    if random.random() < config.GET_METHOD_FAIL_RATE:
        return Response("failed", status_code=500, media_type="text/plain")
    # с вероятностью GET_METHOD_FAST_RATE отвечаем быстро (0.1-0.9 с), иначе медленно (1.1-3 с)
    if random.random() < config.GET_METHOD_FAST_RATE:
        delay = random.uniform(0.1, 0.9)
    else:
        delay = random.uniform(1.1, 3)
    await asyncio.sleep(delay)
    return Response("ok", media_type="text/plain")