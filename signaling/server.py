# signaling/server.py
import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, List

import jwt as pyjwt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# ── Config ────────────────────────────────────────────────────────────────────
APP_JWT_SECRET   = os.environ.get("APP_JWT_SECRET",   "change-me")
APP_JWT_ISSUER   = os.environ.get("APP_JWT_ISSUER",   "my-thin-bridge")
APP_JWT_AUDIENCE = os.environ.get("APP_JWT_AUDIENCE", "my-attached-app")

DEFAULT_SPEAKER_TIME   = 60    # seconds
MOTION_PENDING_TIMEOUT = 30    # seconds
SECONDED_TIMEOUT       = 300   # 5 minutes
VOTE_CLOSED_DISPLAY    = 5     # seconds

# ── Dataclasses ───────────────────────────────────────────────────────────────
@dataclass
class Member:
    id: str
    name: str
    is_chair: bool = False
    hand_raised: bool = False

@dataclass
class Motion:
    text: str
    moved_by: str
    seconded_by: Optional[str] = None
    votes: Dict = field(default_factory=lambda: {"yea": 0, "nay": 0, "abstain": 0})
    member_votes: Dict = field(default_factory=dict)
    result: Optional[str] = None

@dataclass
class Room:
    room_id: str
    phase: str = "open"
    members: List = field(default_factory=list)
    speaker_queue: List = field(default_factory=list)
    current_speaker: Optional[str] = None
    timer_remaining: int = DEFAULT_SPEAKER_TIME
    speaker_time: int = DEFAULT_SPEAKER_TIME
    motion: Optional[Motion] = None
    # Saved state for restoring after motion_pending
    _prev_phase: Optional[str]   = field(default=None, repr=False)
    _prev_speaker: Optional[str] = field(default=None, repr=False)
    _prev_timer: int              = field(default=0,    repr=False)

# ── Global state (asyncio single-threaded — no locks needed) ─────────────────
rooms:         Dict[str, Room]                   = {}
connections:   Dict[str, Dict[str, WebSocket]]   = {}
_timer_tasks:  Dict[str, asyncio.Task]           = {}
_motion_tasks: Dict[str, asyncio.Task]           = {}

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# ── Auth ──────────────────────────────────────────────────────────────────────
def _validate_jwt(token: str) -> dict:
    return pyjwt.decode(
        token, APP_JWT_SECRET,
        algorithms=["HS256"],
        issuer=APP_JWT_ISSUER,
        audience=APP_JWT_AUDIENCE,
    )
