"""Optional persistence layer (Neon Postgres) — v3.5.

Design constraints:
- DATABASE_URL unset → every helper is a cheap no-op and the product stays
  exactly as stateless as before. Nothing may raise toward a user request
  because the database is missing or down: persistence is additive, never
  load-bearing for a response.
- Vercel Python serverless → pg8000 (pure Python, no libpq build) and a
  fresh short-lived connection per operation. Neon's pooled endpoint makes
  per-request connections cheap; holding sockets across invocations is what
  actually leaks.
- Privacy stance survives: we store metadata (counts, savings totals, firm,
  timestamps) — never invoice contents or findings text.

Tables (bootstrapped lazily, CREATE TABLE IF NOT EXISTS):
  leads        — durable copy of /api/leads submissions
  audit_events — per-request metadata for usage history / firm dashboards
  api_keys     — self-serve keys: sha256(key) + firm + tier; complements the
                 TARIFFCHECK_API_KEYS env pairs (env still wins ties)
"""
import hashlib
import json
import logging
import os
import ssl
from urllib.parse import urlparse, unquote

log = logging.getLogger("tariffcheck")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    email TEXT NOT NULL,
    source TEXT,
    firm TEXT,
    entries_per_month TEXT,
    software TEXT,
    context TEXT
);
CREATE TABLE IF NOT EXISTS audit_events (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    endpoint TEXT NOT NULL,
    firm TEXT,
    rows INTEGER,
    findings INTEGER,
    verified_savings NUMERIC,
    meta JSONB
);
CREATE TABLE IF NOT EXISTS api_keys (
    key_hash TEXT PRIMARY KEY,
    firm TEXT NOT NULL,
    tier TEXT NOT NULL DEFAULT 'pilot',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at TIMESTAMPTZ
);
"""

_bootstrapped = False


def db_enabled():
    return bool(os.getenv("DATABASE_URL", "").strip())


def _connect():
    import pg8000.native
    url = urlparse(os.getenv("DATABASE_URL", "").strip())
    kwargs = {
        "user": unquote(url.username or ""),
        "password": unquote(url.password or ""),
        "host": url.hostname,
        "port": url.port or 5432,
        "database": (url.path or "/postgres").lstrip("/") or "postgres",
    }
    # Neon requires TLS; sslmode query params are ignored by pg8000, so pass
    # a default SSL context whenever the URL isn't a local dev database.
    if url.hostname not in ("localhost", "127.0.0.1"):
        kwargs["ssl_context"] = ssl.create_default_context()
    return pg8000.native.Connection(**kwargs)


def _run(statement, **params):
    """One statement on a fresh connection; bootstraps schema on first use.
    Returns rows (list) or None on any failure — never raises upward."""
    global _bootstrapped
    if not db_enabled():
        return None
    try:
        conn = _connect()
        try:
            if not _bootstrapped:
                for stmt in _SCHEMA.split(";"):
                    if stmt.strip():
                        conn.run(stmt)
                _bootstrapped = True
            return conn.run(statement, **params)
        finally:
            conn.close()
    except Exception:
        log.exception("db operation failed (continuing without persistence)")
        return None


def hash_key(key):
    return hashlib.sha256(key.encode()).hexdigest()


def record_lead(payload):
    return _run(
        "INSERT INTO leads (email, source, firm, entries_per_month, software, context) "
        "VALUES (:email, :source, :firm, :epm, :software, :context)",
        email=str(payload.get("email", ""))[:200],
        source=str(payload.get("source", "") or "")[:100],
        firm=str(payload.get("firm", "") or "")[:200],
        epm=str(payload.get("entries_per_month", "") or "")[:50],
        software=str(payload.get("software", "") or "")[:100],
        context=str(payload.get("context", "") or "")[:1000],
    ) is not None


def record_audit(endpoint, firm=None, rows=None, findings=None,
                 verified_savings=None, meta=None):
    return _run(
        "INSERT INTO audit_events (endpoint, firm, rows, findings, verified_savings, meta) "
        "VALUES (:endpoint, :firm, :rows, :findings, :savings, :meta)",
        endpoint=str(endpoint)[:100],
        firm=(str(firm)[:200] if firm else None),
        rows=rows, findings=findings, savings=verified_savings,
        meta=json.dumps(meta or {}),
    ) is not None


def lookup_api_key(supplied):
    """Firm name for a DB-issued key, or None. Keys are stored hashed."""
    rows = _run(
        "SELECT firm FROM api_keys WHERE key_hash = :h AND revoked_at IS NULL",
        h=hash_key(supplied))
    if rows:
        return rows[0][0]
    return None
