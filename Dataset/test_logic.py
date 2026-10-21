import traceback
from youtube_transcript_api import YouTubeTranscriptApi

for vid in ['aircAruvnKk', 'QEP_LNskNuU']:
    print(f"--- Testing {vid} ---")
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(vid)
        
        available_langs = [t.language_code for t in transcript_list]
        print(f"[YOUTUBE] Available languages: {available_langs}")
        
        transcript_obj = None

        # a. English manual
        if not transcript_obj:
            for t in transcript_list:
                if 'en' in t.language_code.lower() and not t.is_generated:
                    transcript_obj = t
                    break
        
        # b. English generated
        if not transcript_obj:
            for t in transcript_list:
                if 'en' in t.language_code.lower() and t.is_generated:
                    transcript_obj = t
                    break
                    
        # c. Hindi manual
        if not transcript_obj:
            for t in transcript_list:
                if 'hi' in t.language_code.lower() and not t.is_generated:
                    transcript_obj = t
                    break
                    
        # d. Hindi generated
        if not transcript_obj:
            for t in transcript_list:
                if 'hi' in t.language_code.lower() and t.is_generated:
                    transcript_obj = t
                    break
                    
        # e. any available transcript
        if not transcript_obj:
            try:
                transcript_obj = next(iter(transcript_list))
            except StopIteration:
                raise Exception("No transcripts available")

        selected_lang = transcript_obj.language_code
        print(f"[YOUTUBE] Selected language: {selected_lang}")
        print(f"[YOUTUBE] Transcript type: {'Generated' if transcript_obj.is_generated else 'Manual'}")
        
        # f. translate to English if translation is supported
        translation_applied = False
        if selected_lang != 'en' and transcript_obj.is_translatable:
            transcript_obj = transcript_obj.translate('en')
            translation_applied = True
            
        print(f"[YOUTUBE] Translation: {'Yes (to en)' if translation_applied else 'No'}")

        detected_language = selected_lang
        fetched = transcript_obj.fetch()
        translated_text = " ".join([item['text'] for item in fetched]).strip()
        print(f"Success! Translated text starts with: {translated_text[:50]}")
    except Exception as e:
        traceback.print_exc()
