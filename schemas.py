from pydantic import BaseModel, Field
from datetime import date, datetime, time
from typing import Optional, List


# 프론트엔드 PatientType에 맞춘 스키마들
class PatientTypeBase(BaseModel):
    name: str
    gender: Optional[int] = None  # 0: 남성, 1: 여성
    birthday: Optional[date] = None
    neighbourhood: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    emergency_contact: Optional[str] = Field(None, alias="emergencyContact")
    emergency_phone: Optional[str] = Field(None, alias="emergencyPhone")
    blood_type: Optional[str] = Field(None, alias="bloodType")


class PatientTypeCreate(PatientTypeBase):
    pass


class PatientTypeUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[int] = None
    birthday: Optional[date] = None
    neighbourhood: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    emergency_contact: Optional[str] = Field(None, alias="emergencyContact")
    emergency_phone: Optional[str] = Field(None, alias="emergencyPhone")
    blood_type: Optional[str] = Field(None, alias="bloodType")


class PatientTypeOut(PatientTypeBase):
    patient_id: int = Field(alias="patientId")
    created_at: datetime = Field(alias="createdAt")

    class Config:
        from_attributes = True
        populate_by_name = True


# 프론트엔드 AppointmentType에 맞춘 스키마들
class AppointmentTypeBase(BaseModel):
    patient_id: int = Field(alias="patientId")
    memo: Optional[str] = None
    script: Optional[str] = None
    summary: Optional[str] = None
    no_show: bool = Field(default=False, alias="noShow")
    appointment_date: date = Field(alias="appointmentDate")
    appointment_time: Optional[time] = Field(None, alias="appointmentTime")


class AppointmentTypeCreate(AppointmentTypeBase):
    pass


class AppointmentTypeUpdate(BaseModel):
    memo: Optional[str] = None
    script: Optional[str] = None
    summary: Optional[str] = None
    no_show: Optional[bool] = Field(None, alias="noShow")
    appointment_date: Optional[date] = Field(None, alias="appointmentDate")
    appointment_time: Optional[time] = Field(None, alias="appointmentTime")


class AppointmentTypeOut(AppointmentTypeBase):
    appointment_id: int = Field(alias="appointmentId")

    class Config:
        from_attributes = True
        populate_by_name = True


# 간호사 대시보드용 확장된 Appointment 데이터
class AppointmentWithPatientInfo(AppointmentTypeOut):
    patient_name: str = Field(alias="patientName")
    reminder_count: int = Field(0, alias="reminderCount")
    last_reminder_received: bool = Field(False, alias="lastReminderReceived")


# 프론트엔드 ReminderHistType에 맞춘 스키마들
class ReminderHistTypeBase(BaseModel):
    patient_id: int = Field(alias="patientId")
    appointment_id: int = Field(alias="appointmentId")
    message_type: str = Field(alias="messageType")  # 'SMS', 'EMAIL', 'CALL'
    received_at: Optional[datetime] = Field(None, alias="receivedAt")


class ReminderHistTypeCreate(ReminderHistTypeBase):
    pass


class ReminderHistTypeOut(ReminderHistTypeBase):
    reminder_hist_id: int = Field(alias="reminderHistId")
    created_at: datetime = Field(alias="createdAt")

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
    sent_at: datetime = Field(alias="sentAt")


class AppointmentListResponse(BaseModel):
    appointments: List[AppointmentWithPatientInfo]


# 검색/필터링용 스키마들
class AppointmentFilterParams(BaseModel):
    date: Optional[date] = None
    patient_name: Optional[str] = Field(None, alias="patientName")
    no_show: Optional[bool] = Field(None, alias="noShow")


# 노쇼 업데이트용 스키마
class NoShowUpdate(BaseModel):
    no_show: bool = Field(alias="noShow")


# 추가 스키마들 (main.py에서 사용)
class ReminderSendRequest(BaseModel):
    patient_id: int = Field(alias="patientId")
    appointment_id: int = Field(alias="appointmentId")
    message_type: str = Field(alias="messageType")


class RecordingUploadResponse(BaseModel):
    transcription: str
    summary: str
    success: bool


class TodayAppointmentResponse(BaseModel):
    appointment_id: int = Field(alias="appointmentId")
    patient_id: int = Field(alias="patientId")
    patient_name: str = Field(alias="patientName")
    appointment_time: Optional[str] = Field(None, alias="appointmentTime")
    appointment_date: str = Field(alias="appointmentDate")
    no_show: bool = Field(alias="noShow")
    reminder_count: int = Field(alias="reminderCount")
    last_reminder_received: bool = Field(alias="lastReminderReceived")


class NoShowRiskResponse(BaseModel):
    risk_percentage: float = Field(alias="riskPercentage")
    risk_level: str = Field(alias="riskLevel")
