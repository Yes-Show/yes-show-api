from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Boolean, DateTime, Time
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class PatientType(Base):
    """프론트엔드 PatientType 인터페이스에 맞춤"""
    __tablename__ = "patients"

    patientId = Column("patient_id", Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    gender = Column(Integer, nullable=True)  # 1: 남성, 2: 여성
    birthday = Column(Date, nullable=True)
    neighbourhood = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    emergencyContact = Column("emergency_contact", String(255), nullable=True)
    emergencyPhone = Column("emergency_phone", String(20), nullable=True)
    bloodType = Column("blood_type", String(10), nullable=True)
    createdAt = Column("created_at", DateTime, default=datetime.utcnow, nullable=False)
    updatedAt = Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 설정
    appointments = relationship("AppointmentType", back_populates="patient")
    reminders = relationship("ReminderHistType", back_populates="patient")


class AppointmentType(Base):
    """프론트엔드 AppointmentType 인터페이스에 맞춤"""
    __tablename__ = "appointments"

    appointmentId = Column("appointment_id", Integer, primary_key=True, index=True)
    patientId = Column("patient_id", Integer, ForeignKey("patients.patient_id"), nullable=False)
    memo = Column(Text, nullable=True)
    script = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    noShow = Column("no_show", Boolean, default=False)
    appointmentDate = Column("appointment_date", Date, nullable=False)
    appointmentTime = Column("appointment_time", Time, nullable=True)
    createdAt = Column("created_at", DateTime, default=datetime.utcnow, nullable=False)
    updatedAt = Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 설정
    patient = relationship("PatientType", back_populates="appointments")
    reminders = relationship("ReminderHistType", back_populates="appointment")


class ReminderHistType(Base):
    """프론트엔드 ReminderHistType 인터페이스에 맞춤"""
    __tablename__ = "reminder_history"

    reminderHistId = Column("reminder_hist_id", Integer, primary_key=True, index=True)
    patientId = Column("patient_id", Integer, ForeignKey("patients.patient_id"), nullable=False)
    appointmentId = Column("appointment_id", Integer, ForeignKey("appointments.appointment_id"), nullable=False)
    messageType = Column("message_type", String(50), nullable=False)  # 'SMS', 'EMAIL', 'CALL'
    receivedAt = Column("received_at", DateTime, nullable=True)
    createdAt = Column("created_at", DateTime, default=datetime.utcnow, nullable=False)

    # 관계 설정
    patient = relationship("PatientType", back_populates="reminders")
    appointment = relationship("AppointmentType", back_populates="reminders")
