import json
import re
import urllib.parse
import urllib.request
import time

from youtube_transcript_api import YouTubeTranscriptApi
from backend.ml_service import analyze_text, analyze_transcript

# Local in-memory transcript cache to survive YouTube IP rate-limits
TRANSCRIPT_CACHE: dict[str, dict] = {}


def clean_youtube_transcript(text: str) -> str:
    """Safe, non-destructive transcript cleaner that strips sound cues,
    timestamps, URLs, and platform boilerplate without removing valid spoken content."""
    if not isinstance(text, str) or not text:
        return ""

    # 1. Bracketed sound effects and audio cues only
    text = re.sub(
        r'\[(?:Music|Applause|Laughter|Cheering|Noise|Inaudible|Video|Audio|Screaming|Groan|Chuckles|Silence|Static|\s*)+\]',
        ' ', text, flags=re.IGNORECASE
    )

    # 2. Timestamps (e.g., "00:15", "01:23:45", "12:34")
    text = re.sub(r'\b\d{1,2}:\d{2}(?::\d{2})?\b', ' ', text)

    # 3. URLs and HTML tags
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
    text = re.sub(r'<[^>]+>', ' ', text)

    # 4. YouTube platform boilerplate and calls to action
    fillers = [
        r"\bsubscribe\s+to\s+(?:the|my)?\s*channel\b",
        r"\blike\s+and\s+subscribe\b",
        r"\bhit\s+the\s+bell\b",
        r"\bthanks\s+for\s+watching\b",
        r"\bleave\s+a\s+comment\b",
        r"\blink\s+in\s+the\s+description\b"
    ]
    for filler in fillers:
        text = re.sub(filler, ' ', text, flags=re.IGNORECASE)

    # 5. Normalize whitespace
    text = text.replace('\xa0', ' ').replace('\ufffd', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def fetch_video_title(url: str) -> str | None:
    try:
        oembed_url = (
            "https://www.youtube.com/oembed?"
            f"url={urllib.parse.quote(url, safe='')}&format=json"
        )
        with urllib.request.urlopen(oembed_url, timeout=6) as response:
            data = json.loads(response.read().decode())
            return data.get("title")
    except Exception:
        return None


def extract_video_id(url: str) -> str:
    url = url.strip()
    if "v=" in url:
        return url.split("v=")[1].split("&")[0].split("#")[0]
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0].split("#")[0]
    if "/embed/" in url:
        return url.split("/embed/")[1].split("?")[0].split("#")[0]
    if "/shorts/" in url:
        return url.split("/shorts/")[1].split("?")[0].split("#")[0]
    
    # Try regex fallback for 11-char YouTube ID
    match = re.search(r"([a-zA-Z0-9_-]{11})", url)
    if match:
        return match.group(1)
        
    raise ValueError("Invalid YouTube URL")


def is_english_code(code: str) -> bool:
    """Check if a language code represents an English dialect."""
    if not code or not isinstance(code, str):
        return False
    c = code.lower().strip()
    return c == 'en' or c.startswith('en-') or c.startswith('en_')


def is_ip_rate_limited(exc: Exception) -> bool:
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    return "ipblocked" in name or "ipblocked" in text or "toomanyrequests" in name or "429" in text


def extract_transcript_text(fetched) -> str:
    """Safely extract plain text from FetchedTranscript dataclasses or legacy dicts."""
    if not fetched:
        return ""
    parts = []
    for item in fetched:
        if hasattr(item, 'text'):
            parts.append(str(item.text))
        elif isinstance(item, dict) and 'text' in item:
            parts.append(str(item['text']))
        elif isinstance(item, str):
            parts.append(item)
    return " ".join(parts).strip()


def get_cached_transcript_from_db(video_id: str) -> str | None:
    """Look up previously saved transcript from the SQLite database."""
    try:
        import sqlite3
        from pathlib import Path
        db_path = Path(__file__).resolve().parent.parent / "app.db"
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            row = cur.execute(
                "SELECT full_content FROM analysis_history WHERE youtube_url LIKE ? AND full_content IS NOT NULL ORDER BY id DESC LIMIT 1",
                (f"%{video_id}%",)
            ).fetchone()
            conn.close()
            if row and row[0]:
                return row[0]
    except Exception as dbe:
        print(f"[DEBUG] DB cache lookup failed: {dbe}")
    return None


