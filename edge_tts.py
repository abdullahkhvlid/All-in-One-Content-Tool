import requests
import os
import tempfile
from utils.config import get_tts_voice
from utils.logger import log_event

def synthesize_speech(text, output_path):
    url = "https://eastus.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": os.getenv("EDGE_TTS_KEY"),  # or use local browser API if available
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
        "User-Agent": "Mozilla/5.0"
    }
    ssml = f"""<speak version='1.0' xml:lang='en-US'><voice name='{get_tts_voice()}'>{text}</voice></speak>"""
    try:
        r = requests.post(url, headers=headers, data=ssml)
        r.raise_for_status()
        with open(output_path, "wb") as out:
            out.write(r.content)
        log_event("INFO", f"Synthesized speech to {output_path}", "edge_tts")
        return output_path
    except Exception as e:
        log_event("ERROR", f"TTS failed: {e}", "edge_tts")
        raise

if __name__ == '__main__':
    synthesize_speech("Hello, this is a test.", "sample.mp3")