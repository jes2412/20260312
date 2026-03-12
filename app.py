# -*- coding: utf-8 -*-
"""
재고 파악 및 발주 이메일 자동화 웹 시스템
- 사용자 데이터 입력/엑셀 업로드 → 재고 분석 → 발주 필요 시 각 거래처 담당자(엑셀 이메일)로 발주 메일 발송 (발송 계정: yipro53@gmail.com)
"""
import os
import json
import math
from dotenv import load_dotenv
load_dotenv()
from io import BytesIO
from flask import Flask, request, render_template, jsonify
import pandas as pd


def _json_safe(obj):
    """NaN, numpy 타입 등 JSON 직렬화 불가 값을 치환"""
    if obj is None:
        return None
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if hasattr(obj, "item"):  # numpy scalar (int64, float64 등)
        try:
            v = obj.item()
            return None if isinstance(v, float) and math.isnan(v) else v
        except Exception:
            return None
    if isinstance(obj, (pd.Timestamp,)):
        return str(obj)
    return obj

from inventory import (
    load_excel_sheets,
    load_inventory_sheets,
    analyze_inventory_df,
    get_orders_by_supplier,
    get_email_templates,
)
from email_sender import send_orders_to_suppliers, SENDER_EMAIL

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"),
)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB

# 기본 엑셀 경로 (프로젝트 내 학습용 엑셀)
DEFAULT_EXCEL_PATH = os.path.join(os.path.dirname(__file__), "domino_inventory_training.xlsx")


@app.route("/")
def index():
    return render_template("index.html", sender_email=SENDER_EMAIL)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """입력받은 파일(엑셀/CSV) 또는 미선택 시 domino_inventory_training.xlsx 로 재고 분석."""
    try:
        if request.files and "file" in request.files and request.files["file"].filename:
            file = request.files["file"]
            data = file.read()
            filename = file.filename or ""
            sheets = load_inventory_sheets(BytesIO(data), filename=filename)
        else:
            if not os.path.isfile(DEFAULT_EXCEL_PATH):
                return jsonify({"error": "분석할 파일을 선택하거나, domino_inventory_training.xlsx 를 두세요."}), 400
            sheets = load_excel_sheets(DEFAULT_EXCEL_PATH)

        if "Inventory" not in sheets:
            return jsonify({"error": "엑셀에 'Inventory' 시트가 없습니다."}), 400

        analyzed = analyze_inventory_df(sheets["Inventory"])
        orders_by_supplier = get_orders_by_supplier(analyzed)

        # DataFrame → JSON (NaN·numpy 제거해 브라우저 파싱 오류 방지)
        num_cols = ["현재재고", "안전재고", "MOQ", "부족수량", "발주권장수량", "리드타임(일)"]
        analyzed_json = []
        for _, row in analyzed.iterrows():
            r = {}
            for k in row.index:
                v = row[k]
                if pd.isna(v) or v is None or (isinstance(v, float) and math.isnan(v)):
                    r[k] = 0 if k in num_cols else ""
                elif hasattr(v, "item"):
                    r[k] = int(v.item()) if k in num_cols else str(v)
                elif isinstance(v, (pd.Timestamp,)):
                    r[k] = str(v)
                elif k in num_cols:
                    try:
                        r[k] = int(float(v))
                    except (ValueError, TypeError):
                        r[k] = 0
                else:
                    r[k] = str(v) if not isinstance(v, (int, float, str, bool)) else v
            analyzed_json.append(_json_safe(r))

        for row in analyzed_json:
            for key in row:
                if row[key] is None:
                    row[key] = "" if key not in num_cols else 0

        orders_clean = {k: _json_safe(v) for k, v in orders_by_supplier.items()}

        return jsonify({
            "inventory": _json_safe(analyzed_json),
            "orders_by_supplier": orders_clean,
            "summary": {
                "total_items": len(analyzed),
                "order_required_count": int(len(analyzed[analyzed["상태"] == "발주 필요"])),
                "supplier_count": len(orders_by_supplier),
            },
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"분석 중 오류: {e}"}), 500


@app.route("/api/recipients")
def recipients():
    """기본 엑셀 기준 수신 담당자 이메일 목록 (Suppliers + Inventory 거래처이메일)"""
    try:
        if not os.path.isfile(DEFAULT_EXCEL_PATH):
            return jsonify({"suppliers": [], "inventory_emails": []})
        sheets = load_excel_sheets(DEFAULT_EXCEL_PATH)
        suppliers = []
        if "Suppliers" in sheets:
            df = sheets["Suppliers"]
            cols = list(df.columns)
            name_col = next((c for c in cols if "거래처" in str(c) and "명" in str(c)), cols[0] if cols else None)
            person_col = next((c for c in cols if "담당" in str(c)), None)
            email_col = next((c for c in cols if "이메일" in str(c)), None)
            if name_col and email_col:
                for _, row in df.iterrows():
                    suppliers.append({
                        "거래처명": row.get(name_col, ""),
                        "담당자": row.get(person_col, "") if person_col else "",
                        "이메일": row.get(email_col, ""),
                    })
        inv_emails = []
        if "Inventory" in sheets:
            df = sheets["Inventory"]
            email_col = next((c for c in df.columns if "거래처이메일" in str(c)), None)
            if email_col:
                seen = set()
                for _, row in df.iterrows():
                    val = row.get(email_col)
                    if pd.notna(val) and str(val).strip() and str(val).strip() not in seen:
                        if not str(val).startswith("="):
                            seen.add(str(val).strip())
                            inv_emails.append({"이메일": str(val).strip(), "거래처": row.get("거래처", "")})
        return jsonify({"suppliers": suppliers, "inventory_emails": inv_emails})
    except Exception as e:
        return jsonify({"suppliers": [], "inventory_emails": [], "error": str(e)})


@app.route("/api/send-orders", methods=["POST"])
def send_orders():
    """분석 결과 기반으로 발주 이메일 발송 (발송: yipro53@gmail.com → 수신: 엑셀의 각 거래처 담당자 이메일)"""
    try:
        body = request.get_json() or {}
        orders_by_supplier = body.get("orders_by_supplier") or {}
        store_name = body.get("store_name", "도미노피자 점포")

        if not orders_by_supplier:
            return jsonify({"error": "발주할 거래처가 없습니다. 재고를 먼저 분석해 주세요."}), 400

        # 템플릿 기본값 (엑셀 EmailTemplate 시트와 동일)
        subject_tpl = "[발주요청] {{STORE_NAME}} / {{SUPPLIER_NAME}} / {{ORDER_DATE}}"
        body_tpl = (
            "안녕하세요 {{SUPPLIER_NAME}} 담당자님.\n\n"
            "도미노피자 {{STORE_NAME}}입니다.\n"
            "아래 품목에 대해 발주 요청드립니다.\n\n{{ITEM_LIST}}\n\n"
            "첨부한 발주서 확인 부탁드립니다.\n감사합니다.\n{{INTERNAL_OWNER}}"
        )

        # 업로드된 엑셀에서 템플릿 로드한 경우 여기서 덮어쓸 수 있음 (선택)

        results = send_orders_to_suppliers(
            orders_by_supplier, subject_tpl, body_tpl, store_name
        )
        sent_count = sum(1 for r in results if r["sent"])
        return jsonify({
            "message": "발주 메일 발송 요청 완료 (수신: 각 거래처 담당자 이메일)",
            "results": results,
            "sent_count": sent_count,
            "total_count": len(results),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
