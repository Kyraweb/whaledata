"""
API usage logging middleware.
Logs every request to api_requests table.
Uses fire-and-forget pattern to never block or affect requests.
"""
import time
import threading
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


def log_request(ip: str, path: str, method: str, status_code: int, duration: int):
    """Log request in a background thread — never blocks the response."""
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
        pass  # never raise — logging must never affect app behaviour


class APIUsageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Always call next first — logging is secondary
        try:
            path = request.url.path

            # Skip internal/non-public routes
            if (path.startswith("/admin") or
                path == "/health" or
                path.startswith("/docs") or
                path.startswith("/openapi") or
                path.startswith("/redoc")):
                return await call_next(request)

            start    = time.time()
            response = await call_next(request)
            duration = round((time.time() - start) * 1000)

            ip = (request.headers.get("x-forwarded-for", "") or
                  (request.client.host if request.client else "unknown")).split(",")[0].strip()

            # Fire and forget — don't await, don't block
            t = threading.Thread(
                target=log_request,
                args=(ip, path, request.method, response.status_code, duration),
                daemon=True
            )
            t.start()

            return response

        except Exception:
            # If anything in middleware fails, just pass through
            return await call_next(request)
