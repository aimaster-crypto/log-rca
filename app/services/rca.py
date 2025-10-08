from __future__ import annotations
from typing import Dict, Any, List
from . import db_ingest
from .vector_store import query_similar
from .llm import generate_rca


def analyze_correlation(correlation_id: str) -> Dict[str, Any]:
    logs = db_ingest.fetch_logs_by_correlation(correlation_id)

    # Retrieve contexts using log messages as queries
    queries = [l.get("message", "") for l in logs if l.get("message")]
    retrieved: List[str] = []
    if queries:
        results = query_similar(queries, top_k=5)
        for group in results:
            for item in group[:2]:  # take top 2 per log
                retrieved.append(item.get("document", ""))

    rca_text = generate_rca(logs, retrieved)

    return {
        "correlation_id": correlation_id,
        "log_count": len(logs),
        "logs": logs,
        "context_count": len(retrieved),
        "rca": rca_text,
    }
