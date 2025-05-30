from pydantic import BaseModel, Field
from datetime import date, datetime, time
from typing import Optional, List


# 프론트엔드 PatientType에 맞춘 스키마들
class PatientTypeBase(BaseModel):
    name: str
    gender: Optional[int] = None  # 1: 남성, 2: 여성
    birthday: Optional[date] = None
    neighbourhood: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    emergencyContact: Optional[str] = Field(None, alias="emergency_contact")
    emergencyPhone: Optional[str] = Field(None, alias="emergency_phone")
    bloodType: Optional[str] = Field(None, alias="blood_type")


class PatientTypeCreate(PatientTypeBase):
    pass


class PatientTypeUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[int] = None
    birthday: Optional[date] = None
    neighbourhood: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    emergencyContact: Optional[str] = None
    emergencyPhone: Optional[str] = None
    bloodType: Optional[str] = None


class PatientTypeOut(PatientTypeBase):
    patientId: int = Field(alias="patient_id")
    createdAt: datetime = Field(alias="created_at")

    class Config:
        from_attributes = True
        populate_by_name = True


# 프론트엔드 AppointmentType에 맞춘 스키마들
class AppointmentTypeBase(BaseModel):
    patientId: int = Field(alias="patient_id")
    memo: Optional[str] = None
    script: Optional[str] = None
    summary: Optional[str] = None
    noShow: bool = Field(default=False, alias="no_show")
    appointmentDate: date = Field(alias="appointment_date")
    appointmentTime: Optional[time] = Field(None, alias="appointment_time")


class AppointmentTypeCreate(AppointmentTypeBase):
    pass


class AppointmentTypeUpdate(BaseModel):
    memo: Optional[str] = None
    script: Optional[str] = None
    summary: Optional[str] = None
    noShow: Optional[bool] = None
    appointmentDate: Optional[date] = None
    appointmentTime: Optional[time] = None


class AppointmentTypeOut(AppointmentTypeBase):
    appointmentId: int = Field(alias="appointment_id")

    class Config:
        from_attributes = True
        populate_by_name = True


# 간호사 대시보드용 확장된 Appointment 데이터
class AppointmentWithPatientInfo(AppointmentTypeOut):
    patientName: str
    reminderCount: int = 0
    lastReminderReceived: bool = False


# 프론트엔드 ReminderHistType에 맞춘 스키마들
class ReminderHistTypeBase(BaseModel):
    patientId: int = Field(alias="patient_id")
    appointmentId: int = Field(alias="appointment_id")
    messageType: str = Field(alias="message_type")  # 'SMS', 'EMAIL', 'CALL'
    receivedAt: Optional[datetime] = Field(None, alias="received_at")


class ReminderHistTypeCreate(ReminderHistTypeBase):
    pass


class ReminderHistTypeOut(ReminderHistTypeBase):
    reminderHistId: int = Field(alias="reminder_hist_id")
    createdAt: datetime = Field(alias="created_at")

    class Config:
        from_attributes = True
        populate_by_name = True


# API 응답 스키마들
class AudioUploadResponse(BaseModel):
    success: bool
    transcription: str
    summary: Optional[str] = None


class ReminderSendResponse(BaseModel):
    success: bool
    sentAt: datetime


class AppointmentListResponse(BaseModel):
    appointments: List[AppointmentWithPatientInfo]


# 검색/필터링용 스키마들
class AppointmentFilterParams(BaseModel):
    date: Optional[date] = None
    patientName: Optional[str] = None
    noShow: Optional[bool] = None


# 노쇼 업데이트용 스키마
class NoShowUpdate(BaseModel):
    noShow: bool


# 추가 스키마들 (main.py에서 사용)
class ReminderSendRequest(BaseModel):
    patientId: int
    appointmentId: int
    messageType: str


class RecordingUploadResponse(BaseModel):
    transcription: str
    summary: str
    success: bool


class TodayAppointmentResponse(BaseModel):
    appointmentId: int
    patientId: int
    patientName: str
    appointmentTime: Optional[str] = None
    appointmentDate: str
    noShow: bool
    reminderCount: int
    lastReminderReceived: bool


class NoShowRiskResponse(BaseModel):
    riskPercentage: float
    riskLevel: str
