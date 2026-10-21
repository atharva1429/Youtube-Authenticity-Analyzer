import traceback
from youtube_transcript_api import YouTubeTranscriptApi

for vid in ['aircAruvnKk', 'QEP_LNskNuU']:
    print(f"--- Testing {vid} ---")
    try:
        t_list = YouTubeTranscriptApi.list_transcripts(vid)
        print("Transcripts available:")
        for t in t_list:
            print(f" - {t.language} ({t.language_code}), generated: {t.is_generated}, translatable: {t.is_translatable}")
    except Exception as e:
        traceback.print_exc()
