from datetime import datetime, timezone
from src.config import conversations


async def load_session(session_id: str) -> dict | None:
    return await conversations.find_one({"session_id": session_id}, {"_id": 0})


async def save_session(session_id: str, state: dict) -> None:
    now = datetime.now(timezone.utc)
    state["updated_at"] = now
    await conversations.update_one(
        {"session_id": session_id},
        {"$set": state, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
