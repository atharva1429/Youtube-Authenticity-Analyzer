import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.auth import (  # noqa: E402
    get_current_user,
    get_session_secret,
    hash_password,
    login_user,
    logout_user,
    verify_password,
)
from backend.database import get_db, init_db  # noqa: E402
from backend.ml_service import (  # noqa: E402
    _prediction_strength,
    _recommendation,
    _risk_level,
    analyze_text,
    calculate_confidence,
    indicators_to_json,
)
from backend.models import AnalysisHistory, SuspiciousReport, User  # noqa: E402
from backend.schemas import (  # noqa: E402
    AnalysisResponse,
    AnalyticsTrends,
    DailyTrend,
    DashboardStats,
    HistoryDetail,
    HistoryItem,
    MessageResponse,
    ReportAnalytics,
    ReportCreate,
    ReportItem,
    TextAnalysisRequest,
    UserLogin,
    UserRegister,
    UserResponse,
    YouTubeAnalysisRequest,
    parse_indicators,
)
from backend.youtube_service import analyze_youtube, classify_youtube_error  # noqa: E402

REPORT_REASONS = {
    "Fake News",
    "Misinformation",
    "Manipulated Content",
    "Clickbait",
    "Hate Speech",
    "Other",
}

app = FastAPI(
    title="YouTube Authenticity Analyzer",
    version="2.0.0",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    try:
        body_bytes = await request.body()
        body_str = body_bytes.decode("utf-8", errors="replace")
    except Exception:
        body_str = "<could not read body>"
    print("\n==========================================")
    print("VALIDATION ERROR CAPTURED:")
    print("URL:", request.url)
    print("RAW REQUEST BODY RECEIVED:", repr(body_str))
    print("VALIDATION ERRORS:", exc.errors())
    print("==========================================\n")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=get_session_secret(), same_site="lax")


@app.on_event("startup")
def on_startup():
    init_db()


def _report_counts(db: Session, user_id: int) -> dict[int, int]:
    rows = (
        db.query(SuspiciousReport.analysis_id, func.count(SuspiciousReport.id))
        .filter(SuspiciousReport.user_id == user_id)
        .group_by(SuspiciousReport.analysis_id)
        .all()
    )
    return {analysis_id: count for analysis_id, count in rows}


def _history_item(item: AnalysisHistory, report_count: int) -> HistoryItem:
    score = item.decision_score if item.decision_score is not None else 0.0
    credible = item.result == "credible"
    strength = item.prediction_strength or _prediction_strength(score)
    if item.decision_score is not None:
        confidence = calculate_confidence(score)
    elif item.result != "error":
        confidence = 85.0 if strength == "High" else (72.0 if strength == "Medium" else 60.0)
    else:
        confidence = None

    risk = _risk_level(credible, strength) if item.result != "error" else "N/A"
    rec = _recommendation(credible) if item.result != "error" else "Analysis failed."
    text_val = item.full_content or item.input_preview or ""
    w_count = item.transcript_length if item.transcript_length is not None else (len(text_val.split()) if text_val else 0)
    c_count = len(text_val)

    created_at_val = item.created_at
    if created_at_val and created_at_val.tzinfo is None:
        created_at_val = created_at_val.replace(tzinfo=timezone.utc)

    return HistoryItem(
        id=item.id,
        analysis_type=item.analysis_type,
        input_preview=item.input_preview,
        youtube_url=item.youtube_url,
        video_id=item.video_id,
        video_title=item.video_title,
        result=item.result,
        prediction=item.prediction,
        prediction_strength=strength,
        confidence_score=confidence,
        risk_level=risk,
        recommendation=rec,
        transcript_status=item.transcript_status,
        transcript_length=w_count,
        word_count=w_count,
        character_count=c_count,
        created_at=created_at_val,
        reported=report_count > 0,
        report_count=report_count,
    )


def _save_history(db: Session, user_id: int, **kwargs) -> AnalysisHistory:
    now_utc = datetime.now(timezone.utc)
    history = AnalysisHistory(user_id=user_id, created_at=now_utc, **kwargs)
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def _analysis_response(history: AnalysisHistory, result: dict, report_count: int = 0) -> AnalysisResponse:
    text_val = history.full_content or history.input_preview or ""
    w_count = result.get("transcript_length") or (len(text_val.split()) if text_val else 0)
    c_count = len(text_val)

    return AnalysisResponse(
        prediction=result["prediction"],
        result=result["result"],
        label=result["label"],
        prediction_strength=result.get("prediction_strength"),
        decision_score=result.get("decision_score"),
        confidence_score=result.get("confidence_score"),
        risk_level=result.get("risk_level"),
        recommendation=result.get("recommendation"),
        indicators=result.get("indicators", []),
        transcript_status=result.get("transcript_status"),
        transcript_length=w_count,
        word_count=w_count,
        character_count=c_count,
        youtube_url=result.get("youtube_url"),
        video_id=result.get("video_id"),
        video_title=result.get("video_title"),
        history_id=history.id,
        reported=report_count > 0,
        success=True,
    )


