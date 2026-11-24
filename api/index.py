import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

class VercelPathMiddleware:
    """Middleware to normalize request paths when Vercel rewrites to /api/index.py."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = environ.get("HTTP_X_MATCHED_PATH")
        if matched_path and not matched_path.startswith("/api/index"):
            environ["PATH_INFO"] = matched_path
        else:
            path = environ.get("PATH_INFO", "")
            for prefix in ["/api/index.py", "/api/index"]:
                if path.startswith(prefix):
                    remainder = path[len(prefix):]
                    environ["PATH_INFO"] = remainder if remainder.startswith("/") else ("/" + remainder if remainder else "/")
                    break
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
handler = app
