"""Create a LiveKit room for the optional room/session demo.

Required environment variables:
    LIVEKIT_URL
    LIVEKIT_API_KEY
    LIVEKIT_API_SECRET

Optional:
    LIVEKIT_ROOM
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from livekit import api


def _load_env_files() -> None:
    root = Path(__file__).resolve().parents[1]
    for path in (root / "pipeline" / ".env", root / "livekit" / ".env"):
        if not path.exists():
            continue
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _require_env(names: list[str]) -> None:
    missing = [name for name in names if not os.getenv(name)]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"Missing required environment variable(s): {joined}")


def _room_name() -> str:
    return os.getenv("LIVEKIT_ROOM", "aurora-demo-room")


async def main() -> None:
    _load_env_files()
    _require_env(["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"])
    room_name = _room_name()
    try:
        async with api.LiveKitAPI() as lkapi:
            room = await lkapi.room.create_room(
                api.CreateRoomRequest(
                    name=room_name,
                    empty_timeout=10 * 60,
                    max_participants=10,
                )
            )
    except Exception as exc:
        print(f"failed to create room {room_name!r}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"created room: {room.name}")


if __name__ == "__main__":
    asyncio.run(main())