def _export_payload(item: AnalysisHistory) -> dict:
    score = item.decision_score if item.decision_score is not None else 0.0
    credible = item.result == "credible"
    strength = item.prediction_strength or _prediction_strength(score)
    confidence = calculate_confidence(score) if item.decision_score is not None else None
    risk = _risk_level(credible, strength) if item.result != "error" else "N/A"
    rec = _recommendation(credible) if item.result != "error" else "Analysis failed."
    text_val = item.full_content or item.input_preview or ""
    w_count = item.transcript_length if item.transcript_length is not None else (len(text_val.split()) if text_val else 0)

    created_at_iso = None
    if item.created_at:
        dt = item.created_at if item.created_at.tzinfo else item.created_at.replace(tzinfo=timezone.utc)
        created_at_iso = dt.isoformat()

    return {
        "analysis_id": item.id,
        "date_time": created_at_iso,
        "analysis_type": item.analysis_type,
        "prediction": item.result,
        "prediction_label": "Credible Content ✅" if item.result == "credible" else "Suspicious Content ⚠️",
        "prediction_strength": strength,
        "confidence_score": confidence,
        "risk_level": risk,
        "recommendation": rec,
        "word_count": w_count,
        "character_count": len(text_val),
        "original_url": item.youtube_url,
        "transcript_preview": item.input_preview,
        "indicators": parse_indicators(item.indicators),
        "decision_score": item.decision_score,
    }




@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    from backend.ml_service import model, vectorizer

    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return {
        "status": "online",
        "api_server": "online",
        "model": "Logistic Regression (v4)",
        "vectorizer": "TF-IDF (v4 Domain-Adapted)",
        "database": "SQLite",
        "model_loaded": model is not None,
        "vectorizer_loaded": vectorizer is not None,
        "database_connected": db_ok,
    }


