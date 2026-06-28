"""FastAPI surface for the YIELD AI-CFO agent.

The Claude agent (or the Next.js frontend) calls these clean intent endpoints;
the backend handles IBKR session, conid resolution, and the reply-confirm loop.

Run:  uvicorn app:app --reload --port 8000
Docs: http://localhost:8000/docs
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ibkr.client import IBKRClient, IBKRError
from ibkr.service import HedgeService

client: IBKRClient
service: HedgeService


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, service
    client = IBKRClient()
    service = HedgeService(client)
    yield
    await client.aclose()


app = FastAPI(title="YIELD IBKR backend", version="0.1.0", lifespan=lifespan)


# --- request models ----------------------------------------------------------
class InferRequest(BaseModel):
    line_items: list[str] = Field(..., description="invoice / AP line-item texts")


class FutureHedge(BaseModel):
    root: str = Field(..., examples=["ZW"])
    month: str = Field(..., description="MMMYY", examples=["SEP26"])
    side: str = Field(..., examples=["BUY", "SELL"])
    quantity: int = Field(..., gt=0)
    order_type: str = "MKT"
    price: float | None = None
    tif: str = "DAY"
    use_micro: bool = False


class OptionHedge(BaseModel):
    root: str = Field(..., examples=["CL"])
    month: str = Field(..., examples=["SEP26"])
    strike: float
    right: str = Field(..., examples=["C", "P"])
    side: str = Field(..., examples=["BUY", "SELL"])
    quantity: int = Field(..., gt=0)
    order_type: str = "LMT"
    price: float | None = None
    tif: str = "DAY"


def _guard(exc: Exception) -> HTTPException:
    if isinstance(exc, IBKRError):
        return HTTPException(status_code=502, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


# --- read --------------------------------------------------------------------
@app.get("/health")
async def health() -> dict:
    return {"ok": True}

@app.get("/session")
async def session() -> dict:
    try:
        return await service.session()
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

@app.get("/strikes/{root}/{month}")
async def strikes(root: str, month: str) -> dict:
    try:
        return await service.strikes(root, month)
    except Exception as e:
        raise _guard(e)


# --- write -------------------------------------------------------------------
@app.post("/hedge/future")
async def hedge_future(req: FutureHedge) -> dict:
    try:
        return await service.hedge_future(**req.model_dump())
    except Exception as e:
        raise _guard(e)

@app.post("/hedge/option")
async def hedge_option(req: OptionHedge) -> dict:
    try:
        return await service.hedge_option(**req.model_dump())
    except Exception as e:
        raise _guard(e)

@app.get("/orders")
async def orders() -> object:
    try:
        return await client.live_orders()
    except Exception as e:
        raise _guard(e)

@app.delete("/orders/{order_id}")
async def cancel(order_id: str) -> object:
    try:
        return await client.cancel_order(order_id)
    except Exception as e:
        raise _guard(e)
