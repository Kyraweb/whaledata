"""
API usage logging — attached as @app.middleware in main.py.
Uses background tasks to avoid blocking requests.
"""
import time
import threading


def log_request_bg(ip: str, path: str, method: str, status_code: int, duration: int):
    """Write log entry in background thread."""
    try:
        from app.database import get_connection
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO api_requests (ip, path, method, status_code, response_ms)
            VALUES (%s, %s, %s, %s, %s);
        """, (ip, path, method, status_code, duration))
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass


SKIP_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


def should_log(path: str) -> bool:
    if path.startswith("/admin"):
        return False
    if path in SKIP_PATHS:
        return False
    if path.startswith("/openapi") or path.startswith("/redoc"):
        return False
    return True