@app.post("/api/auth/register", response_model=UserResponse)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = (
        db.query(User)
        .filter((User.username == payload.username) | (User.email == payload.email))
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already registered")

    user = User(
        username=payload.username.strip(),
        email=payload.email.strip().lower(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/auth/login", response_model=UserResponse)
def login(payload: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username.strip()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    login_user(request, user)
    return user


@app.post("/api/auth/logout", response_model=MessageResponse)
def logout(request: Request):
    logout_user(request)
    return MessageResponse(message="Logged out successfully")


@app.get("/api/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/api/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    base = db.query(AnalysisHistory).filter(AnalysisHistory.user_id == current_user.id)
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_local = datetime.now().strftime("%Y-%m-%d")
    today_count = base.filter(
        (func.date(AnalysisHistory.created_at) == today_utc) |
        (func.date(AnalysisHistory.created_at) == today_local)
    ).count()
    return DashboardStats(
        total_analyses=base.count(),
        text_analyses=base.filter(AnalysisHistory.analysis_type == "text").count(),
        youtube_analyses=base.filter(AnalysisHistory.analysis_type == "youtube").count(),
        credible_results=base.filter(AnalysisHistory.result == "credible").count(),
        suspicious_results=base.filter(AnalysisHistory.result == "suspicious").count(),
        error_results=base.filter(AnalysisHistory.result == "error").count(),
        total_reports=db.query(SuspiciousReport).filter(SuspiciousReport.user_id == current_user.id).count(),
        today_analyses=today_count,
    )


def _build_trends(items: list[AnalysisHistory], days: int, label_fmt: str) -> list[DailyTrend]:
    now = datetime.now(timezone.utc).date()
    buckets: dict[str, dict] = {}
    ordered_keys: list[str] = []
    for i in range(days - 1, -1, -1):
        day = now - timedelta(days=i)
        key = day.strftime(label_fmt)
        if key not in buckets:
            buckets[key] = {"date": key, "count": 0, "credible": 0, "suspicious": 0}
            ordered_keys.append(key)

    for item in items:
        if not item.created_at:
            continue
        created = item.created_at.date() if hasattr(item.created_at, "date") else item.created_at
        age = (now - created).days
        if age < 0 or age >= days:
            continue
        key = created.strftime(label_fmt)
        if key in buckets:
            buckets[key]["count"] += 1
            if item.result == "credible":
                buckets[key]["credible"] += 1
            elif item.result == "suspicious":
                buckets[key]["suspicious"] += 1

    return [DailyTrend(**buckets[k]) for k in ordered_keys]



@app.get("/api/analytics/trends", response_model=AnalyticsTrends)
def analytics_trends(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.user_id == current_user.id)
        .order_by(AnalysisHistory.created_at.desc())
        .all()
    )
    return AnalyticsTrends(
        daily=_build_trends(items, 7, "%a"),
        weekly=_build_trends(items, 28, "%b %d"),
    )


@app.post("/api/analyze/text", response_model=AnalysisResponse)
def analyze_text_endpoint(
    payload: TextAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please enter some text.")

    result = analyze_text(text)
    preview = text[:500] + ("..." if len(text) > 500 else "")

    history = _save_history(
        db,
        current_user.id,
        analysis_type="text",
        input_preview=preview,
        full_content=text,
        result=result["result"],
        prediction=result["prediction"],
        prediction_strength=result["prediction_strength"],
        decision_score=result["decision_score"],
        indicators=indicators_to_json(result["indicators"]),
    )
    return _analysis_response(history, result)


@app.post("/api/analyze/youtube", response_model=AnalysisResponse)
def analyze_youtube_endpoint(
    payload: YouTubeAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    print("\n[ENDPOINT REACHED] analyze_youtube_endpoint payload received:", payload)
    url = payload.url.strip()
    if not url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please enter a YouTube URL.")

    try:
        result = analyze_youtube(url)
    except ValueError as ve:
        if str(ve) == "Transcript text is empty":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_type": "empty_transcript",
                    "message": "No Speech Detected",
                    "detail": "The video contains no spoken words or the audio could not be transcribed.",
                    "transcript_status": "failed",
                },
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "invalid",
                "message": "Invalid YouTube URL",
                "detail": "Please provide a valid YouTube watch URL containing 'v='.",
                "transcript_status": "invalid",
            },
        )
    except Exception as exc:
        error_info = classify_youtube_error(str(exc))
        history = _save_history(
            db,
            current_user.id,
            analysis_type="youtube",
            youtube_url=url,
            input_preview=url,
            result="error",
            prediction=-1,
            transcript_status=error_info["transcript_status"],
        )
        print(f"\n[DEBUG] _save_history called with status: {error_info['transcript_status']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                **error_info,
                "history_id": history.id,
            },
        )

    transcript = result["transcript_text"]
    try:
        print(f"\n[DEBUG] Transcript fetch result (preview): {transcript[:100].encode('ascii', 'replace').decode('ascii')}...")
    except Exception:
        pass
    
    preview = transcript[:500] + ("..." if len(transcript) > 500 else "")
    print("\n[DEBUG] Saving successful analysis to history...")

    history = _save_history(
        db,
        current_user.id,
        analysis_type="youtube",
        input_preview=preview,
        full_content=transcript,
        youtube_url=url,
        video_id=result["video_id"],
        video_title=result.get("video_title"),
        result=result["result"],
        prediction=result["prediction"],
        prediction_strength=result["prediction_strength"],
        decision_score=result["decision_score"],
        indicators=indicators_to_json(result["indicators"]),
        transcript_status=result["transcript_status"],
        transcript_length=result["transcript_length"],
    )
    final_response = _analysis_response(history, result)
    try:
        print("\n[DEBUG] Final API response:", str(final_response.model_dump()).encode("ascii", "replace").decode("ascii"))
    except Exception:
        pass
    return final_response


@app.get("/api/history", response_model=list[HistoryItem])
def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    counts = _report_counts(db, current_user.id)
    items = (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.user_id == current_user.id)
        .order_by(AnalysisHistory.created_at.desc())
        .limit(200)
        .all()
    )
    return [_history_item(item, counts.get(item.id, 0)) for item in items]


@app.get("/api/history/{history_id}", response_model=HistoryDetail)
def get_history_detail(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.id == history_id, AnalysisHistory.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    report_count = (
        db.query(SuspiciousReport)
        .filter(SuspiciousReport.analysis_id == item.id, SuspiciousReport.user_id == current_user.id)
        .count()
    )
    return HistoryDetail(
        **_history_item(item, report_count).model_dump(),
        full_content=item.full_content or item.input_preview,
        indicators=parse_indicators(item.indicators),
        decision_score=item.decision_score,
    )


@app.get("/api/history/{history_id}/export/json")
def export_history_json(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.id == history_id, AnalysisHistory.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    payload = _export_payload(item)
    content = json.dumps(payload, indent=2)
    filename = f"analysis-{history_id}.json"
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/history/{history_id}/export/txt")
def export_history_txt(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.id == history_id, AnalysisHistory.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    payload = _export_payload(item)
    lines = [
        "YouTube Authenticity Analyzer — Analysis Report",
        "=" * 48,
        f"Date: {payload['date']}",
        f"Analysis Type: {payload['analysis_type']}",
        f"Prediction: {payload['prediction_label']}",
        f"Transcript Length: {payload['transcript_length'] or 'N/A'}",
        f"Original URL: {payload['original_url'] or 'N/A'}",
        "",
        "Transcript Preview:",
        payload["transcript_preview"] or "N/A",
    ]
    if payload["indicators"]:
        lines.extend(["", "Indicators Detected:", *[f"- {i}" for i in payload["indicators"]]])

    filename = f"analysis-{history_id}.txt"
    return Response(
        content="\n".join(lines),
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.delete("/api/history/{history_id}", response_model=MessageResponse)
def delete_history_item(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.id == history_id, AnalysisHistory.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    db.delete(item)
    db.commit()
    return MessageResponse(message="History item deleted")


@app.post("/api/reports", response_model=ReportItem)
def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.reason not in REPORT_REASONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid report reason")

    analysis = (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.id == payload.analysis_id, AnalysisHistory.user_id == current_user.id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    if analysis.result != "suspicious":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only suspicious content can be reported")

    report = SuspiciousReport(
        analysis_id=analysis.id,
        user_id=current_user.id,
        reporter_name=payload.reporter_name.strip(),
        reason=payload.reason,
        comments=(payload.comments or "").strip() or None,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return ReportItem(
        id=report.id,
        analysis_id=report.analysis_id,
        reporter_name=report.reporter_name,
        reason=report.reason,
        comments=report.comments,
        created_at=report.created_at,
        analysis_type=analysis.analysis_type,
        analysis_result=analysis.result,
        youtube_url=analysis.youtube_url,
        input_preview=analysis.input_preview,
    )


@app.get("/api/reports", response_model=list[ReportItem])
def list_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(SuspiciousReport, AnalysisHistory)
        .join(AnalysisHistory, SuspiciousReport.analysis_id == AnalysisHistory.id)
        .filter(SuspiciousReport.user_id == current_user.id)
        .order_by(SuspiciousReport.created_at.desc())
        .limit(200)
        .all()
    )
    return [
        ReportItem(
            id=report.id,
            analysis_id=report.analysis_id,
            reporter_name=report.reporter_name,
            reason=report.reason,
            comments=report.comments,
            created_at=report.created_at,
            analysis_type=analysis.analysis_type,
            analysis_result=analysis.result,
            youtube_url=analysis.youtube_url,
            input_preview=analysis.input_preview,
        )
        for report, analysis in rows
    ]


@app.get("/api/reports/analytics", response_model=ReportAnalytics)
def report_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    reports = (
        db.query(SuspiciousReport, AnalysisHistory)
        .join(AnalysisHistory, SuspiciousReport.analysis_id == AnalysisHistory.id)
        .filter(SuspiciousReport.user_id == current_user.id)
        .order_by(SuspiciousReport.created_at.desc())
        .all()
    )

    if not reports:
        return ReportAnalytics(total_reports=0, recent_reports=[], reason_breakdown={})

    reason_counter = Counter(r.reason for r, _ in reports)
    category_counter = Counter(a.analysis_type for _, a in reports)
    most_common_reason = reason_counter.most_common(1)[0][0] if reason_counter else None
    most_reported_category = category_counter.most_common(1)[0][0] if category_counter else None

    recent = [
        ReportItem(
            id=report.id,
            analysis_id=report.analysis_id,
            reporter_name=report.reporter_name,
            reason=report.reason,
            comments=report.comments,
            created_at=report.created_at,
            analysis_type=analysis.analysis_type,
            analysis_result=analysis.result,
            youtube_url=analysis.youtube_url,
            input_preview=analysis.input_preview,
        )
        for report, analysis in reports[:8]
    ]

    return ReportAnalytics(
        total_reports=len(reports),
        most_common_reason=most_common_reason,
        most_reported_category=most_reported_category,
        recent_reports=recent,
        reason_breakdown=dict(reason_counter),
    )
