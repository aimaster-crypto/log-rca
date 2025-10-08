from __future__ import annotations
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from ..config import settings


def _engine():
    if not settings.DB_URL:
        return None
    return create_engine(settings.DB_URL, pool_pre_ping=True)


def fetch_logs_by_correlation(correlation_id: str) -> List[Dict[str, Any]]:
    if not correlation_id:
        return []
    # Development mode: return dummy logs when enabled or DB not configured
    if settings.USE_DUMMY_LOGS or not settings.DB_URL:
        base = datetime.utcnow()
        mk = lambda i, lvl, msg, logger: {
            "ts": (base + timedelta(seconds=i)).isoformat() + "Z",
            "level": lvl,
            "logger": logger,
            "message": msg,
            "correlation_id": correlation_id,
        }
        return [
            mk(0, "INFO", f"Received request with correlation {correlation_id}", "com.example.api.Gateway"),
            mk(1, "INFO", "Calling UserService.getUserDetails", "com.example.service.UserService"),
            mk(2, "WARN", "Cache miss for userId=42", "com.example.cache.UserCache"),
            mk(3, "ERROR", "NullPointerException at UserAssembler.map(User.java:87)", "com.example.assembler.UserAssembler"),
            mk(4, "INFO", "Request completed with status=500", "com.example.api.Gateway"),
        ]

    eng = _engine()
    if not eng:
        # DB URL present but engine not created; return empty
        return []

    sql = text(
        f"""
        SELECT 
            {settings.COL_TIMESTAMP} AS ts,
            {settings.COL_LEVEL} AS level,
            {settings.COL_LOGGER} AS logger,
            {settings.COL_MESSAGE} AS message,
            {settings.COL_CORRELATION_ID} AS correlation_id
        FROM {settings.LOG_TABLE}
        WHERE {settings.COL_CORRELATION_ID} = :cid
        ORDER BY {settings.COL_TIMESTAMP} ASC
        """
    )
    with eng.connect() as conn:
        rows = conn.execute(sql, {"cid": correlation_id}).mappings().all()
    logs = [dict(r) for r in rows]
    return logs
