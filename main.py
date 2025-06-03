from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, date, time
from typing import List, Optional
from pydantic import BaseModel, Field
import json

from database import engine, get_db, Base
from models import PatientType, AppointmentType, ReminderHistType
from schemas import (
    PatientTypeCreate, PatientTypeUpdate, PatientTypeOut,
    AppointmentTypeCreate, AppointmentTypeUpdate, AppointmentTypeOut,
    AppointmentWithPatientInfo, AppointmentListResponse,
    ReminderHistTypeCreate, ReminderHistTypeOut,
    AudioUploadResponse, ReminderSendResponse,
    AppointmentFilterParams, NoShowUpdate
)

# DB 테이블 자동 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Yes-Show API", version="1.0.0")

# CORS 설정 (프론트엔드 연결용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# 1. 환자(Patient) API - 프론트엔드 요구사항 맞춤
# =============================================================================

@app.get("/patient/name/{name}", response_model=PatientTypeOut, tags=["patient"])
def get_patient_by_name(name: str, db: Session = Depends(get_db)):
    """환자 이름으로 환자 정보 조회"""
    patient = db.query(PatientType).filter(PatientType.name == name).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@app.get("/patient/search", response_model=List[PatientTypeOut], tags=["patient"])
def search_patients(query: str = Query(...), db: Session = Depends(get_db)):
    """환자 검색 (이름, 전화번호 등으로)"""
    patients = db.query(PatientType).filter(
        or_(
            PatientType.name.contains(query),
            PatientType.phone.contains(query),
            PatientType.email.contains(query)
        )
    ).all()

    if not patients:
        raise HTTPException(status_code=404, detail="No patients found")
    return patients


# =============================================================================
# 2. 예약(Appointment) API - 프론트엔드 요구사항 맞춤
# =============================================================================

