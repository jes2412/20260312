# 도미노 재고·발주 자동화 시스템

재고를 파악하고, 부족 시 **엑셀에 있는 각 거래처 담당자 이메일**로 발주 메일을 보내는 웹 시스템입니다. 발송 계정은 **yipro53@gmail.com** 을 사용합니다.

## 기능

- **분석 파일 입력**: 재고 분석에 쓸 파일을 **업로드**합니다. 엑셀(.xlsx/.xls) 또는 CSV 선택 가능. 파일을 넣지 않으면 **domino_inventory_training.xlsx** 를 사용합니다.
- **재고 분석**: 입력된 파일(또는 기본 엑셀)의 Inventory 형식 데이터로 현재재고·안전재고·MOQ 기반 발주권장수량 계산 (공식: `MAX(MOQ, 안전재고 - 현재재고)`)
- **발주 메일 발송**: 재고 부족 시 **domino_inventory_training 엑셀의 담당자(거래처이메일)**에게 발주 메일 발송 (발송 계정: **yipro53@gmail.com**)

## 엑셀 / CSV 구조 (참고)

- **엑셀**  
  - **Inventory** 시트 필수 컬럼: 품목코드, 재료명, 규격, 단위, 현재재고, 안전재고, MOQ, 거래처, 알림담당자, 거래처이메일, 리드타임(일)  
  - **Suppliers**, **EmailTemplate** 시트는 선택

- **분석 파일**: 엑셀 또는 CSV를 업로드하면 해당 파일로 분석합니다. 업로드하지 않으면 domino_inventory_training.xlsx 로 분석합니다.  
- (참고) **CSV (sales_Data 형식)** 이면 품목코드/재료명/거래처 등 필드 매핑 후 분석합니다.  
  - **필드 매핑**:  
    | CSV 필드 (sales_Data) | 재고 필드   |
    |------------------------|------------|
    | category_small         | 품목코드 (카테고리) |
    | category_small / category_mid | 재료명     |
    | Tenant                 | 거래처     |
    | Price                  | 규격(금액) |
  - **userID**는 고객 고유 ID이며, 품목과 무관하여 매핑하지 않습니다.  
  - **Address**는 테넌트 주소지이며, 이메일과 무관하게 매핑하지 않습니다.  
  - 재고에 없는 항목(단위, 현재재고, 안전재고, MOQ, 거래처이메일 등)은 기본값으로 채워집니다.  
  - 발주 메일을 보내려면 CSV에 **거래처이메일** 컬럼을 추가하거나, 엑셀에서 담당자 이메일을 관리하면 됩니다.

## 실행 방법

```bash
cd c:\Projects\ch2
pip install -r requirements.txt
python app.py
```

브라우저에서 **http://localhost:5000** 접속 후:

1. (선택) 분석할 **파일 선택** (엑셀/CSV). 비우면 domino_inventory_training.xlsx 사용
2. **재고 분석 실행** 클릭
3. **발주 메일 발송** 버튼으로 엑셀 담당자에게 발주 메일 발송 (발주 필요 건수가 있을 때 활성화)
4. 결과 테이블에서 발주 필요 품목 확인

## 이메일 발송 설정 (Gmail은 별도 인증 필요)

**그냥 하면 안 됩니다.** Gmail은 보안상 일반 비밀번호로 SMTP 발송을 막고 있어서, 아래 인증 과정을 한 번 거쳐야 합니다.

### Gmail 사용 시 필수 단계

1. **2단계 인증 켜기**
   - Google 계정 → [보안] → [2단계 인증] 켜기  
   - (이미 켜져 있으면 생략)

2. **앱 비밀번호 만들기**
   - Google 계정 → [보안] → [2단계 인증] → 맨 아래 **앱 비밀번호**
   - 기기 선택: "기타(맞춤 이름)" → 예: "재고발주시스템" 입력
   - 생성된 **16자리 비밀번호**를 복사 (공백 없이 사용해도 됨)

3. **`.env` 파일에 넣기**
   - 프로젝트 폴더에 `.env` 파일 생성 (또는 `.env.example` 복사)
   - 다음처럼 설정:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=yipro53@gmail.com
   SMTP_PASSWORD=여기에_앱비밀번호_16자리
   ```

- **일반 로그인 비밀번호**는 `SMTP_PASSWORD`에 넣으면 안 됩니다. 반드시 **앱 비밀번호**를 사용해야 합니다.
- 수신 주소는 엑셀의 **거래처이메일** 컬럼 값으로 자동 발송됩니다.

설정을 하지 않으면 "발송 요청"만 되고 실제 메일은 나가지 않으며, 화면에는 발송 실패로 표시됩니다.

## 프로젝트 구조

```
ch2/
├── app.py              # Flask 앱 (API + 라우트)
├── inventory.py        # 재고 분석·발주 수량 계산
├── email_sender.py     # 이메일 발송 (발송: yipro53@gmail.com → 수신: 엑셀 거래처 담당자)
├── templates/
│   └── index.html      # 웹 UI
├── domino_inventory_training.xlsx
├── requirements.txt
├── .env.example
└── README.md
```
