import json
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class TextAnalysisRequest(BaseModel):
    text: str = Field(min_length=1)


class YouTubeAnalysisRequest(BaseModel):
    url: str = Field(default="", min_length=1)

    @model_validator(mode="before")
    @classmethod
    def extract_url(cls, data):
        if isinstance(data, dict):
            val = data.get("url") or data.get("youtube_url") or data.get("text") or data.get("link") or ""
            if isinstance(val, str):
                data["url"] = val.strip()
        return data



class AnalysisResponse(BaseModel):
    prediction: int
    result: str
    label: str
    prediction_strength: Optional[str] = None
    decision_score: Optional[float] = None
    confidence_score: Optional[float] = None
    risk_level: Optional[str] = None
    recommendation: Optional[str] = None
    indicators: list[str] = []
    transcript_status: Optional[str] = None
    transcript_length: Optional[int] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    youtube_url: Optional[str] = None
    video_id: Optional[str] = None
    video_title: Optional[str] = None
    history_id: Optional[int] = None
    reported: bool = False
    success: bool = True


class HistoryItem(BaseModel):
    id: int
    analysis_type: str
    input_preview: Optional[str] = None
    youtube_url: Optional[str] = None
    video_id: Optional[str] = None
    video_title: Optional[str] = None
    result: str
    prediction: int
    prediction_strength: Optional[str] = None
    confidence_score: Optional[float] = None
    risk_level: Optional[str] = None
    recommendation: Optional[str] = None
    transcript_status: Optional[str] = None
    transcript_length: Optional[int] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    created_at: datetime
    reported: bool = False
    report_count: int = 0

    class Config:
        from_attributes = True


class HistoryDetail(HistoryItem):
    full_content: Optional[str] = None
    indicators: list[str] = []
    decision_score: Optional[float] = None



class DashboardStats(BaseModel):
    total_analyses: int
    text_analyses: int
    youtube_analyses: int
    credible_results: int
    suspicious_results: int
    total_reports: int
    error_results: int
    today_analyses: int = 0


class DailyTrend(BaseModel):
    date: str
    count: int
    credible: int
    suspicious: int


class AnalyticsTrends(BaseModel):
    daily: list[DailyTrend] = []
    weekly: list[DailyTrend] = []


class ReportCreate(BaseModel):
    analysis_id: int
    reporter_name: str = Field(min_length=2, max_length=120)
    reason: str = Field(min_length=2, max_length=80)
    comments: Optional[str] = Field(default=None, max_length=2000)


class ReportItem(BaseModel):
    id: int
    analysis_id: int
    reporter_name: str
    reason: str
    comments: Optional[str] = None
    created_at: datetime
    analysis_type: Optional[str] = None
    analysis_result: Optional[str] = None
    youtube_url: Optional[str] = None
    input_preview: Optional[str] = None

    class Config:
        from_attributes = True


class ReportAnalytics(BaseModel):
    total_reports: int
    most_common_reason: Optional[str] = None
    most_reported_category: Optional[str] = None
    recent_reports: list[ReportItem] = []
    reason_breakdown: dict[str, int] = {}


class MessageResponse(BaseModel):
    message: str


def parse_indicators(raw: Optional[str]) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []
