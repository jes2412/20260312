# Vercel 배포 보안 설정

## 1. vercel.json 보안 헤더 (적용됨)

- **X-Content-Type-Options: nosniff** – MIME 타입 스니핑 방지  
- **X-Frame-Options: DENY** – 다른 사이트에 iframe 삽입 방지  
- **X-XSS-Protection: 1; mode=block** – XSS 필터 활성화  
- **Referrer-Policy** – 외부 전달 시 referrer 제한  
- **Permissions-Policy** – 위치/마이크/카메라 등 권한 비허용  

## 2. Vercel 대시보드에서 설정할 것

### 환경 변수 (비밀 정보)

- [Vercel 프로젝트] → **Settings** → **Environment Variables**
- 다음 값은 **반드시 환경 변수로만** 넣고, 코드/저장소에는 넣지 마세요.
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` (메일 발송)
  - `DEPLOYMENT_PASSWORD` (아래 “앱 비밀번호” 사용 시)

### DEPLOYMENT_PASSWORD 설정 방법 (단계별)

사이트 접속 시 비밀번호를 물어보게 하려면 Vercel에 **DEPLOYMENT_PASSWORD** 환경 변수를 넣으면 됩니다.

#### 1단계: Vercel 로그인 및 프로젝트 열기

1. 브라우저에서 **https://vercel.com** 접속
2. 로그인 후 상단 **Dashboard** 클릭
3. 배포한 프로젝트(예: 20260312) **이름 클릭** → 프로젝트 페이지로 이동

#### 2단계: Settings → Environment Variables 이동

4. 상단 메뉴에서 **Settings** 탭 클릭
5. 왼쪽 사이드바에서 **Environment Variables** 클릭  
   (또는 스크롤해서 "Environment Variables" 섹션 찾기)

#### 3단계: 변수 추가

6. **Name (키)** 입력란에 아래를 **그대로** 입력:
   ```
   DEPLOYMENT_PASSWORD
   ```
7. **Value (값)** 입력란에 **사용할 비밀번호** 입력 (예: `MySecurePass123`)
8. **Environment**에서 적용할 환경 선택:
   - **Production**만 체크 → 실제 배포 주소(예: xxx.vercel.app)에만 적용
   - **Preview**만 체크 → PR/브랜치 미리보기에만 적용
   - **Development**만 체크 → 로컬 `vercel dev` 에만 적용  
   → 보통 **Production** (또는 Production + Preview) 체크
9. **Save** 버튼 클릭

#### 4단계: 재배포 (필수)

환경 변수는 **새로 배포할 때만** 반영됩니다.

10. 상단 **Deployments** 탭 클릭
11. 맨 위(최신) 배포 오른쪽 **⋮(점 세 개)** 클릭 → **Redeploy** 선택
12. **Redeploy** 버튼 한 번 더 클릭

몇 분 후 배포가 끝나면, 사이트 주소로 접속할 때 **브라우저 로그인 창**이 뜹니다.

#### 접속할 때

- **사용자 이름**: 아무 값이나 입력해도 됩니다 (예: `admin`, `user`)
- **비밀번호**: 7단계에서 넣은 **DEPLOYMENT_PASSWORD** 값 그대로 입력

비밀번호를 쓰지 않으려면 Vercel에서 **DEPLOYMENT_PASSWORD** 변수를 삭제한 뒤 다시 Redeploy 하면 됩니다.

### Vercel Deployment Protection (선택)

- [프로젝트] → **Settings** → **Deployment Protection**
- **Vercel Authentication**: 팀/조직 멤버만 배포 또는 Preview 접근 가능하도록 제한
- **Password Protection**: Preview 배포에 비밀번호 설정 (Vercel 쪽에서 제공하는 기능)
- **Trusted IPs**: 특정 IP만 접근 허용 (Enterprise 등)

## 3. 정리

| 항목              | 설정 위치                    | 비고                    |
|-------------------|-----------------------------|-------------------------|
| 보안 헤더         | `vercel.json` (headers)     | 이미 적용됨             |
| SMTP / 메일 비밀번호 | Environment Variables      | 코드에 넣지 말 것       |
| 앱 접근 비밀번호  | `DEPLOYMENT_PASSWORD` 환경 변수 | 설정 시 Basic 인증 사용 |
| 배포/팀 접근 제한 | Deployment Protection       | Vercel 유료 기능 활용   |
