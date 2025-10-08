from __future__ import annotations
import os
import re
import hashlib
import logging
import time
from typing import List, Dict
from ..config import settings
from .vector_store import get_collection, upsert_documents


LOG_PATTERN = re.compile(settings.LOG_REGEX)
logger = logging.getLogger(__name__)


def _read_file(fp: str) -> List[str]:
    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
        return f.readlines()


def _extract_snippets(java_path: str) -> List[Dict]:
    logger.info("Scanning Java path for log statements: %s", java_path)
    snippets: List[Dict] = []
    java_files = 0
    total_matches = 0
    for root, _, files in os.walk(java_path):
        for fn in files:
            if not fn.endswith(".java"):
                continue
            fp = os.path.join(root, fn)
            java_files += 1
            try:
                lines = _read_file(fp)
            except Exception as e:
                logger.warning("Failed to read file %s: %s", fp, e)
                continue

            joined = "".join(lines)
            # find log invocation positions by regex on joined text, then map to line numbers
            for match in LOG_PATTERN.finditer(joined):
                # Find the starting index and map to an approximate line number
                start_idx = match.start()
                # Approx line via counting newlines up to start_idx
                prefix = joined[:start_idx]
                approx_line = prefix.count("\n")

                start = max(0, approx_line - settings.CONTEXT_WINDOW)
                end = min(len(lines), approx_line + settings.CONTEXT_WINDOW)
                context = "".join(lines[start:end])
                message_group = match.group(0)
                snippet_text = f"File: {fp}\nLines: {start}-{end}\nMatch: {message_group}\n\nContext:\n{context}"
                doc_id = hashlib.sha1(snippet_text.encode("utf-8")).hexdigest()
                snippets.append({
                    "id": doc_id,
                    "text": snippet_text,
                    "metadata": {
                        "file": fp,
                        "range": f"{start}-{end}",
                        "type": "java_log_context"
                    }
                })
                total_matches += 1
            if total_matches:
                logger.debug("File %s: cumulative matches so far: %d", fp, total_matches)
    logger.info("Completed scan. Java files: %d, matches: %d, snippets: %d", java_files, total_matches, len(snippets))
    return snippets


def scan_and_index(java_path: str | None = None) -> int:
    # allow override path from UI; fallback to env
    java_path = (java_path or settings.JAVA_CODE_PATH).strip()
    if not java_path:
        logger.error("scan_and_index called with empty java_path")
        return 0
    if not os.path.exists(java_path):
        logger.error("Provided java_path does not exist: %s", java_path)
        return 0

    start_ts = time.time()
    logger.info("Starting index build from path: %s", java_path)
    snippets = _extract_snippets(java_path)
    if not snippets:
        logger.warning("No snippets extracted from %s. Check LOG_REGEX or source path.", java_path)
        return 0

    try:
        upsert_documents(snippets)
        took = time.time() - start_ts
        logger.info("Indexed %d documents to collection '%s' in %.2fs", len(snippets), settings.CHROMA_COLLECTION, took)
        return len(snippets)
    except Exception as e:
        logger.exception("Failed to upsert documents to vector store: %s", e)
        return 0
