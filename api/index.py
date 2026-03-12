# -*- coding: utf-8 -*-
"""
Vercel 서버리스 진입점. rewrites로 모든 경로가 여기로 오므로 PATH 보정 후 Flask에 전달.
"""
import sys
import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
os.chdir(root)

try:
    from app import app as flask_app
except Exception as e:
    flask_app = None
    _import_error = str(e)


def app(environ, start_response):
    """PATH_INFO에서 /api/index[/...] 제거 후 원래 경로로 Flask에 전달"""
    if flask_app is None:
        start_response("500 Internal Server Error", [("Content-Type", "text/plain; charset=utf-8")])
        return [("Import error: " + _import_error).encode("utf-8")]
    try:
        path = (environ.get("PATH_INFO") or "").strip() or "/"
        if path.startswith("/api/index"):
            path = path[len("/api/index"):].lstrip("/")
            path = "/" + path if path else "/"
            environ = dict(environ)
            environ["PATH_INFO"] = path
            environ["SCRIPT_NAME"] = ""
        return flask_app(environ, start_response)
    except Exception as e:
        start_response("500 Internal Server Error", [("Content-Type", "text/plain; charset=utf-8")])
        return [("Error: " + str(e)).encode("utf-8")]
