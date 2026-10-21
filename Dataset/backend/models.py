from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    analyses = relationship("AnalysisHistory", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("SuspiciousReport", back_populates="user", cascade="all, delete-orphan")


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    analysis_type = Column(String(20), nullable=False)
    input_preview = Column(Text, nullable=True)
    full_content = Column(Text, nullable=True)
    youtube_url = Column(String(500), nullable=True)
    video_id = Column(String(50), nullable=True)
    video_title = Column(String(500), nullable=True)
    result = Column(String(20), nullable=False)
    prediction = Column(Integer, nullable=False)
    prediction_strength = Column(String(20), nullable=True)
    decision_score = Column(Float, nullable=True)
    indicators = Column(Text, nullable=True)
    transcript_status = Column(String(50), nullable=True)
    transcript_length = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="analyses")
    reports = relationship("SuspiciousReport", back_populates="analysis", cascade="all, delete-orphan")


class SuspiciousReport(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_history.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reporter_name = Column(String(120), nullable=False)
    reason = Column(String(80), nullable=False)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    analysis = relationship("AnalysisHistory", back_populates="reports")
    user = relationship("User", back_populates="reports")
