# Yes-Show API AI 서비스 테스트

### 1. AI 서비스 상태 확인
GET http://localhost:8080/ai/status
Accept: application/json

### 2. 기본 헬스체크 (AI 서비스 URL 포함)
GET http://localhost:8080/
Accept: application/json

### 3. 새로운 appointment 생성 (먼저 이것부터)
POST http://localhost:8080/appointment
Content-Type: application/json

{
    "patientId": 1,
    "appointmentDate": "2024-12-07",
    "appointmentTime": "14:30:00",
    "memo": "AI 테스트용 예약"
}

### 4. 음성 파일 업로드 및 AI 처리 (핵심 기능)
POST http://localhost:8080/recording/upload-with-ai
Content-Type: multipart/form-data; boundary=boundary

--boundary
Content-Disposition: form-data; name="appointment_id"

1
--boundary
Content-Disposition: form-data; name="audio_file"; filename="test.wav"
Content-Type: audio/wav

[여기에 실제 WAV 파일 데이터]
--boundary--

### 5. 생성된 script 조회
GET http://localhost:8080/appointment/1/script
Accept: text/plain

### 6. 생성된 summary 조회
GET http://localhost:8080/appointment/1/summary
Accept: text/plain

### 7. Memo 업데이트
POST http://localhost:8080/appointment/1/memo
Content-Type: application/json

{
    "memo": "AI로 처리된 진료 기록입니다."
}

### 8. 환자 상세 정보 조회 (통계 포함)
GET http://localhost:8080/patient/1/detailed
Accept: application/json

### 9. 환자 이름으로 검색 (기존 기능)
GET http://localhost:8080/patient/name/홍길동
Accept: application/json

### 10. 오늘 예약 현황
GET http://localhost:8080/dashboard/appointments/today
Accept: application/json

### cURL 명령어 예시들:

# AI 서비스 상태 확인
# curl http://localhost:8080/ai/status

# 음성 파일 업로드 (실제 파일 사용)
# curl -X POST http://localhost:8080/recording/upload-with-ai \
#   -F "appointment_id=1" \
#   -F "audio_file=@test.wav"

# Script 조회
# curl http://localhost:8080/appointment/1/script

# Summary 조회
# curl http://localhost:8080/appointment/1/summary

# Memo 업데이트
# curl -X POST http://localhost:8080/appointment/1/memo \
#   -H "Content-Type: application/json" \
#   -d '{"memo": "테스트 메모"}'

# 환자 상세 정보
# curl http://localhost:8080/patient/1/detailed