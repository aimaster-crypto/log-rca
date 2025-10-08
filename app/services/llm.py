from __future__ import annotations
from typing import List, Dict, Any
from ..config import settings


def generate_rca(logs: List[Dict[str, Any]], contexts: List[str]) -> str:
    prompt = _build_prompt(logs, contexts)

    if settings.OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL or None)
            resp = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": (
                        "You are a senior SRE. Generate a professional RCA report in clean Markdown format. Use the following exact sections with detailed, actionable content:\n\n"
                        "# Summary\n"
                        "- Provide a brief overview of the incident and key findings.\n\n"
                        "# Timeline\n"
                        "- List 5-10 key events in chronological order using format: `- **YYYY-MM-DD HH:MM:SS** - [Level] - Logger: Message`\n"
                        "- Use **bold** for timestamps and levels.\n\n"
                        "# Root Cause\n"
                        "- Clearly state the primary cause with evidence from logs/context.\n\n"
                        "# Contributing Factors\n"
                        "- Bullet list of secondary factors (e.g., configuration, dependencies).\n\n"
                        "# Impact\n"
                        "- Describe the business/technical impact with metrics if available.\n\n"
                        "# Affected Components\n"
                        "- List components (e.g., services, classes) with brief descriptions.\n\n"
                        "# Recommended Fix\n"
                        "- Step-by-step remediation actions, including code/config changes.\n\n"
                        "# Preventive Actions\n"
                        "- Long-term measures like monitoring, alerts, and improvements.\n\n"
                        "Use bullet points, **bold** key terms, and keep it concise but specific. Ensure the Markdown renders well in a web UI."
                    )},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            return resp.choices[0].message.content
        except Exception as e:
            if settings.REQUIRE_LLM:
                return (
                    "# Summary\n- LLM generation failed.\n\n"
                    f"Error: {e}\n\n"
                    "Check OPENAI_BASE_URL, OPENAI_API_KEY, and LLM_MODEL (must be a chat-capable model)."
                )
            # else fall through to heuristic

    # If LLM is required but no API key is set, report explicitly
    if settings.REQUIRE_LLM and not settings.OPENAI_API_KEY:
        return (
            "# Summary\n- LLM is required but no API key is configured.\n\n"
            "Set OPENAI_API_KEY and (optionally) OPENAI_BASE_URL to a compatible endpoint, and use a chat model in LLM_MODEL."
        )

    # Fallback simple heuristic summary (only when REQUIRE_LLM is disabled)
    return _fallback_summary(logs, contexts)


def _build_prompt(logs: List[Dict[str, Any]], contexts: List[str]) -> str:
    log_lines = []
    for l in logs:
        ts = l.get("ts") or l.get("timestamp")
        lvl = l.get("level")
        msg = l.get("message")
        logger = l.get("logger")
        log_lines.append(f"[{ts}] {lvl} {logger}: {msg}")

    ctx_sample = "\n---\n".join(contexts[:10])

    prompt = (
        "You are given application logs with the same correlation ID and retrieved code/log snippets from a Java Spring app.\n"
        "Generate a precise RCA report using the sections defined in the system message. Follow these guidelines:\n"
        "- **Timeline**: Extract 5-10 key events in chronological order. Format each as `- **YYYY-MM-DD HH:MM:SS** - [Level] - Logger: Message` (use actual timestamps from logs).\n"
        "- **Affected Components**: Reference package/class names from context (e.g., com.example.api.Gateway).\n"
        "- **Recommended Fix & Preventive Actions**: Provide concrete, numbered steps for fixes and long-term measures.\n"
        "- **Overall**: Keep it professional, use **bold** for emphasis, and ensure clean Markdown that renders well in a web UI.\n\n"
        "Logs:\n" + "\n".join(log_lines) + "\n\nRetrieved Context:\n" + ctx_sample + "\n"
    )
    return prompt


def _fallback_summary(logs: List[Dict[str, Any]], contexts: List[str]) -> str:
    if not logs:
        return (
            "# Summary\n- No logs found for the correlation ID.\n\n"
            "# Timeline\n- N/A\n\n"
            "# Root Cause\n- Unknown due to missing logs.\n\n"
            "# Contributing Factors\n- Database not configured or empty result.\n\n"
            "# Impact\n- Unable to diagnose issue without logs.\n\n"
            "# Affected Components\n- Unknown\n\n"
            "# Recommended Fix\n- Verify DB_URL and schema; ensure logs are written for this correlation.\n\n"
            "# Preventive Actions\n- Add request-scoped logging and alerts when no logs are present.\n"
        )
    errors = [l for l in logs if str(l.get("level", "")).lower() in ("error", "fatal")] or [l for l in logs if "exception" in str(l.get("message", "")).lower()]
    timeline = []
    for l in logs[:10]:
        ts = l.get("ts") or l.get("timestamp")
        lvl = l.get("level")
        logger = l.get("logger")
        msg = l.get("message")
        timeline.append(f"- **{ts}** - [{lvl}] - {logger}: {msg}")
    md = [
        "# Summary",
        f"- Total logs analyzed: {len(logs)}; errors: {len(errors)}",
        "- Likely failing component: inspect last ERROR/Exception and related logger.",
        "",
        "# Timeline",
        *timeline,
        "",
        "# Root Cause",
        "- Suspected failure near last ERROR/Exception; see timeline and contexts.",
        "",
        "# Contributing Factors",
        "- Insufficient caching or null checks (suspected).",
        "",
        "# Impact",
        "- Request failed; user-facing 5xx observed.",
        "",
        "# Affected Components",
        "- Refer to involved loggers in timeline (services/assemblers).",
        "",
        "# Recommended Fix",
        "- Add null checks and unit tests for edge cases; improve error handling.",
        "",
        "# Preventive Actions",
        "- Add alerts for error spikes and correlation-based tracing dashboards.",
        "",
        "---\nTop contexts (sample):\n" + "\n---\n".join(contexts[:5])
    ]
    return "\n".join(md)
