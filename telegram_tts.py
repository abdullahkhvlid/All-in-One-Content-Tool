# Save this as telegram_tts.py
from gtts import gTTS
import sys

def text_to_speech(text, lang='hi'):  # Default: Hindi ('hi')
    tts = gTTS(text=text, lang=lang)
    tts.save("output.mp3")
    print(f"Audio saved as 'output.mp3'")

if __name__ == "__main__":
    user_text = sys.argv[1]  # Run: python telegram_tts.py "Your text"
    text_to_speech(user_text)