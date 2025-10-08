# Log RCA Assistant (Flask + RAG)

A Flask web app that:
- Scans a Spring Boot Java codebase to extract log statements and surrounding code context.
- Builds a vector index (Chroma) of log/code snippets using local Sentence-Transformers or OpenAI embeddings.
- Fetches logs for a given correlation ID from your Spring Boot database.
- Runs a RAG pipeline to produce an RCA using an LLM (OpenAI if available, fallback heuristic otherwise).

## Quickstart

1. Create and activate a virtual environment, then install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment:

- Copy `.env.example` to `.env` and set values.
- Ensure `DB_URL` points to your Spring Boot log database.
- Set `JAVA_CODE_PATH` to your Spring Boot source root.
- Optionally set `OPENAI_API_KEY` to enable LLM + OpenAI embeddings.

3. Build the vector index from the Java codebase:

```bash
python run.py  # starts the server
# In the UI, click "Build Index"; or curl -X POST http://localhost:5000/ingest
```

4. Analyze by correlation ID:

- Open http://localhost:5000
- Enter a correlation ID and click Analyze.

## Structure

- `app/__init__.py`: Flask app factory.
- `app/config.py`: Config via environment.
- `app/routes.py`: HTTP routes.
- `app/services/db_ingest.py`: Fetch logs from DB.
- `app/services/code_scan.py`: Parse Java and index log contexts.
- `app/services/embeddings.py`: Embedding provider (OpenAI/local).
- `app/services/vector_store.py`: Chroma vector store helpers.
- `app/services/llm.py`: LLM call + fallback.
- `app/services/rca.py`: RCA pipeline orchestration.
- `templates/index.html`: UI.
- `run.py`: Dev entrypoint.

## Notes

- DB schema is configurable via env. Defaults assume a `logs` table with columns: `timestamp, level, logger, message, correlation_id`.
- Code scanning uses a regex for logger calls like `logger.info("...")`. Adjust `LOG_REGEX` if your pattern differs.
- Chroma is persisted at `./data/chroma`. Delete it to rebuild fresh.
- For production, run via Gunicorn/Uvicorn behind a reverse proxy.

## Troubleshooting

- No logs returned: verify `DB_URL`, table/column envs, and that the correlation ID exists.
- Empty context: ensure `JAVA_CODE_PATH` points to your code and run Build Index.
- LLM errors: ensure `OPENAI_API_KEY` and `LLM_MODEL` are valid, otherwise the app will fallback to a heuristic summary.
