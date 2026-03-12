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
) -> tuple[bool, Optional[str]]:
    """
    발주 메일을 to_email(엑셀의 거래처 담당자 이메일)로 발송.
    반환: (성공 여부, 실패 시 오류 메시지)
    """
    host = smtp_host or os.environ.get("SMTP_HOST")
    port = smtp_port or int(os.environ.get("SMTP_PORT", "587"))
    user = smtp_user or os.environ.get("SMTP_USER") or SENDER_EMAIL
    password = smtp_password or os.environ.get("SMTP_PASSWORD")

    if not host or not user or not password:
        return False, "SMTP 설정 없음: Vercel/로컬에서 SMTP_HOST, SMTP_USER, SMTP_PASSWORD 환경변수를 설정하세요. Gmail은 앱 비밀번호 필요."

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(user, to_email, msg.as_string())
        return True, None
    except smtplib.SMTPAuthenticationError as e:
        return False, f"SMTP 로그인 실패(계정/앱 비밀번호 확인): {e}"
    except smtplib.SMTPException as e:
        return False, f"SMTP 오류: {e}"
    except OSError as e:
        return False, f"연결 오류(방화벽/타임아웃): {e}"
    except Exception as e:
        return False, str(e)


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
        sent, err_msg = send_order_email(subject, body, to_email=to_email)
        results.append({
            "supplier": supplier_name,
            "to_email": to_email,
            "sent": sent,
            "error": None if sent else (err_msg or "발송 실패"),
        })
    return results
