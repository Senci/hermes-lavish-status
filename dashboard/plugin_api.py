"""lavish-status backend, mounted at /api/plugins/lavish-status/.

GET /summary returns the block and decide counts, the sessions board URL and the pages behind them,
read from ~/.hermes/lavish-kit/summary.json (written every 5 s by lavish-kit's hx-status.py). The
file is only read. A missing, unreadable or stale file gives the empty payload with fresh=false.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

STALE_SECONDS = 30
WAITING = ("block", "decide")


def _summary_path() -> Path:
    # The kit writes under the real home, not the active profile's HERMES_HOME.
    return Path.home() / ".hermes" / "lavish-kit" / "summary.json"


def _empty() -> dict:
    return {"fresh": False, "counts": {k: 0 for k in WAITING}, "board_url": "", "pages": []}


def read_summary(now: float | None = None) -> dict:
    try:
        raw = json.loads(_summary_path().read_text(encoding="utf-8"))
        at = float(raw["at"])
    except (OSError, ValueError, KeyError, TypeError):
        return _empty()
    if (time.time() if now is None else now) - at > STALE_SECONDS:
        return _empty()
    counts = raw.get("counts") if isinstance(raw.get("counts"), dict) else {}
    pages = [
        {"key": p.get("key"), "url": p.get("url"), "title": p.get("title"), "attn": p["attn"]}
        for p in raw.get("pages") or []
        if isinstance(p, dict) and p.get("attn") in WAITING
    ]
    board = raw.get("board_url")
    return {
        "fresh": True,
        "counts": {k: int(counts.get(k) or 0) for k in WAITING},
        "board_url": board if isinstance(board, str) and board.startswith(("http://", "https://")) else "",
        "pages": pages,
    }


@router.get("/summary")
def get_summary():
    return read_summary()
