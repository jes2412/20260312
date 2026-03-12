# -*- coding: utf-8 -*-
"""
Vercel 서버리스 진입점. rewrites로 모든 경로가 여기로 오므로 PATH 보정 후 Flask에 전달.
"""
import sys
import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
os.chdir(root)

from app import app as flask_app


def _parse_query(qs):
    if not qs:
        return {}
    from urllib.parse import unquote_plus
    out = {}
    for p in qs.split("&"):
        if "=" in p:
            k, v = p.split("=", 1)
            out[unquote_plus(k)] = unquote_plus(v)
    return out


def app(environ, start_response):
    """원본 경로 복원: vercel rewrite가 __path 쿼리로 넘기거나 PATH_INFO에 /api/index/xxx 로 넘김."""
    path = (environ.get("PATH_INFO") or "").strip() or "/"
    query = _parse_query(environ.get("QUERY_STRING") or "")
    if path.startswith("/api/index"):
        path = path[len("/api/index"):].lstrip("/")
        path = "/" + path if path else "/"
    if "__path" in query and path == "/":
        raw = query["__path"].strip()
        path = "/" + raw if raw and not raw.startswith("/") else (raw or "/")
    environ = dict(environ)
    environ["PATH_INFO"] = path
    environ["SCRIPT_NAME"] = ""
    return flask_app(environ, start_response)