def fetch_transcript_chain(video_id: str) -> tuple[str, str, str, bool, str | None]:
    """
    Robust fallback chain in exact priority order:
    1. English transcript (manually created)
    2. Generated English transcript
    3. Any available transcript
    4. Translate to English (if translatable, translate and fetch)
    5. Return detailed reason if unavailable

    Returns:
        (text, detected_language, transcript_type, is_translated, failure_cause)
    """
    # 0. Check in-memory cache first to avoid unneeded external calls
    if video_id in TRANSCRIPT_CACHE:
        cached = TRANSCRIPT_CACHE[video_id]
        print(f"[YOUTUBE] [OK] Cache hit: In-memory transcript found for {video_id}")
        return cached["text"], cached.get("detected_language", "en"), "cached", False, None

    failure_log = []
    ytt_api = YouTubeTranscriptApi()
    transcript_list = None
    list_err_msg = None

    # Step 0: Fetch available transcript metadata via YouTubeTranscriptApi
    try:
        transcript_list = ytt_api.list(video_id)
    except AttributeError:
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        except Exception as e:
            list_err_msg = f"{type(e).__name__}: {e}"
    except Exception as e:
        list_err_msg = f"{type(e).__name__}: {e}"

    transcripts = []
    if transcript_list:
        try:
            transcripts = list(transcript_list)
        except Exception as e:
            list_err_msg = f"Iteration error: {e}"

    if list_err_msg:
        failure_log.append(f"List API: {list_err_msg}")
        print(f"[YOUTUBE] Transcript list retrieval notice: {list_err_msg}")

    if transcripts:
        available_codes = [
            f"{t.language_code}{' (gen)' if getattr(t, 'is_generated', False) else ''}"
            for t in transcripts
        ]
        print(f"[YOUTUBE] Available transcripts ({len(transcripts)}): {available_codes}")

        # Partition transcripts into categorized lists
        manual_english = [
            t for t in transcripts
            if is_english_code(t.language_code) and not getattr(t, 'is_generated', False)
        ]
        manual_english.sort(key=lambda t: 0 if t.language_code.lower() == 'en' else 1)

        generated_english = [
            t for t in transcripts
            if is_english_code(t.language_code) and getattr(t, 'is_generated', False)
        ]
        generated_english.sort(key=lambda t: 0 if t.language_code.lower() == 'en' else 1)

        other_transcripts = [
            t for t in transcripts
            if not is_english_code(t.language_code)
        ]
        other_transcripts.sort(key=lambda t: 1 if getattr(t, 'is_generated', False) else 0)

        # -------------------------------------------------------------------
        # ATTEMPT 1: English transcript (manually created)
        # -------------------------------------------------------------------
        if manual_english:
            print(f"[YOUTUBE] [Step 1] Attempting manually created English transcript ({len(manual_english)} candidate(s))...")
            for t in manual_english:
                try:
                    fetched = t.fetch()
                    text = extract_transcript_text(fetched)
                    if text:
                        print(f"[YOUTUBE] [Step 1 SUCCESS] Retrieved manual English transcript ({t.language_code})")
                        return text, t.language_code, "manual", False, None
                except Exception as e:
                    cause = f"Manual English ({t.language_code}) fetch failed: {type(e).__name__}: {e}"
                    print(f"[YOUTUBE] [Step 1 FAILED] {cause}")
                    failure_log.append(cause)
                    if is_ip_rate_limited(e):
                        print("[YOUTUBE] Rate limit encountered, checking cache/DB...")
                        db_t = get_cached_transcript_from_db(video_id)
                        if db_t:
                            print(f"[YOUTUBE] [OK] Cache hit: Database transcript found for {video_id}")
                            return db_t, "en", "db_cached", False, None
                        break
        else:
            print("[YOUTUBE] [Step 1] No manually created English transcript available.")

        # -------------------------------------------------------------------
        # ATTEMPT 2: Generated English transcript
        # -------------------------------------------------------------------
        if generated_english:
            print(f"[YOUTUBE] [Step 2] Attempting generated English transcript ({len(generated_english)} candidate(s))...")
            for t in generated_english:
                try:
                    fetched = t.fetch()
                    text = extract_transcript_text(fetched)
                    if text:
                        print(f"[YOUTUBE] [Step 2 SUCCESS] Retrieved generated English transcript ({t.language_code})")
                        return text, t.language_code, "generated", False, None
                except Exception as e:
                    cause = f"Generated English ({t.language_code}) fetch failed: {type(e).__name__}: {e}"
                    print(f"[YOUTUBE] [Step 2 FAILED] {cause}")
                    failure_log.append(cause)
                    if is_ip_rate_limited(e):
                        print("[YOUTUBE] Rate limit encountered, checking cache/DB...")
                        db_t = get_cached_transcript_from_db(video_id)
                        if db_t:
                            print(f"[YOUTUBE] [OK] Cache hit: Database transcript found for {video_id}")
                            return db_t, "en", "db_cached", False, None
                        break
        else:
            print("[YOUTUBE] [Step 2] No generated English transcript available.")

        # -------------------------------------------------------------------
        # ATTEMPT 3 & 4: Any available transcript + Translate to English
        # -------------------------------------------------------------------
        if other_transcripts:
            print(f"[YOUTUBE] [Steps 3 & 4] Attempting other available transcripts ({len(other_transcripts)} candidate(s))...")
            
            # Step 4: First attempt to translate to English if supported
            rate_limited = False
            for t in other_transcripts:
                if rate_limited:
                    break
                is_translatable = getattr(t, 'is_translatable', False)
                lang = t.language_code
                t_type = "generated" if getattr(t, 'is_generated', False) else "manual"

                if is_translatable:
                    try:
                        print(f"[YOUTUBE] [Step 4] Translating {lang} ({t_type}) to English...")
                        translated_obj = t.translate('en')
                        fetched = translated_obj.fetch()
                        text = extract_transcript_text(fetched)
                        if text:
                            print(f"[YOUTUBE] [Step 4 SUCCESS] Successfully translated {lang} transcript to English")
                            return text, lang, t_type, True, None
                    except Exception as e:
                        cause = f"Translation ({lang} -> en) failed: {type(e).__name__}: {e}"
                        print(f"[YOUTUBE] [Step 4 FAILED] {cause}")
                        failure_log.append(cause)
                        if is_ip_rate_limited(e):
                            rate_limited = True
                            break

            # Step 3: Fetch in native language if translation failed or was not translatable
            if not rate_limited:
                for t in other_transcripts:
                    lang = t.language_code
                    t_type = "generated" if getattr(t, 'is_generated', False) else "manual"
                    try:
                        print(f"[YOUTUBE] [Step 3] Fetching native transcript in {lang} ({t_type})...")
                        fetched = t.fetch()
                        text = extract_transcript_text(fetched)
                        if text:
                            print(f"[YOUTUBE] [Step 3 SUCCESS] Retrieved native transcript in {lang}")
                            return text, lang, t_type, False, None
                    except Exception as e:
                        cause = f"Native fetch ({lang}) failed: {type(e).__name__}: {e}"
                        print(f"[YOUTUBE] [Step 3 FAILED] {cause}")
                        failure_log.append(cause)
                        if is_ip_rate_limited(e):
                            break
        else:
            print("[YOUTUBE] [Steps 3 & 4] No other language transcripts available.")

    # Direct fetch fallback in case list metadata failed but direct track retrieval works
    try:
        print("[YOUTUBE] Attempting direct fetch fallback via API...")
        direct = ytt_api.fetch(video_id, languages=['en'])
        text = extract_transcript_text(direct)
        if text:
            print("[YOUTUBE] [OK] Direct fetch fallback succeeded")
            return text, "en", "direct", False, None
    except Exception as d_err:
        failure_log.append(f"Direct API fetch: {type(d_err).__name__}: {d_err}")

    # Check database history cache
    db_text = get_cached_transcript_from_db(video_id)
    if db_text:
        print(f"[YOUTUBE] [OK] Cache hit: Database transcript found for {video_id}")
        return db_text, "en", "db_cached", False, None

    # -------------------------------------------------------------------
    # ATTEMPT 5: Return detailed reason if unavailable
    # -------------------------------------------------------------------
    detailed_cause = " | ".join(failure_log) if failure_log else (list_err_msg or "No captions available for this video.")
    print(f"[YOUTUBE] [Step 5] Transcript unavailable for {video_id}. Detailed cause: {detailed_cause}")
    return "", "", "", False, detailed_cause


