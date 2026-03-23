"""
API usage logging middleware.
Logs every request to api_requests table.
Admin panel shows usage stats and flags high-volume IPs.
"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.database import get_connection

THRESHOLD_PER_HOUR = 500  # flag IPs exceeding this


class APIUsageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip admin and health routes
        path = request.url.path
        if path.startswith("/admin") or path == "/health" or path.startswith("/docs") or path.startswith("/openapi"):
            return await call_next(request)

        start   = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000)  # ms

        ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown").split(",")[0].strip()

        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("""
                INSERT INTO api_requests (ip, path, method, status_code, response_ms)
                VALUES (%s, %s, %s, %s, %s);
            """, (ip, path, request.method, response.status_code, duration))
            conn.commit()
            cur.close()
            conn.close()
        except Exception:
            pass  # never block a request due to logging failure

        return response
