# -*- coding: utf-8 -*-
"""
재고 분석 및 발주 권장 수량 계산
엑셀 시트: Inventory, Suppliers, EmailTemplate 구조 기반
"""
import pandas as pd
from io import BytesIO
from typing import List, Dict, Any, Optional


# sales_Data.csv 형식 → 재고(Inventory) 필드 매핑
# userID = 고객 고유 ID (품목과 무관, 매핑하지 않음)
# Address = 테넌트 주소지 (이메일과 무관, 매핑하지 않음)
SALES_FORMAT_COLUMNS = {"userID", "Gender", "Age", "DAT", "Tenant", "Price", "category_big", "category_mid", "category_small", "Address"}

SALES_TO_INVENTORY = {
    "category_small": "품목코드",  # 품목코드 = 카테고리
    "Tenant": "거래처",
    "Price": "규격",               # 금액 표기용
}

# 재고 형식에 없으면 쓰는 기본값
DEFAULT_INVENTORY_ROW = {
    "규격": "-",
    "단위": "건",
    "현재재고": 0,
    "안전재고": 1,
    "MOQ": 1,
    "알림담당자": "",
    "거래처이메일": "",
    "리드타임(일)": 1,
}


def _is_sales_format(df: pd.DataFrame) -> bool:
    """sales_Data.csv 형태(컬럼명 기준)인지 확인"""
    cols = set(df.columns)
    return SALES_FORMAT_COLUMNS.issubset(cols) or "Tenant" in cols and "Price" in cols and ("category_small" in cols or "category_mid" in cols)


def _sales_df_to_inventory(df: pd.DataFrame) -> pd.DataFrame:
    """sales_Data 형식 DataFrame을 재고(Inventory) 형식으로 변환. 품목코드=카테고리, Address는 사용 안 함."""
    out = pd.DataFrame()
    for sales_col, inv_col in SALES_TO_INVENTORY.items():
        if sales_col in df.columns:
            out[inv_col] = df[sales_col].astype(str)
    if "품목코드" not in out.columns and "category_mid" in df.columns:
        out["품목코드"] = df["category_mid"].astype(str)
    if "품목코드" not in out.columns:
        out["품목코드"] = [f"ID{i}" for i in range(len(df))]
    if "재료명" not in out.columns and "category_small" in df.columns:
        out["재료명"] = df["category_small"].astype(str)
    if "재료명" not in out.columns and "category_mid" in df.columns:
        out["재료명"] = df["category_mid"].astype(str)
    for col, default in DEFAULT_INVENTORY_ROW.items():
        if col not in out.columns:
            out[col] = default
    if "규격" in out.columns and "Price" in df.columns:
        out["규격"] = df["Price"].astype(str).apply(lambda x: f"금액 {x}" if x and x != "nan" else "-")
    return out


def normalize_to_inventory(df: pd.DataFrame) -> pd.DataFrame:
    """CSV가 sales_Data 형식이면 재고 형식으로 변환, 이미 재고 형식이면 그대로 반환"""
    if _is_sales_format(df):
        return _sales_df_to_inventory(df)
    return df


# 발주 수량 공식: MAX(MOQ, 안전재고 - 현재재고)
def compute_order_quantity(current: float, safety: float, moq: int) -> int:
    if current >= safety:
        return 0
    short = safety - current
    return max(moq, int(short))


def analyze_inventory_df(df: pd.DataFrame) -> pd.DataFrame:
    """재고 DataFrame에 부족수량, 발주권장수량, 상태, 담당자알림메시지 계산"""
    required = [
        "품목코드", "재료명", "규격", "단위", "현재재고", "안전재고", "MOQ",
        "거래처", "알림담당자", "거래처이메일", "리드타임(일)"
    ]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"필수 컬럼 없음: {col}")

    out = df.copy()
    out["부족수량"] = (out["안전재고"] - out["현재재고"]).clip(lower=0).astype(int)
    out["발주권장수량"] = out.apply(
        lambda r: compute_order_quantity(
            r["현재재고"], r["안전재고"], int(r["MOQ"])
        ),
        axis=1,
    )
    out["상태"] = out.apply(
        lambda r: "발주 필요" if r["현재재고"] < r["안전재고"] else "정상",
        axis=1,
    )

    def alert_message(row):
        if row["상태"] != "발주 필요":
            return ""
        return (
            f"{row['재료명']} 재고 부족 - "
            f"현재 {int(row['현재재고'])}{row['단위']}, "
            f"안전재고 {int(row['안전재고'])}{row['단위']}, "
            f"권장발주 {int(row['발주권장수량'])}{row['단위']}"
        )

    out["담당자알림메시지"] = out.apply(alert_message, axis=1)
    return out


