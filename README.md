# Yes-Show API 백엔드

프론트엔드와 연동되는 백엔드 API 서버입니다.

## 🚀 실행 방법

### 1. 환경 설정
```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 데이터베이스 설정
```bash
# .env 파일 생성해서 DB 정보 입력
DATABASE_URL=postgresql://username:password@localhost:5432/yes_show <- 정확한 URL은 혹시 테스트하실분 있으시면 개인톡으로 알려드립니다
```

### 3. 서버 실행
```bash
uvicorn main:app --reload --port 8080
```

### 4. 확인
- **API 문서**: http://localhost:8000/docs
- **서버 상태**: http://localhost:8080/health

## 🧪 테스트 방법

### 기본 테스트
```bash
# 서버 상태 확인
curl http://localhost:8080/health

# 환자 검색 테스트
curl "http://localhost:8080/patient/search?query=홍길동"

# 오늘 예약 현황
curl http://localhost:8080/dashboard/appointments/today
```

### 주요 API 엔드포인트

| 기능 | 메소드 + URL | 설명 |
|------|-------------|------|
| 환자 검색 | `GET /patient/search?query=이름` | 환자 이름으로 검색 |
| 환자별 예약 | `GET /appointment/patient/{환자ID}` | 특정 환자 예약 목록 |
| 오늘 예약 | `GET /dashboard/appointments/today` | 오늘 예약 현황 |
| 리마인더 발송 | `POST /reminder/send` | SMS/이메일 리마인더 |
| 음성 업로드 | `POST /recording/upload` | 음성파일 → 텍스트 변환 |

### 데이터 추가 테스트
```bash
# 새 예약 생성
curl -X POST http://localhost:8080/appointment \
  -H "Content-Type: application/json" \
  -d '{"patientId": 1, "memo": "테스트", "appointmentDate": "2024-12-07"}'
```

## 📝 참고사항

- **포트**: 8080
- **CORS**: 이미 설정됨 (프론트엔드 연동 가능)
- **에러**: 빨간 에러 나면 콘솔 로그 확인

## 🔧 문제 해결

**DB 연결 에러**: `.env` 파일에 올바른 PostgreSQL 정보 입력  
**포트 충돌**: `--port 8081` 등으로 다른 포트 사용  
**패키지 에러**: `pip install -r requirements.txt` 다시 실행
