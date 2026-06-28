"""FastAPI surface for the Alpaca commodity-ETF options backend.

Run:  uvicorn app_alpaca:app --reload --port 8001
Docs: http://localhost:8001/docs
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from alpaca.client import AlpacaClient, AlpacaError
from alpaca.service import AlpacaHedgeService

client: AlpacaClient
service: AlpacaHedgeService


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, service
    client = AlpacaClient()
    service = AlpacaHedgeService(client)
    yield
    await client.aclose()


app = FastAPI(title="YIELD Alpaca backend", version="0.1.0", lifespan=lifespan)


class InferRequest(BaseModel):
    line_items: list[str] = Field(..., description="bank statement / AP line-item texts")


class OptionHedge(BaseModel):
    ticker: str = Field(..., examples=["USO"])
    right: str = Field(..., examples=["P", "C"])
    quantity: int = Field(..., gt=0)
    side: str = "buy"
    strike: float | None = None
    expiration: str | None = Field(None, examples=["2026-09-18"])
    order_type: str = "limit"
    limit_price: float | None = None
    tif: str = "day"


class Collar(BaseModel):
    ticker: str = Field(..., examples=["USO"])
    quantity: int = Field(..., gt=0)
    put_strike: float
    call_strike: float
    expiration: str | None = None
    limit_price: float | None = None
    tif: str = "day"


def _guard(e: Exception) -> HTTPException:
    if isinstance(e, AlpacaError):
        return HTTPException(status_code=502, detail=str(e))
    return HTTPException(status_code=400, detail=str(e))


@app.get("/health")
async def health() -> dict:
    return {"ok": True}

@app.get("/account")
async def account() -> dict:
    try:
        return await service.account()
    except Exception as e:
        raise _guard(e)

@app.get("/instruments")
async def instruments() -> list[dict]:
    return service.instruments()

@app.post("/infer")
async def infer(req: InferRequest) -> dict:
    return service.infer(req.line_items)

@app.get("/positions")
async def positions() -> object:
    try:
        return await service.positions()
    except Exception as e:
        raise _guard(e)

@app.get("/chain/{ticker}")
async def chain(ticker: str, right: str | None = None,
                expiration_date_gte: str | None = None) -> dict:
    try:
        return await service.chain(ticker, right, expiration_date_gte)
    except Exception as e:
        raise _guard(e)

@app.post("/hedge/option")
async def hedge_option(req: OptionHedge) -> dict:
    try:
        return await service.hedge_option(**req.model_dump())
    except Exception as e:
        raise _guard(e)

@app.post("/hedge/collar")
async def hedge_collar(req: Collar) -> dict:
    try:
        return await service.hedge_collar(**req.model_dump())
    except Exception as e:
        raise _guard(e)

@app.get("/orders")
async def orders() -> object:
    try:
        return await client.list_orders()
    except Exception as e:
        raise _guard(e)

@app.delete("/orders/{order_id}")
async def cancel(order_id: str) -> object:
    try:
        return await client.cancel_order(order_id)
    except Exception as e:
        raise _guard(e)