_WHISPER_MODEL = None


def get_whisper_model():
    """Lazily load and cache the faster-whisper model on CPU int8 (loaded once and reused)."""
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        from faster_whisper import WhisperModel
        _WHISPER_MODEL = WhisperModel(
            "tiny.en",
            device="cpu",
            compute_type="int8"
        )
        print("[WHISPER] Model Loaded")
    return _WHISPER_MODEL


def clean_whisper_transcript(text: str) -> str:
    """Whisper transcript normalizer:
    1. Remove repeated consecutive words ('the the the earth' -> 'the earth')
    2. Remove repeated short phrases ('thank you thank you thank you' -> 'thank you')
    3. Remove transcription artifacts: [Music], (background music), (sound effects), etc.
    4. Collapse excessive whitespace
    5. Preserve actual content words (scientific/educational/technical terms intact)
    """
    if not isinstance(text, str) or not text:
        return ""

    # 1. Remove transcription artifacts: [Music], (background music), (sound effects), etc.
    text = re.sub(
        r'\[(?:Music|Applause|Laughter|Cheering|Noise|Inaudible|Video|Audio|Screaming|Groan|Chuckles|Silence|Static|\s*)+\]',
        ' ', text, flags=re.IGNORECASE
    )
    text = re.sub(
        r'\((?:Music|Applause|Laughter|Cheering|Noise|Inaudible|Video|Audio|Screaming|Groan|Chuckles|Silence|Static|background music|sound effects|\s*)+\)',
        ' ', text, flags=re.IGNORECASE
    )

    # 2. Remove repeated consecutive words (e.g., 'the the the earth' -> 'the earth')
    text = re.sub(r'\b([a-zA-Z0-9_\'\-]+)(?:\s+\1\b)+', r'\1', text, flags=re.IGNORECASE)

    # 3. Remove repeated short phrases (2 to 6 words) (e.g., 'thank you thank you thank you' -> 'thank you')
    for _ in range(3):
        text = re.sub(r'\b((?:[a-zA-Z0-9_\'\-]+\s+){1,5}[a-zA-Z0-9_\'\-]+)(?:\s+\1\b)+', r'\1', text, flags=re.IGNORECASE)

    # 4. Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def transcribe_with_whisper(url: str, video_id: str) -> tuple[str, str]:
    """Download audio and transcribe using faster-whisper as a fallback without truncating audio."""
    import tempfile
    import os
    import yt_dlp

    print("[YT] Download Started")
    with tempfile.TemporaryDirectory() as tmpdir:
        out_tmpl = os.path.join(tmpdir, "audio.%(ext)s")
        ydl_opts = {
            "format": "ba/b",
            "outtmpl": out_tmpl,
            "extractor_args": {
                "youtube": {
                    "player_client": ["mweb", "android", "ios"]
                }
            },
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 30,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as dl_err:
            print(f"[YT] Download Failed: {dl_err}")
            raise RuntimeError(f"Audio download failed: {dl_err}")

        files = os.listdir(tmpdir)
        if not files:
            print("[YT] Download Failed: No audio file was created")
            raise RuntimeError("Audio download produced no files for Whisper transcription.")

        print("[YT] Download Finished")
        audio_path = os.path.join(tmpdir, files[0])

        try:
            model = get_whisper_model()
            print("[WHISPER] Transcription Started")
            segments, info = model.transcribe(audio_path, beam_size=1)
            raw_text = " ".join([seg.text for seg in segments]).strip()
            print("[WHISPER] Transcription Finished")
            detected_lang = getattr(info, "language", "en") or "en"
            return raw_text, detected_lang
        except Exception as tx_err:
            print(f"[WHISPER] Transcription Failed: {tx_err}")
            raise RuntimeError(f"Whisper transcription failed: {tx_err}")


def analyze_youtube(url: str) -> dict:
    start_time = time.time()
    video_id = extract_video_id(url)
    
    print(f"[YOUTUBE] Video ID: {video_id}")
    print("[YOUTUBE] Transcript API started")
    
    text, detected_language, transcript_type, is_translated, failure_cause = fetch_transcript_chain(video_id)
    
    # Automatic Whisper fallback if Transcript API returned no usable captions
    if not text or not text.strip():
        print(f"[YOUTUBE] Primary Transcript API unavailable ({failure_cause}). Triggering Whisper fallback...")
        try:
            whisper_text, whisper_lang = transcribe_with_whisper(url, video_id)
            if whisper_text and whisper_text.strip():
                text = whisper_text
                detected_language = whisper_lang
                transcript_type = "whisper"
                is_translated = False
                print(f"[WHISPER] [OK] Successfully transcribed audio via Whisper ({len(text.split())} words)")
        except Exception as wex:
            print(f"[WHISPER] Whisper fallback failed: {wex}")
            raise RuntimeError(f"Whisper fallback failed: {wex}")

    if not text or not text.strip():
        error_msg = failure_cause or "No transcript could be retrieved."
        print(f"[YOUTUBE] Analysis halted: {error_msg}")
        raise RuntimeError(error_msg)

    # Save to memory cache
    TRANSCRIPT_CACHE[video_id] = {
        "text": text,
        "detected_language": detected_language,
        "transcript_type": transcript_type,
        "is_translated": is_translated,
    }

    word_count = len(text.split())
    fetch_time = time.time() - start_time
    print(f"[YOUTUBE] Transcript successfully retrieved in: {fetch_time:.2f} seconds ({word_count} words)")
    print(f"[YOUTUBE] Language: {detected_language} | Type: {transcript_type} | Translated: {is_translated}")

    print("[YOUTUBE] ML prediction started")
    ml_start_time = time.time()

    # Normalize Whisper output through whisper cleanup then YouTube cleaner
    if transcript_type == "whisper":
        cleaned_text = clean_whisper_transcript(text)
        cleaned_text = clean_youtube_transcript(cleaned_text)
    else:
        cleaned_text = clean_youtube_transcript(text)

    if not cleaned_text.strip():
        cleaned_text = text

    analysis = analyze_transcript(cleaned_text)

    ml_time = time.time() - ml_start_time
    print(f"[YOUTUBE] ML prediction completed in: {ml_time:.2f} seconds")
    
    total_time = time.time() - start_time
    print(f"[TOTAL TIME] {total_time:.2f} seconds")

    return {
        **analysis,
        "transcript_status": "available",
        "transcript_length": word_count,
        "youtube_url": url,
        "video_id": video_id,
        "video_title": fetch_video_title(url),
        "transcript_text": text,
        "translated_text": text,
        "detected_language": detected_language,
    }


def classify_youtube_error(error_text: str) -> dict:
    lowered = error_text.lower()
    
    if "invalid" in lowered or "video id" in lowered:
        return {
            "transcript_status": "invalid",
            "error_message": "Invalid YouTube URL",
            "error_detail": "Please provide a valid YouTube watch URL containing 'v='.",
            "error_type": "invalid",
        }
        
    if "ipblocked" in lowered or "too many requests" in lowered or "429" in lowered:
        return {
            "transcript_status": "blocked",
            "error_message": "YouTube IP Blocked",
            "error_detail": "YouTube is currently rate-limiting or blocking transcript requests. Please try again later.",
            "error_type": "rate_limit",
        }

    if "disabled" in lowered or "transcriptsdisabled" in lowered or "subtitles are disabled" in lowered:
        return {
            "transcript_status": "disabled",
            "error_message": "Transcripts Disabled",
            "error_detail": "Subtitles/transcripts have been disabled by the creator for this video.",
            "error_type": "disabled",
        }

    if "videounavailable" in lowered or "no longer available" in lowered or "private video" in lowered:
        return {
            "transcript_status": "removed",
            "error_message": "Video Unavailable",
            "error_detail": "This video is unavailable, private, or has been removed from YouTube.",
            "error_type": "removed",
        }

    clean_cause = error_text.strip()
    if clean_cause.startswith("RuntimeError:"):
        clean_cause = clean_cause[len("RuntimeError:"):].strip()
    if clean_cause.startswith("Transcript unavailable:"):
        clean_cause = clean_cause[len("Transcript unavailable:"):].strip()

    return {
        "transcript_status": "unavailable",
        "error_message": "Transcript Not Available",
        "error_detail": clean_cause if clean_cause else "Could not retrieve captions for this YouTube video. Please use a video with captions enabled.",
        "error_type": "failed",
    }
