from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field
import json
import httpx
import asyncio
import os

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
    allow_origins=["http://localhost:3000"],  # 개발용 Origin 목록
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI 서비스 URL 설정 (환경변수에서 가져오거나 기본값 사용)
WHISPER_API_URL = os.getenv("WHISPER_API_URL", "https://simple-cow-specially.ngrok-free.app/transcribe")
GEMMA_API_URL = os.getenv("GEMMA_API_URL", "https://ladybird-needed-lately.ngrok-free.app/summarize")


# =============================================================================
# AI 서비스 연동 함수들
# =============================================================================

async def call_whisper_api(audio_file_content: bytes, filename: str) -> str:
    """Whisper API를 호출하여 음성을 텍스트로 변환"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {'file': (filename, audio_file_content, 'audio/wav')}
            response = await client.post(WHISPER_API_URL, files=files)
            response.raise_for_status()

            result = response.json()
            return result.get('transcript', '')
    except Exception as e:
        print(f"Whisper API 호출 실패: {str(e)}")
        return f"음성 변환 실패: {str(e)}"


async def call_gemma_api(script_text: str) -> str:
    """Gemma API를 호출하여 텍스트를 요약"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {"script": script_text}
            response = await client.post(
                GEMMA_API_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            result = response.json()
            return result.get('summary', '')
    except Exception as e:
        print(f"Gemma API 호출 실패: {str(e)}")
        return f"요약 생성 실패: {str(e)}"


# =============================================================================
# 1. 음성 파일 업로드 API (명세서 1번) - 핵심 구현
# =============================================================================

class AudioUploadResult(BaseModel):
    success: bool
    message: str
    script: Optional[str] = None
    summary: Optional[str] = None


@app.post("/recording/upload-with-ai", response_model=AudioUploadResult, tags=["recording"])
async def upload_recording_with_ai(
        audio_file: UploadFile = File(...),
        appointment_id: int = Form(...)
):
    """
    음성 파일 업로드 및 AI 처리 (명세서 1번)
    - Whisper로 음성→텍스트 변환
    - Gemma로 텍스트 요약
    - appointment 레코드에 script, summary 저장
    """

    # 파일 검증
    if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="Audio file required")

    # appointment 존재 확인
    db = next(get_db())
    try:
        appointment = db.query(AppointmentType).filter(
            AppointmentType.appointment_id == appointment_id
        ).first()

        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")

        # 파일 내용 읽기
        audio_content = await audio_file.read()

        # 1단계: Whisper API로 음성→텍스트 변환
        print(f"Whisper API 호출 중... (파일: {audio_file.filename})")
        script_text = await call_whisper_api(audio_content, audio_file.filename)

        # 2단계: script를 appointment에 저장
        appointment.script = script_text
        db.commit()
        print(f"Script 저장 완료: {len(script_text)} 문자")

        # 3단계: Gemma API로 텍스트 요약
        summary_text = ""
        if script_text and "실패" not in script_text:
            print("Gemma API 호출 중...")
            summary_text = await call_gemma_api(script_text)

            # 4단계: summary를 appointment에 저장
            appointment.summary = summary_text
            db.commit()
            print(f"Summary 저장 완료: {len(summary_text)} 문자")

        return AudioUploadResult(
            success=True,
            message="음성 파일 처리가 완료되었습니다.",
            script=script_text,
            summary=summary_text
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")
    finally:
        db.close()


# =============================================================================
# 2. Memo 작성 API (명세서 6번)
# =============================================================================

class MemoUpdateRequest(BaseModel):
    memo: str


@app.post("/appointment/{appointment_id}/memo", tags=["appointment"])
def update_appointment_memo(
        appointment_id: int,
        memo_request: MemoUpdateRequest,
        db: Session = Depends(get_db)
):
    """
    Appointment memo 업데이트 (명세서 6번)
    """
    appointment = db.query(AppointmentType).filter(
        AppointmentType.appointment_id == appointment_id
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.memo = memo_request.memo
    db.commit()

    return {"success": True, "message": "Memo updated successfully"}


# =============================================================================
# 3. 환자 예약&노쇼 관련 세부정보 로드 (명세서 7번)
# =============================================================================

class PatientDetailResponse(BaseModel):
    # 환자 기본 정보
    patient_id: int = Field(alias="patientId")
    name: str
    gender: Optional[int] = None
    birthday: Optional[str] = None
    neighbourhood: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    emergency_contact: Optional[str] = Field(None, alias="emergencyContact")
    emergency_phone: Optional[str] = Field(None, alias="emergencyPhone")
    blood_type: Optional[str] = Field(None, alias="bloodType")

    # 통계 정보
    total_appointments: int = Field(alias="totalAppointments")
    no_show_count: int = Field(alias="noShowCount")
    no_show_rate: float = Field(alias="noShowRate")

    # 최근 예약들
    recent_appointments: List[AppointmentTypeOut] = Field(alias="recentAppointments")

    # 리마인더 통계
    total_reminders: int = Field(alias="totalReminders")

    class Config:
        populate_by_name = True


@app.get("/patient/{patient_id}/detailed", response_model=PatientDetailResponse, tags=["patient"])
def get_patient_detailed_info(patient_id: int, db: Session = Depends(get_db)):
    """
    환자 예약&노쇼 관련 세부정보 로드 (명세서 7번)
    """
    # 환자 기본 정보 조회
    patient = db.query(PatientType).filter(PatientType.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # 예약 통계 계산
    total_appointments = db.query(AppointmentType).filter(
        AppointmentType.patient_id == patient_id
    ).count()

    no_show_count = db.query(AppointmentType).filter(
        and_(
            AppointmentType.patient_id == patient_id,
            AppointmentType.no_show == True
        )
    ).count()

    no_show_rate = (no_show_count / total_appointments * 100) if total_appointments > 0 else 0

    # 최근 예약 목록 (최대 10개)
    recent_appointments = db.query(AppointmentType).filter(
        AppointmentType.patient_id == patient_id
    ).order_by(desc(AppointmentType.appointment_date)).limit(10).all()

    # 리마인더 통계
    total_reminders = db.query(ReminderHistType).filter(
        ReminderHistType.patient_id == patient_id
    ).count()

    return PatientDetailResponse(
        patientId=patient.patient_id,
        name=patient.name,
        gender=patient.gender,
        birthday=patient.birthday,
        neighbourhood=patient.neighbourhood,
        phone=patient.phone,
        email=patient.email,
        emergencyContact=patient.emergency_contact,
        emergencyPhone=patient.emergency_phone,
        bloodType=patient.blood_type,
        totalAppointments=total_appointments,
        noShowCount=no_show_count,
        noShowRate=round(no_show_rate, 1),
        recentAppointments=recent_appointments,
        totalReminders=total_reminders
    )


# =============================================================================
# 기존 API들 (이미 구현된 것들)
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


@app.get("/appointment/patient/{patient_id}", response_model=List[AppointmentTypeOut], tags=["appointment"])
def get_appointments_by_patient(patient_id: int, db: Session = Depends(get_db)):
    """특정 환자의 모든 예약 내역 조회"""
    patient = db.query(PatientType).filter(PatientType.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    appointments = db.query(AppointmentType).filter(
        AppointmentType.patient_id == patient_id
    ).order_by(desc(AppointmentType.appointment_date)).all()

    return appointments


@app.post("/appointment", response_model=AppointmentTypeOut, tags=["appointment"])
def create_appointment(appointment: AppointmentTypeCreate, db: Session = Depends(get_db)):
    """새로운 예약 생성 (명세서 2번)"""
    try:
        patient = db.query(PatientType).filter(PatientType.patient_id == appointment.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        appointment_data = appointment.dict()
        db_appointment = AppointmentType(**appointment_data)

        db.add(db_appointment)
        db.commit()
        db.refresh(db_appointment)

        return db_appointment
    except Exception as e:
        import traceback
        print("Error in create_appointment:", e)
        print(traceback.format_exc())
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.get("/appointment/{appointment_id}/script", response_model=str, tags=["appointment"])
def get_appointment_script(appointment_id: int, db: Session = Depends(get_db)):
    """특정 예약의 스크립트(대화록) 조회 (명세서 3번)"""
    appointment = db.query(AppointmentType).filter(AppointmentType.appointment_id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return appointment.script or ""


@app.get("/appointment/{appointment_id}/summary", response_model=str, tags=["appointment"])
def get_appointment_summary(appointment_id: int, db: Session = Depends(get_db)):
    """특정 예약의 요약 정보 조회 (명세서 4번)"""
    appointment = db.query(AppointmentType).filter(AppointmentType.appointment_id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return appointment.summary or ""


# =============================================================================
# 나머지 기존 API들...
# =============================================================================

@app.get("/reminder/patient/{patient_id}", response_model=List[ReminderHistTypeOut], tags=["reminder"])
def get_patient_reminders(patient_id: int, db: Session = Depends(get_db)):
    """특정 환자의 리마인더 히스토리 조회"""
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
    appointment = db.query(AppointmentType).filter(AppointmentType.appointment_id == request.appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    patient = db.query(PatientType).filter(PatientType.patient_id == request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    db_reminder = ReminderHistType(
        patient_id=request.patient_id,
        appointment_id=request.appointment_id,
        message_type=request.message_type,
        received_at=datetime.utcnow().isoformat()
    )
    db.add(db_reminder)
    db.commit()

    return {"success": True, "message": "Reminder sent successfully"}


@app.get("/dashboard/appointments/today", tags=["dashboard"])
def get_today_appointments(db: Session = Depends(get_db)):
    """오늘의 예약 현황"""
    today_str = date.today().isoformat()

    appointments_with_patients = db.query(
        AppointmentType, PatientType.name
    ).join(
        PatientType, AppointmentType.patient_id == PatientType.patient_id
    ).filter(
        AppointmentType.appointment_date == today_str
    ).all()

    result = []
    for appointment, patient_name in appointments_with_patients:
        reminder_count = db.query(ReminderHistType).filter(
            ReminderHistType.appointment_id == appointment.appointment_id
        ).count()

        last_reminder = db.query(ReminderHistType).filter(
            ReminderHistType.appointment_id == appointment.appointment_id
        ).order_by(desc(ReminderHistType.created_at)).first()

        appointment_data = {
            "appointmentId": appointment.appointment_id,
            "patientId": appointment.patient_id,
            "patientName": patient_name,
            "appointmentTime": appointment.appointment_time,
            "appointmentDate": appointment.appointment_date,
            "noShow": appointment.no_show,
            "reminderCount": reminder_count,
            "lastReminderReceived": last_reminder is not None and last_reminder.received_at is not None
        }
        result.append(appointment_data)

    return result


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
        "timestamp": datetime.utcnow().isoformat(),
        "base_url": "http://localhost:8080",
        "ai_services": {
            "whisper_url": WHISPER_API_URL,
            "gemma_url": GEMMA_API_URL
        }
    }


@app.get("/health", tags=["default"])
def health_check():
    """헬스체크"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# =============================================================================
# AI 서비스 상태 확인 엔드포인트
# =============================================================================

@app.get("/ai/status", tags=["ai"])
async def check_ai_services():
    """AI 서비스 상태 확인"""
    whisper_status = "down"
    gemma_status = "down"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Whisper 서비스 확인
            try:
                whisper_response = await client.get(WHISPER_API_URL.replace('/transcribe', '/health'))
                if whisper_response.status_code == 200:
                    whisper_status = "up"
            except:
                pass

            # Gemma 서비스 확인
            try:
                gemma_response = await client.get(GEMMA_API_URL.replace('/summarize', '/health'))
                if gemma_response.status_code == 200:
                    gemma_status = "up"
            except:
                pass
    except Exception as e:
        pass

    return {
        "whisper": {
            "url": WHISPER_API_URL,
            "status": whisper_status
        },
        "gemma": {
            "url": GEMMA_API_URL,
            "status": gemma_status
        }
    }