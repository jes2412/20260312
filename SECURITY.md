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

### 배포 비밀번호 (앱 접근 제한)

- 환경 변수 **DEPLOYMENT_PASSWORD** 에 값을 넣으면, 사이트 접속 시 **Basic 인증** 비밀번호로 동작합니다.
- 브라우저에서 ID/비밀번호 창이 뜨면, 비밀번호에 **DEPLOYMENT_PASSWORD** 값을 입력하면 됩니다. (사용자명은 아무 값이나 가능)
- 비워 두면 비밀번호 없이 접속됩니다.

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
