"""FastAPI surface for the parametric-insurance escrow backend.

Run:  uvicorn app:app --reload --port 8003
Docs: http://localhost:8003/docs

Matches the orchestrator's :8003 contract (quant-engine/spice/tools.py):
  POST /policy  {premium_usdc, trigger_index, payout_usdc}
  POST /settle  {index_value}
  GET  /info
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from escrow.service import EscrowService

app = FastAPI(title="Spice parametric-insurance escrow", version="0.1.0")
_service: EscrowService | None = None


def service() -> EscrowService:
    global _service
    if _service is None:
        _service = EscrowService()
    return _service


class PolicyRequest(BaseModel):
    premium_usdc: float = Field(0, ge=0, examples=[1240])
    trigger_index: int = Field(..., examples=[35])      # heat index threshold
    payout_usdc: float = Field(..., gt=0, examples=[84000])
    insured: str | None = Field(None, description="payout recipient; defaults to the operator wallet")


class SettleRequest(BaseModel):
    index_value: int = Field(..., examples=[41])        # observed heat index
    policy_id: int | None = None


def _guard(e: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=str(e))


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/info")
def info(policy_id: int | None = None) -> dict:
    try:
        return service().info(policy_id)
    except Exception as e:
        raise _guard(e)


@app.post("/policy")
def policy(req: PolicyRequest) -> dict:
    try:
        return service().policy(req.premium_usdc, req.trigger_index, req.payout_usdc, req.insured)
    except Exception as e:
        raise _guard(e)


@app.post("/settle")
def settle(req: SettleRequest) -> dict:
    try:
        return service().settle(req.index_value, req.policy_id)
    except Exception as e:
        raise _guard(e)
