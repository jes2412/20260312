# -*- coding: utf-8 -*-
"""
발주 이메일 발송
- 발송(From): yipro53@gmail.com (시스템 발송용 계정)
- 수신(To): 엑셀 내 각 거래처 담당자 이메일(거래처이메일)
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any, Optional
import os


# 시스템이 사용하는 발송 이메일 주소 (From / SMTP 계정)
SENDER_EMAIL = "yipro53@gmail.com"


def render_template(
    subject_tpl: str,
    body_tpl: str,
    store_name: str,
    supplier_name: str,
    item_list_text: str,
    internal_owner: str = "도미노피자 재고관리시스템",
) -> tuple:
    """템플릿 치환 후 제목/본문 반환"""
    order_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    sub = (
        subject_tpl.replace("{{STORE_NAME}}", store_name)
        .replace("{{SUPPLIER_NAME}}", supplier_name)
        .replace("{{ORDER_DATE}}", order_date)
    )
    body = (
        body_tpl.replace("{{STORE_NAME}}", store_name)
        .replace("{{SUPPLIER_NAME}}", supplier_name)
        .replace("{{ORDER_DATE}}", order_date)
        .replace("{{ITEM_LIST}}", item_list_text)
        .replace("{{INTERNAL_OWNER}}", internal_owner)
    )
    return sub, body


def send_order_email(
    subject: str,
    body: str,
    to_email: str,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_user: Optional[str] = None,
    smtp_password: Optional[str] = None,
) -> bool:
    """
    발주 메일을 to_email(엑셀의 거래처 담당자 이메일)로 발송.
    발송 계정(From)은 smtp_user 또는 환경변수, 미설정 시 SENDER_EMAIL 사용.
    SMTP 미설정 시 False 반환.
    """
    host = smtp_host or os.environ.get("SMTP_HOST")
    port = smtp_port or int(os.environ.get("SMTP_PORT", "587"))
    user = smtp_user or os.environ.get("SMTP_USER") or SENDER_EMAIL
    password = smtp_password or os.environ.get("SMTP_PASSWORD")

    if not all([host, user, password]):
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(user, to_email, msg.as_string())
        return True
    except Exception:
        return False


def send_orders_to_suppliers(
    orders_by_supplier: Dict[str, List[Dict[str, Any]]],
    subject_tpl: str,
    body_tpl: str,
    store_name: str = "도미노피자 점포",
) -> List[Dict[str, Any]]:
    """
    거래처별 발주 내역을 해당 거래처 담당자 이메일(엑셀의 거래처이메일)로 발송.
    발송 주소(From): yipro53@gmail.com (또는 SMTP_USER).
    거래처당 한 통씩 발송.
    반환: [ {"supplier": 이름, "to_email": 수신이메일, "sent": True/False, "error": 메시지 또는 None }, ... ]
    """
    from inventory import build_item_list_text

    results = []
    for supplier_name, items in orders_by_supplier.items():
        if not items:
            continue
        to_email = items[0].get("거래처이메일", "").strip()
        if not to_email:
            results.append({
                "supplier": supplier_name,
                "to_email": None,
                "sent": False,
                "error": "거래처이메일 없음",
            })
            continue
        item_list_text = build_item_list_text(items)
        subject, body = render_template(
            subject_tpl, body_tpl, store_name, supplier_name, item_list_text
        )
        sent = send_order_email(subject, body, to_email=to_email)
        results.append({
            "supplier": supplier_name,
            "to_email": to_email,
            "sent": sent,
            "error": None if sent else "SMTP 설정 필요 또는 발송 실패",
        })
    return results
