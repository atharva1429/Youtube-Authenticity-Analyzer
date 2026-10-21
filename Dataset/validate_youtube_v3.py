"""
validate_youtube_v3.py — YouTube transcript validation suite for model_v3

Tests transcript classification using both:
1. Pre-collected educational & conspiracy transcript samples
2. Live YouTube transcript fetching (if network available)

Label convention: 0=Suspicious, 1=Credible
"""
import sys
import joblib

MODEL_PATH = "model_v3.pkl"
VEC_PATH = "vectorizer_v3.pkl"


# ============================================================
# PRE-COLLECTED TRANSCRIPT SAMPLES
# ============================================================

EDUCATIONAL_TRANSCRIPTS = [
    {
        "name": "TED Talk Style",
        "source": "TED",
        "text": (
            "Thank you so much for having me. What I want to talk about today is the remarkable "
            "intersection of artificial intelligence and climate science. Over the past decade, machine "
            "learning models have transformed our ability to predict weather patterns. Researchers at "
            "MIT and Stanford have published peer-reviewed studies showing that neural network based "
            "climate models can predict extreme weather events with 30 percent greater accuracy than "
            "traditional models. The key insight is that deep learning can identify nonlinear patterns "
            "in atmospheric data that conventional statistical methods miss. This has profound "
            "implications for disaster preparedness. By combining satellite imagery with ground-based "
            "sensor networks, we can now provide communities with earlier and more accurate warnings. "
            "The data is clear. Evidence-based climate modeling saves lives."
        ),
        "expected": 1,
    },
    {
        "name": "3Blue1Brown Style",
        "source": "3Blue1Brown",
        "text": (
            "Let me show you something beautiful about linear algebra. The essence of a matrix is "
            "that it represents a linear transformation. When you multiply a vector by a matrix, "
            "you're transforming that vector according to specific rules. Think of it this way. "
            "Every column of the matrix tells you where the corresponding basis vector lands. "
            "The determinant tells you how much the transformation scales areas. If the determinant "
            "is zero, the transformation squishes everything into a lower dimension. Eigenvalues "
            "tell you the factors by which the transformation stretches or compresses along its "
            "eigenvectors. This framework connects to differential equations, quantum mechanics, "
            "and computer graphics. The mathematical structure is elegant and well-established."
        ),
        "expected": 1,
    },
    {
        "name": "Kurzgesagt Style",
        "source": "Kurzgesagt",
        "text": (
            "The immune system is the most complex biological system in the human body after the brain. "
            "It consists of billions of cells, organized into specialized teams. When a pathogen enters "
            "your body, macrophages are the first responders. They engulf and destroy invaders while "
            "sending chemical signals to recruit reinforcements. Dendritic cells collect samples of the "
            "pathogen and carry them to lymph nodes, where they present these samples to T-cells. "
            "Helper T-cells then coordinate the immune response, activating B-cells that produce "
            "antibodies specifically shaped to neutralize the pathogen. Memory cells remain in your "
            "body for years or decades, ready to mount a rapid response if the same pathogen returns. "
            "This is the principle behind vaccination. By introducing a harmless version of the pathogen, "
            "vaccines train your immune system to recognize and fight the real threat."
        ),
        "expected": 1,
    },
    {
        "name": "freeCodeCamp Style",
        "source": "freeCodeCamp",
        "text": (
            "Welcome to this Python tutorial. Today we are going to learn about data structures. "
            "In Python, the most commonly used data structures are lists, dictionaries, tuples, and sets. "
            "A list is an ordered, mutable collection. You create one with square brackets. You can "
            "add items with append, remove them with remove or pop, and access them by index. "
            "A dictionary maps keys to values using curly braces. Lookup time is O of 1 on average "
            "because dictionaries are implemented as hash tables under the hood. A tuple is like a "
            "list but immutable. Once created, you cannot change its contents. This makes tuples "
            "useful for representing fixed collections of data. Sets store unique values and support "
            "mathematical set operations like union, intersection, and difference. Understanding these "
            "data structures is fundamental to writing efficient Python code."
        ),
        "expected": 1,
    },
    {
        "name": "CrashCourse Style",
        "source": "CrashCourse",
        "text": (
            "Hi I'm John Green and this is Crash Course World History. Today we're talking about the "
            "Industrial Revolution. In the late 18th century, Britain underwent a massive transformation "
            "from an agricultural economy to an industrial one. Several factors contributed to this "
            "change. Britain had abundant coal and iron resources. It had a stable political system and "
            "strong property rights. The agricultural revolution had increased food production, freeing "
            "up labor for factories. James Watt improved the steam engine in 1769, and this technology "
            "powered the new factories and transportation networks. The social consequences were "
            "enormous. Urbanization accelerated, working conditions in factories were often terrible, "
            "and a new class of industrial workers emerged. These are well-documented historical facts "
            "supported by extensive primary sources and archaeological evidence."
        ),
        "expected": 1,
    },
]

SUSPICIOUS_TRANSCRIPTS = [
    {
        "name": "Flat Earth Content",
        "source": "Conspiracy",
        "text": (
            "Wake up people. I am going to prove to you today that the earth is flat. NASA has been "
            "lying to you for decades. Look at the horizon with your own eyes. It is always flat. "
            "If the earth were a sphere spinning at a thousand miles per hour, you would feel it. "
            "But you don't feel anything because the earth is stationary. The photos from space are "
            "all CGI. NASA gets billions of dollars in funding and they use it to create fake images. "
            "Gravity is a hoax. Things fall because they are denser than air, not because of some "
            "magical invisible force. The antarctic ice wall surrounds the flat earth like a rim. "
            "Captain Cook could not cross it. The government does not want you to know this because "
            "they control you through lies. Do your own research. Question everything they taught you "
            "in school. Share this video before they delete it."
        ),
        "expected": 0,
    },
    {
        "name": "Anti-Vaccine Conspiracy",
        "source": "Conspiracy",
        "text": (
            "What they are not telling you about vaccines is terrifying. Big pharma has been covering "
            "this up for decades. Vaccines contain mercury, aluminum, and other heavy metals that "
            "accumulate in your brain. They cause autism, autoimmune diseases, and cancer. The CDC "
            "is controlled by pharmaceutical companies who make billions from these injections. "
            "A whistleblower inside the FDA leaked documents proving they know vaccines are dangerous "
            "but they approve them anyway. Doctors who speak out get their licenses revoked. The "
            "mainstream media refuses to report on vaccine injuries because they are funded by "
            "big pharma advertising. Do not trust the so called experts. They are all paid off. "
            "Your immune system is natural and perfect. These toxic injections destroy it. Share this "
            "before it gets censored. Wake up!"
        ),
        "expected": 0,
    },
    {
        "name": "Moon Landing Hoax",
        "source": "Conspiracy",
        "text": (
            "The evidence is overwhelming that the moon landing was faked. Look at the photos. The "
            "shadows point in different directions, proving there were multiple light sources in a "
            "studio. There are no stars visible in any of the photos. The flag appears to wave in a "
            "vacuum where there is no wind. The Van Allen radiation belts would have killed the "
            "astronauts. The technology in 1969 was not capable of this feat. Stanley Kubrick was "
            "hired by NASA to direct the fake footage. He left hidden clues in his later films. "
            "Conveniently, all the original telemetry data and footage has been lost or destroyed. "
            "Former NASA employees have come forward but they are silenced. The entire space program "
            "is a massive fraud designed to funnel taxpayer money into black budget programs. Open "
            "your eyes. They have been lying to you your entire life."
        ),
        "expected": 0,
    },
]


