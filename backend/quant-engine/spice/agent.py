"""The live orchestrator: one Claude Opus 4.8 agent loop, streaming.

Confirmed against the Anthropic Python SDK: messages.stream(...) with tools +
adaptive thinking, accumulate text per content block, get_final_message() to
read tool_use blocks, loop until stop_reason != "tool_use". Each text block and
tool call is emitted as an SSE event (with a `who` specialist label). The agent
places the hedges and then stops at "watching the oracle" — the operator fires
the climax (handled by the server), reusing the scripted payout tail.
"""

from __future__ import annotations

import json
import os

from . import tools as T
from .company_view import company_view

MODEL = "claude-opus-4-8"

SYSTEM = """You are Spice, an autonomous risk desk that runs an ordinary business's \
finances like a trading desk. You route work through three specialists: a Risk agent \
(analysis), a Hedging agent (options + insurance), and a Placement agent (yield).

Run this exact sequence, one tool at a time, narrating each step in ONE short sentence:
1. analyze_exposure — reveal the hidden commodity exposure and the current margin.
2. run_shock — stress it with the scenario shock and state the margin + VaR hit.
3. hedge_options on the two biggest commodity exposures (wheat = WEAT, gas = UNG).
4. take_escrow_policy for the energy tail (premium ~1240, payout ~84000 USDC).
5. lend_morpho to supply ~180000 of idle cash and self-fund the premiums.

After all hedges are placed, say in one sentence that the hedges are live and you are \
watching the energy oracle, then STOP — do not narrate further. Be concise and concrete; \
no preamble, no markdown."""


def has_key() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY"))


async def run_agent(emit) -> None:
    """Drive the agent loop, emitting SSE events via `emit` (async callable)."""
    from anthropic import AsyncAnthropic  # lazy: keeps the mock path import-clean

    client = AsyncAnthropic()
    cv = company_view()
    messages: list[dict] = [{
        "role": "user",
        "content": (
            f"Run the desk on {cv['name']} (revenue €{cv['revenue']:,.0f}, "
            f"net margin {cv['net_margin'] * 100:.0f}%). Find the hidden commodity "
            f"exposure, stress it, and hedge it across the venues."
        ),
    }]

    for _ in range(8):  # bounded agent loop
        cur: list[str] | None = None
        async with client.messages.stream(
            model=MODEL, max_tokens=4000, thinking={"type": "adaptive"},
            system=SYSTEM, tools=T.TOOLS, messages=messages,
        ) as stream:
            async for event in stream:
                if event.type == "content_block_start" and getattr(event.content_block, "type", None) == "text":
                    cur = []
                elif event.type == "content_block_delta" and event.delta.type == "text_delta" and cur is not None:
                    cur.append(event.delta.text)
                elif event.type == "content_block_stop" and cur is not None:
                    txt = "".join(cur).strip()
                    if txt:
                        await emit({"type": "agent_message", "who": "Orchestrator", "text": txt})
                    cur = None
            final = await stream.get_final_message()

        messages.append({"role": "assistant", "content": final.content})
        tool_uses = [b for b in final.content if b.type == "tool_use"]
        if final.stop_reason != "tool_use" or not tool_uses:
            break

        results = []
        for tu in tool_uses:
            await emit({"type": "tool_call", "who": T.WHO.get(tu.name, "Orchestrator"),
                        "tool": tu.name, "input": tu.input})
            out = await T.dispatch(tu.name, tu.input, emit)
            results.append({"type": "tool_result", "tool_use_id": tu.id, "content": json.dumps(out)})
        messages.append({"role": "user", "content": results})
