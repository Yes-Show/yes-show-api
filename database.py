from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# PostgreSQL 연결 설정 (환경변수 또는 기본값)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/yes_show")

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    echo=True,  # 개발 시 SQL 쿼리 로그 출력 (프로덕션에서는 False로 설정)
    pool_pre_ping=True  # 연결 상태 확인
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성 (모든 모델의 부모 클래스)
Base = declarative_base()


def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """데이터베이스 초기화 (테이블 생성)"""
    from models import PatientType, AppointmentType, ReminderHistType
    Base.metadata.create_all(bind=engine)
    print("데이터베이스 테이블이 생성되었습니다.")


if __name__ == "__main__":
    # 직접 실행시 데이터베이스 초기화
    init_db()
