import json
import math
from pathlib import Path

import joblib

from backend.text_indicators import detect_indicators

BASE_DIR = Path(__file__).resolve().parent.parent

model = joblib.load(BASE_DIR / "model_v4.pkl")
vectorizer = joblib.load(BASE_DIR / "vectorizer_v4.pkl")


def calculate_confidence(score: float) -> float:
    return round(100.0 / (1.0 + math.exp(-abs(score))), 1)


def _prediction_strength(score: float) -> str:
    magnitude = abs(score)

    if magnitude >= 0.8:
        return "High"

    if magnitude >= 0.25:
        return "Medium"

    return "Low"


def _risk_level(credible: bool, strength: str) -> str:
    if credible:
        return "Low Risk"

    if strength == "High":
        return "High Risk"

    if strength == "Medium":
        return "Medium Risk"

    return "Low Risk"


def _recommendation(credible: bool) -> str:
    if credible:
        return (
            "Content appears credible based on model analysis. "
            "Verify critical claims with trusted sources when necessary."
        )

    return (
        "Suspicious content detected by the model. "
        "Further verification from reliable sources is recommended."
    )


def predict_text(text: str) -> int:
    text_tfidf = vectorizer.transform([text])
    prediction = model.predict(text_tfidf)[0]
    return int(prediction)


def analyze_text(text: str) -> dict:
    text_tfidf = vectorizer.transform([text])

    prediction = int(model.predict(text_tfidf)[0])

    # XGBoost / RandomForest / LogisticRegression
    if hasattr(model, "predict_proba"):

        prob = float(model.predict_proba(text_tfidf)[0][1])

        score = prob

        confidence = round(
            max(prob, 1 - prob) * 100,
            1
        )

        strength_score = abs(prob - 0.5) * 2

    # LinearSVC fallback
    else:

        score = float(model.decision_function(text_tfidf)[0])

        confidence = calculate_confidence(score)

        strength_score = abs(score)

    if strength_score >= 0.8:
        strength = "High"
    elif strength_score >= 0.25:
        strength = "Medium"
    else:
        strength = "Low"

    credible = prediction == 1

    risk = _risk_level(credible, strength)

    recommendation = _recommendation(credible)

    indicators = detect_indicators(text) if not credible else []

    return {
        "prediction": prediction,
        "result": "credible" if credible else "suspicious",
        "label": (
            "Credible Content ✅"
            if credible
            else "Suspicious Content ⚠️"
        ),
        "prediction_strength": strength,
        "decision_score": round(score, 4),
        "confidence_score": confidence,
        "risk_level": risk,
        "recommendation": recommendation,
        "indicators": indicators,
    }


def indicators_to_json(indicators: list[str]) -> str:
    return json.dumps(indicators)


def analyze_transcript(text: str, chunk_size: int = 300, overlap: int = 100) -> dict:
    """Analyze a long transcript using sliding-window chunk evaluation.
    
    Splits text into overlapping chunks of ~chunk_size words (with step size = chunk_size - overlap),
    computes probability of credibility for each chunk, and calculates a robust composite score.
    """
    words = text.split()
    
    # Short text: classify directly
    if len(words) <= chunk_size:
        return analyze_text(text)
    
    # Split into sliding overlapping chunks
    step = max(chunk_size - overlap, 50)
    chunks = []
    for i in range(0, len(words), step):
        chunk_words = words[i:i + chunk_size]
        if len(chunk_words) >= 30:  # Skip trivial tail chunks
            chunks.append(" ".join(chunk_words))
    
    if not chunks:
        return analyze_text(text)
    
    # Classify each chunk and collect credibility probabilities
    chunk_probas = []
    for chunk in chunks:
        text_tfidf = vectorizer.transform([chunk])
        if hasattr(model, "predict_proba"):
            p_cred = float(model.predict_proba(text_tfidf)[0][1])
        else:
            p_cred = float(model.predict(text_tfidf)[0])
        chunk_probas.append(p_cred)
    
    mean_p = float(sum(chunk_probas) / len(chunk_probas))
    cred_chunks = sum(1 for p in chunk_probas if p >= 0.5)
    cred_ratio = float(cred_chunks / len(chunk_probas))
    
    # Composite score combines mean credibility with proportion of credible segments
    composite_score = 0.5 * mean_p + 0.5 * cred_ratio
    
    prediction = 1 if composite_score >= 0.5 else 0
    credible = prediction == 1
    
    score = composite_score
    confidence = round(max(composite_score, 1.0 - composite_score) * 100, 1)
    strength_score = abs(composite_score - 0.5) * 2
    
    if strength_score >= 0.8:
        strength = "High"
    elif strength_score >= 0.25:
        strength = "Medium"
    else:
        strength = "Low"
    
    risk = _risk_level(credible, strength)
    recommendation = _recommendation(credible)
    indicators = detect_indicators(text) if not credible else []
    
    return {
        "prediction": prediction,
        "result": "credible" if credible else "suspicious",
        "label": (
            "Credible Content ✅"
            if credible
            else "Suspicious Content ⚠️"
        ),
        "prediction_strength": strength,
        "decision_score": round(score, 4),
        "confidence_score": confidence,
        "risk_level": risk,
        "recommendation": recommendation,
        "indicators": indicators,
        "chunks_analyzed": len(chunk_probas),
    }