@app.get("/appointment/patient/{patient_id}", response_model=List[AppointmentTypeOut], tags=["appointment"])
def get_appointments_by_patient(patient_id: int, db: Session = Depends(get_db)):
    """특정 환자의 모든 예약 내역 조회"""
    # 환자 존재 확인
    patient = db.query(PatientType).filter(PatientType.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    appointments = db.query(AppointmentType).filter(
        AppointmentType.patient_id == patient_id
    ).order_by(desc(AppointmentType.appointment_date)).all()

    return appointments


@app.post("/appointment", response_model=AppointmentTypeOut, tags=["appointment"])
def create_appointment(appointment: AppointmentTypeCreate, db: Session = Depends(get_db)):
    """새로운 예약 생성"""
    # 환자 존재 확인
    patient = db.query(PatientType).filter(PatientType.patient_id == appointment.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    db_appointment = AppointmentType(**appointment.dict())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


@app.get("/appointment/{appointment_id}/script", response_model=str, tags=["appointment"])
def get_appointment_script(appointment_id: int, db: Session = Depends(get_db)):
    """특정 예약의 스크립트(대화록) 조회 - 문자열로 직접 반환"""
    appointment = db.query(AppointmentType).filter(AppointmentType.appointment_id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return appointment.script or ""


@app.get("/appointment/{appointment_id}/summary", response_model=str, tags=["appointment"])
def get_appointment_summary(appointment_id: int, db: Session = Depends(get_db)):
    """특정 예약의 요약 정보 조회 - 문자열로 직접 반환"""
    appointment = db.query(AppointmentType).filter(AppointmentType.appointment_id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return appointment.summary or ""


# =============================================================================
# 3. 리마인더 API (간호사용) - 프론트엔드 요구사항 맞춤
# =============================================================================

@app.get("/reminder/patient/{patient_id}", response_model=List[ReminderHistTypeOut], tags=["reminder"])
def get_patient_reminders(patient_id: int, db: Session = Depends(get_db)):
    """특정 환자의 리마인더 히스토리 조회"""
    # 환자 존재 확인
    patient = db.query(PatientType).filter(PatientType.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    reminders = db.query(ReminderHistType).filter(
        ReminderHistType.patient_id == patient_id
    ).order_by(desc(ReminderHistType.created_at)).all()

    return reminders


class ReminderSendRequest(BaseModel):
    patient_id: int = Field(alias="patientId")
    appointment_id: int = Field(alias="appointmentId")
    message_type: str = Field(alias="messageType")


@app.post("/reminder/send", response_model=dict, tags=["reminder"])
def send_reminder(request: ReminderSendRequest, db: Session = Depends(get_db)):
    """리마인더 발송"""
    # 예약 존재 확인
    appointment = db.query(AppointmentType).filter(AppointmentType.appointment_id == request.appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # 환자 존재 확인
    patient = db.query(PatientType).filter(PatientType.patient_id == request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # 실제 리마인더 발송 로직은 여기에 구현
    # (SMS, 이메일, 전화 등)

    # 리마인더 기록 저장
    db_reminder = ReminderHistType(
        patient_id=request.patient_id,
        appointment_id=request.appointment_id,
        message_type=request.message_type,
        received_at=datetime.utcnow()  # 발송 즉시 수신으로 처리
    )
    db.add(db_reminder)
    db.commit()

    return {"success": True, "message": "Reminder sent successfully"}


# =============================================================================
# 4. 음성 녹음 API - 프론트엔드 요구사항 맞춤
# =============================================================================

class RecordingUploadResponse(BaseModel):
    transcription: str
    summary: str
    success: bool


@app.post("/recording/upload", response_model=RecordingUploadResponse, tags=["recording"])
async def upload_recording(
        audioFile: UploadFile = File(...),
        appointmentId: int = Form(...)
):
    """음성 파일 업로드 및 AI 텍스트 변환"""

    # 파일 검증
    if not audioFile.content_type or not audioFile.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="Audio file required")

    try:
        # 파일 내용 읽기
        audio_content = await audioFile.read()

        # 여기서 실제 음성-텍스트 변환 API 호출
        # (예: OpenAI Whisper, Google Speech-to-Text 등)

        # 임시 응답 (실제 구현시 교체 필요)
        transcription = "음성이 성공적으로 업로드되었습니다. 실제 STT 변환 기능 구현이 필요합니다."
        summary = '{"주요 증상": "음성 파일 업로드 완료", "진단": "STT 구현 필요", "처방": "실제 AI 분석 구현 필요"}'

        return RecordingUploadResponse(
            transcription=transcription,
            summary=summary,
            success=True
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing error: {str(e)}")


# =============================================================================
# 5. 대시보드 API (간호사용) - 프론트엔드 요구사항 맞춤
# =============================================================================

class TodayAppointmentResponse(BaseModel):
    appointment_id: int = Field(alias="appointmentId")
    patient_id: int = Field(alias="patientId")
    patient_name: str = Field(alias="patientName")
    appointment_time: Optional[str] = Field(None, alias="appointmentTime")
    appointment_date: str = Field(alias="appointmentDate")
    no_show: bool = Field(alias="noShow")
    reminder_count: int = Field(alias="reminderCount")
    last_reminder_received: bool = Field(alias="lastReminderReceived")


@app.get("/dashboard/appointments/today", response_model=List[TodayAppointmentResponse], tags=["dashboard"])
def get_today_appointments(db: Session = Depends(get_db)):
    """오늘의 예약 현황"""
    today = date.today()

    # 예약과 환자 정보를 조인하여 가져오기
    appointments_with_patients = db.query(
        AppointmentType, PatientType.name
    ).join(
        PatientType, AppointmentType.patient_id == PatientType.patient_id
    ).filter(
        AppointmentType.appointment_date == today
    ).all()

    result = []
    for appointment, patient_name in appointments_with_patients:
        # 리마인더 개수 계산
        reminder_count = db.query(ReminderHistType).filter(
            ReminderHistType.appointment_id == appointment.appointment_id
        ).count()

        # 최근 리마인더 수신 여부 확인
        last_reminder = db.query(ReminderHistType).filter(
            ReminderHistType.appointment_id == appointment.appointment_id
        ).order_by(desc(ReminderHistType.created_at)).first()

        appointment_time = appointment.appointment_time.strftime("%H:%M") if appointment.appointment_time else None

        appointment_data = TodayAppointmentResponse(
            appointmentId=appointment.appointment_id,
            patientId=appointment.patient_id,
            patientName=patient_name,
            appointmentTime=appointment_time,
            appointmentDate=appointment.appointment_date.strftime("%Y-%m-%d"),
            noShow=appointment.no_show,
            reminderCount=reminder_count,
            lastReminderReceived=last_reminder is not None and last_reminder.received_at is not None
        )
        result.append(appointment_data)

    return result


class NoShowRiskResponse(BaseModel):
    risk_percentage: float = Field(alias="riskPercentage")
    risk_level: str = Field(alias="riskLevel")


@app.get("/dashboard/no-show-risk/{patient_id}", response_model=NoShowRiskResponse, tags=["dashboard"])
def get_no_show_risk(patient_id: int, db: Session = Depends(get_db)):
    """환자별 노쇼 위험도 계산"""
    # 환자 존재 확인
    patient = db.query(PatientType).filter(PatientType.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # 해당 환자의 전체 예약 수와 노쇼 수 계산
    total_appointments = db.query(AppointmentType).filter(
        AppointmentType.patient_id == patient_id
    ).count()

    no_show_count = db.query(AppointmentType).filter(
        and_(
            AppointmentType.patient_id == patient_id,
            AppointmentType.no_show == True
        )
    ).count()

    # 위험도 계산
    if total_appointments == 0:
        risk_percentage = 0.0
        risk_level = "unknown"
    else:
        risk_percentage = (no_show_count / total_appointments) * 100

        if risk_percentage < 20:
            risk_level = "low"
        elif risk_percentage < 50:
            risk_level = "medium"
        else:
            risk_level = "high"

    return NoShowRiskResponse(
        riskPercentage=round(risk_percentage, 1),
        riskLevel=risk_level
    )


# =============================================================================
# 기존 API들 (추가로 필요한 경우)
# =============================================================================

@app.put("/appointment/{appointment_id}/no-show", response_model=AppointmentTypeOut, tags=["appointment"])
def update_no_show_status(
        appointment_id: int,
        no_show_update: NoShowUpdate,
        db: Session = Depends(get_db)
):
    """노쇼 상태 업데이트"""
    appointment = db.query(AppointmentType).filter(AppointmentType.appointment_id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.no_show = no_show_update.no_show
    db.commit()
    db.refresh(appointment)
    return appointment


# =============================================================================
# 헬스체크 및 기본 정보
# =============================================================================

@app.get("/", tags=["default"])
def root():
    """API 상태 확인"""
    return {
        "message": "Yes-Show API가 정상적으로 작동중입니다.",
        "version": "1.0.0",
        "timestamp": datetime.utcnow(),
        "base_url": "http://localhost:8080"
    }


@app.get("/health", tags=["default"])
def health_check():
    """헬스체크"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}
