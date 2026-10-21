import json
import re
from collections import Counter

SENSATIONAL_WORDS = [
    "shocking", "unbelievable", "incredible", "explosive", "bombshell",
    "outrageous", "mind-blowing", "jaw-dropping", "devastating", "terrifying",
    "horrifying", "scandal", "conspiracy", "cover-up", "exposed", "secret",
    "viral", "insane", "crazy", "miracle", "destroyed", "slammed", "epic",
]

CLICKBAIT_PHRASES = [
    "you won't believe", "what happens next", "shocking truth",
    "they don't want you to know", "this will change everything",
    "number one will shock you", "one weird trick", "gone wrong",
    "must see", "watch till the end", "doctors hate", "you need to see",
    "before it's deleted", "mainstream media won't tell", "click here",
    "find out why", "the truth about", "you'll never guess",
]

URGENCY_WORDS = [
    "urgent", "immediately", "right now", "hurry", "limited time",
    "act fast", "don't wait", "last chance", "breaking", "alert",
    "expires", "deadline", "before it's too late", "time is running out",
]

EMOTIONAL_PHRASES = [
    "you'll cry", "heartbreaking", "outraged", "furious", "disgusting",
    "make you angry", "feel sick", "can't believe", "lost faith",
    "emotional", "devastated", "terrified", "hate this", "love this",
    "manipulated", "betrayed", "wake up", "open your eyes",
]

SUSPICIOUS_WORDING = [
    "guaranteed", "100% proof", "they are hiding", "big pharma",
    "deep state", "fake news", "real truth", "do your research",
    "share before deleted", "censored", "whistleblower", "leaked",
]


def detect_indicators(text: str) -> list[str]:
    """Derive rule-based indicators from observable text properties."""
    indicators: list[str] = []
    if not text or len(text.strip()) < 20:
        return indicators

    lower = text.lower()
    words = re.findall(r"[a-z']+", lower)

    sensational_hits = [w for w in SENSATIONAL_WORDS if w in lower]
    if len(sensational_hits) >= 2:
        indicators.append("Excessive sensational language")

    clickbait_hits = [p for p in CLICKBAIT_PHRASES if p in lower]
    if clickbait_hits:
        indicators.append("Clickbait patterns")

    urgency_hits = [w for w in URGENCY_WORDS if w in lower]
    if len(urgency_hits) >= 2:
        indicators.append("Repeated urgency words")

    emotional_hits = [p for p in EMOTIONAL_PHRASES if p in lower]
    if emotional_hits:
        indicators.append("Emotional manipulation")

    suspicious_hits = [p for p in SUSPICIOUS_WORDING if p in lower]
    if suspicious_hits:
        indicators.append("Suspicious wording")

    if len(words) >= 12:
        ngrams = [" ".join(words[i : i + 4]) for i in range(len(words) - 3)]
        min_repeats = 3 if len(words) < 200 else max(6, int(len(words) * 0.015))
        repeated = [ng for ng, count in Counter(ngrams).items() if count >= min_repeats]
        if repeated and "Suspicious wording" not in indicators:
            indicators.append("Suspicious wording")

    alpha_chars = [c for c in text if c.isalpha()]
    if len(alpha_chars) >= 30:
        caps_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
        if caps_ratio >= 0.25:
            indicators.append("Excessive capitalization")

    word_count = max(len(words), 1)
    exclamation_density = text.count("!") / word_count
    if exclamation_density >= 0.08 and "Excessive sensational language" not in indicators:
        indicators.append("Excessive sensational language")

    return list(dict.fromkeys(indicators))
