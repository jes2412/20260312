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


def app(environ, start_response):
    """PATH_INFO가 /api/index 로 들어오면 / 등으로 보정해 Flask가 첫 페이지를 찾도록 함"""
    path = (environ.get("PATH_INFO") or "").strip() or "/"
    if path.startswith("/api/index"):
        path = path[len("/api/index"):].strip() or "/"
        environ = dict(environ)
        environ["PATH_INFO"] = path
        environ["SCRIPT_NAME"] = ""
    return flask_app(environ, start_response)
