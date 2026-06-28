"""FastAPI surface for the Morpho vault backend.

Run:  uvicorn app:app --reload --port 8002
Docs: http://localhost:8002/docs
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from morpho.service import MorphoService

app = FastAPI(title="YIELD Morpho backend", version="0.1.0")
_service: MorphoService | None = None


def service() -> MorphoService:
    global _service
    if _service is None:
        _service = MorphoService()
    return _service


class AmountRequest(BaseModel):
    amount_usdc: float = Field(..., gt=0, examples=[100])


def _guard(e: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=str(e))


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/info")
def info(owner: str | None = None) -> dict:
    try:
        return service().info(owner)
    except Exception as e:
        raise _guard(e)


@app.post("/deposit")
def deposit(req: AmountRequest) -> dict:
    try:
        return service().deposit(req.amount_usdc)
    except Exception as e:
        raise _guard(e)


@app.post("/withdraw")
def withdraw(req: AmountRequest) -> dict:
    try:
        return service().withdraw(req.amount_usdc)
    except Exception as e:
        raise _guard(e)