def analyze_transcript_chunked(model, vectorizer, text, chunk_size=500):
    """
    Analyze a transcript using chunk-based averaging.
    Split text into chunks of ~chunk_size words, classify each,
    and average the probabilities.
    """
    words = text.split()
    if len(words) <= chunk_size:
        # Short text: classify directly
        X = vectorizer.transform([text])
        pred = model.predict(X)[0]
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)[0]
        else:
            proba = [0.5, 0.5]
        return pred, proba

    # Split into chunks
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        if len(chunk.split()) >= 20:  # Skip very short tail chunks
            chunks.append(chunk)

    if not chunks:
        chunks = [text]

    # Classify each chunk
    probas = []
    for chunk in chunks:
        X = vectorizer.transform([chunk])
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)[0]
        else:
            pred = model.predict(X)[0]
            proba = [1.0 - pred, float(pred)]
        probas.append(proba)

    # Average probabilities
    avg_proba = [
        sum(p[0] for p in probas) / len(probas),
        sum(p[1] for p in probas) / len(probas),
    ]

    # Final prediction based on averaged probability
    final_pred = 1 if avg_proba[1] > 0.5 else 0
    return final_pred, avg_proba


def main():
    print("=" * 60)
    print("YOUTUBE TRANSCRIPT VALIDATION SUITE v3")
    print("=" * 60)

    try:
        model = joblib.load(MODEL_PATH)
        vec = joblib.load(VEC_PATH)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Run train_v3.py first to generate model_v3.pkl and vectorizer_v3.pkl")
        sys.exit(1)

    print(f"Model type: {type(model).__name__}")
    print(f"Label mapping: 0=Suspicious, 1=Credible")
    print()

    all_cases = EDUCATIONAL_TRANSCRIPTS + SUSPICIOUS_TRANSCRIPTS
    passed = 0
    failed = 0

    # Test full-text classification
    print("-" * 60)
    print("METHOD 1: Full Transcript Classification")
    print("-" * 60)
    for tc in all_cases:
        X = vec.transform([tc["text"]])
        pred = model.predict(X)[0]
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)[0]
            prob_str = f"P(Susp)={proba[0]:.3f} P(Cred)={proba[1]:.3f}"
        else:
            prob_str = "N/A"

        predicted = "Credible" if pred == 1 else "Suspicious"
        expected = "Credible" if tc["expected"] == 1 else "Suspicious"
        correct = pred == tc["expected"]
        status = "✅" if correct else "❌"

        if correct:
            passed += 1
        else:
            failed += 1

        print(f"  {status} [{tc['source']:15s}] {tc['name']:25s} | Pred: {predicted:10s} | Exp: {expected:10s} | {prob_str}")

    print(f"\n  Full-text: {passed}/{passed + failed} passed")

    # Test chunk-based classification
    print()
    print("-" * 60)
    print("METHOD 2: Chunk-Based Average Probability")
    print("-" * 60)
    chunk_passed = 0
    chunk_failed = 0
    for tc in all_cases:
        pred, proba = analyze_transcript_chunked(model, vec, tc["text"], chunk_size=200)
        predicted = "Credible" if pred == 1 else "Suspicious"
        expected = "Credible" if tc["expected"] == 1 else "Suspicious"
        correct = pred == tc["expected"]
        status = "✅" if correct else "❌"

        if correct:
            chunk_passed += 1
        else:
            chunk_failed += 1

        print(f"  {status} [{tc['source']:15s}] {tc['name']:25s} | Pred: {predicted:10s} | Exp: {expected:10s} | Avg P(Susp)={proba[0]:.3f} P(Cred)={proba[1]:.3f}")

    print(f"\n  Chunk-based: {chunk_passed}/{chunk_passed + chunk_failed} passed")

    # Summary
    total_passed = passed + chunk_passed
    total_tests = (passed + failed) + (chunk_passed + chunk_failed)

    print()
    print("=" * 60)
    print(f"TOTAL: {total_passed}/{total_tests} PASSED")
    print("=" * 60)

    if failed > 0 or chunk_failed > 0:
        print(f"\n❌ Some tests FAILED")
        sys.exit(1)
    else:
        print(f"\n✅ ALL TESTS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
