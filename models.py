from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Boolean, DateTime, Time
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class PatientType(Base):
    """프론트엔드 PatientType 인터페이스에 맞춤"""
    __tablename__ = "patients"

    patient_id = Column("patient_id", Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    gender = Column(Integer, nullable=True)  # 0: 남성, 1: 여성
    birthday = Column(Date, nullable=True)
    neighbourhood = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    emergency_contact = Column("emergency_contact", String(255), nullable=True)
    emergency_phone = Column("emergency_phone", String(20), nullable=True)
    blood_type = Column("blood_type", String(10), nullable=True)
    created_at = Column("created_at", DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 설정
    appointments = relationship("AppointmentType", back_populates="patient")
    reminders = relationship("ReminderHistType", back_populates="patient")


class AppointmentType(Base):
    """프론트엔드 AppointmentType 인터페이스에 맞춤"""
    __tablename__ = "appointments"

    appointment_id = Column("appointment_id", Integer, primary_key=True, index=True)
    patient_id = Column("patient_id", Integer, ForeignKey("patients.patient_id"), nullable=False)
    memo = Column(Text, nullable=True)
    script = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    no_show = Column("no_show", Boolean, default=False)
    appointment_date = Column("appointment_date", Date, nullable=False)
    appointment_time = Column("appointment_time", Time, nullable=True)
    created_at = Column("created_at", DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 설정
    patient = relationship("PatientType", back_populates="appointments")
    reminders = relationship("ReminderHistType", back_populates="appointment")


class ReminderHistType(Base):
    """프론트엔드 ReminderHistType 인터페이스에 맞춤"""
    __tablename__ = "reminder_history"

    reminder_hist_id = Column("reminder_hist_id", Integer, primary_key=True, index=True)
    patient_id = Column("patient_id", Integer, ForeignKey("patients.patient_id"), nullable=False)
    appointment_id = Column("appointment_id", Integer, ForeignKey("appointments.appointment_id"), nullable=False)
    message_type = Column("message_type", String(50), nullable=False)  # 'SMS', 'EMAIL', 'CALL'
    received_at = Column("received_at", DateTime, nullable=True)
    created_at = Column("created_at", DateTime, default=datetime.utcnow, nullable=False)

    # 관계 설정
    patient = relationship("PatientType", back_populates="reminders")
    appointment = relationship("AppointmentType", back_populates="reminders")
