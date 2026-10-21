"""
validate_text_v3.py — Text validation suite for model_v3

Tests 10 hardcoded examples (5 credible, 5 suspicious).
Label convention: 0=Suspicious, 1=Credible
"""
import sys
import joblib

MODEL_PATH = "model_v3.pkl"
VEC_PATH = "vectorizer_v3.pkl"


def main():
    print("=" * 60)
    print("TEXT VALIDATION SUITE v3")
    print("=" * 60)

    try:
        model = joblib.load(MODEL_PATH)
        vec = joblib.load(VEC_PATH)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Run train_v3.py first to generate model_v3.pkl and vectorizer_v3.pkl")
        sys.exit(1)

    print(f"Model type: {type(model).__name__}")
    print(f"Vocabulary size: {len(vec.vocabulary_)}")
    print(f"Label mapping: 0=Suspicious, 1=Credible")
    print()

    test_cases = [
        # Credible examples (expected label = 1)
        {
            "text": "Photosynthesis is the process by which plants convert sunlight into glucose.",
            "expected": 1,
            "category": "Credible",
        },
        {
            "text": "The Earth revolves around the Sun.",
            "expected": 1,
            "category": "Credible",
        },
        {
            "text": "Neural networks are machine learning models.",
            "expected": 1,
            "category": "Credible",
        },
        {
            "text": "Python is a programming language.",
            "expected": 1,
            "category": "Credible",
        },
        {
            "text": "Water boils at 100°C at sea level.",
            "expected": 1,
            "category": "Credible",
        },
        # Suspicious examples (expected label = 0)
        {
            "text": "The Earth is flat and NASA hides the truth.",
            "expected": 0,
            "category": "Suspicious",
        },
        {
            "text": "Vaccines contain government tracking microchips.",
            "expected": 0,
            "category": "Suspicious",
        },
        {
            "text": "Drinking bleach cures all diseases.",
            "expected": 0,
            "category": "Suspicious",
        },
        {
            "text": "The moon landing was filmed in a studio.",
            "expected": 0,
            "category": "Suspicious",
        },
        {
            "text": "Scientists are hiding free energy technology.",
            "expected": 0,
            "category": "Suspicious",
        },
    ]

    passed = 0
    failed = 0
    results = []

    for tc in test_cases:
        text = tc["text"]
        expected = tc["expected"]
        category = tc["category"]

        X = vec.transform([text])
        pred = model.predict(X)[0]

        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)[0]
            confidence = max(proba) * 100
            prob_str = f"P(Susp)={proba[0]:.3f} P(Cred)={proba[1]:.3f}"
        elif hasattr(model, "decision_function"):
            score = model.decision_function(X)[0]
            confidence = abs(score) * 50 + 50  # approximate
            prob_str = f"score={score:.3f}"
        else:
            confidence = 0
            prob_str = "N/A"

        predicted_label = "Credible" if pred == 1 else "Suspicious"
        correct = pred == expected
        status = "✅ PASS" if correct else "❌ FAIL"

        if correct:
            passed += 1
        else:
            failed += 1

        print(f"  {status} | {predicted_label:10s} (conf={confidence:.1f}%) | Expected: {category:10s} | {prob_str}")
        print(f"         Text: {text}")
        print()

        results.append({
            "text": text,
            "expected": category,
            "predicted": predicted_label,
            "correct": correct,
            "confidence": round(confidence, 1),
        })

    print("=" * 60)
    print(f"RESULTS: {passed}/{passed + failed} PASSED")
    print("=" * 60)

    if failed > 0:
        print(f"\n❌ {failed} test(s) FAILED")
        sys.exit(1)
    else:
        print("\n✅ ALL TESTS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
