"""Vercel entry point. Reuses the existing application without starting a server."""
import sys
from pathlib import Path
from urllib.parse import urlsplit, parse_qsl, urlencode
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from server import ShopNowRequestHandler
from database import get_db_connection

class handler(ShopNowRequestHandler):
    def _restore_route(self):
        parts = urlsplit(self.path)
        pairs = parse_qsl(parts.query, keep_blank_values=True)
        route = next((v for k, v in pairs if k == "__route"), None)
        if route is not None:
            self.path = "/api/" + route.lstrip("/")
            query = urlencode([(k, v) for k, v in pairs if k != "__route"])
            if query:
                self.path += "?" + query

    def do_GET(self):
        self._restore_route()
        path = urlsplit(self.path).path
        if path == "/api/health":
            self._send_json({"success": True, "service": "shopnow-api"})
            return
        if path == "/api/ready":
            conn = get_db_connection()
            ready = False
            if conn:
                try:
                    cursor = conn.cursor()
                    for table in ("users", "admins", "sessions", "account_tokens", "login_attempts",
                                  "wishlist", "reviews", "order_status_history", "products", "categories",
                                  "cart", "orders", "order_items"):
                        cursor.execute(f"SELECT 1 FROM {table} LIMIT 1")
                        cursor.fetchall()
                    cursor.close()
                    ready = True
                except Exception:
                    pass
                finally:
                    conn.close()
            self._send_json({"success": ready, "message": "Database ready" if ready else
                             "Database unavailable or schema not installed"}, 200 if ready else 503)
            return
        if not path.startswith("/api/"):
            self._send_json({"success": False, "message": "Not found"}, 404)
            return
        super().do_GET()

    def do_POST(self):
        self._restore_route()
        super().do_POST()