def load_excel_sheets(path_or_bytes) -> Dict[str, pd.DataFrame]:
    """엑셀 파일에서 Inventory, Suppliers, EmailTemplate 시트 로드"""
    xlsx = pd.ExcelFile(path_or_bytes, engine="openpyxl")
    result = {}
    for name in ["Inventory", "Suppliers", "EmailTemplate"]:
        if name in xlsx.sheet_names:
            result[name] = pd.read_excel(xlsx, sheet_name=name, engine="openpyxl")
    return result


def load_inventory_sheets(path_or_bytes, filename: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """
    CSV 또는 엑셀 파일에서 재고 데이터 로드.
    - 확장자가 .csv 이면 CSV로 읽어 Inventory 시트로 반환.
    - 그 외에는 엑셀 엔진(openpyxl)으로 시트 로드.
    """
    if filename and str(filename).lower().endswith(".csv"):
        if hasattr(path_or_bytes, "read"):
            data = path_or_bytes.read()
        else:
            data = path_or_bytes
        raw = BytesIO(data) if isinstance(data, bytes) else data
        for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
            try:
                df = pd.read_csv(BytesIO(data) if isinstance(data, bytes) else raw, encoding=enc)
                df = normalize_to_inventory(df)
                return {"Inventory": df}
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        df = pd.read_csv(BytesIO(data) if isinstance(data, bytes) else raw, encoding="utf-8", errors="replace")
        df = normalize_to_inventory(df)
        return {"Inventory": df}
    if hasattr(path_or_bytes, "seek"):
        path_or_bytes.seek(0)
    return load_excel_sheets(path_or_bytes)


def get_orders_by_supplier(analyzed: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
    """발주 필요 품목만 거래처별로 묶어서 반환"""
    orders = analyzed[analyzed["상태"] == "발주 필요"].copy()
    by_supplier: Dict[str, List[Dict[str, Any]]] = {}
    for _, row in orders.iterrows():
        supplier = row["거래처"]
        if supplier not in by_supplier:
            by_supplier[supplier] = []
        by_supplier[supplier].append({
            "품목코드": row["품목코드"],
            "재료명": row["재료명"],
            "규격": str(row["규격"]),
            "단위": row["단위"],
            "현재재고": int(row["현재재고"]),
            "안전재고": int(row["안전재고"]),
            "발주권장수량": int(row["발주권장수량"]),
            "거래처이메일": row["거래처이메일"],
        })
    return by_supplier


def build_item_list_text(items: List[Dict[str, Any]]) -> str:
    """이메일 본문용 품목 목록 텍스트"""
    lines = []
    for i, it in enumerate(items, 1):
        lines.append(
            f"{i}. {it['재료명']} ({it['규격']} {it['단위']}) "
            f"- 현재재고: {it['현재재고']}, 권장발주: {it['발주권장수량']}{it['단위']}"
        )
    return "\n".join(lines)


def get_email_templates(templates_df: pd.DataFrame) -> tuple:
    """EmailTemplate 시트에서 제목/본문 템플릿 문자열 추출"""
    subject = ""
    body = ""
    if templates_df is None or templates_df.empty:
        return subject, body
    # 컬럼이 '발주 이메일 템플릿', 'Unnamed: 1' 형태일 수 있음
    cols = list(templates_df.columns)
    val_col = cols[1] if len(cols) > 1 else cols[0]
    for _, row in templates_df.iterrows():
        left = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
        right = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""
        if "제목" in left:
            subject = right
        elif "본문" in left:
            body = right
    return subject, body
