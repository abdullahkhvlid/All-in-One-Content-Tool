import os
from dotenv import load_dotenv

load_dotenv()

def get_db_url():
    return os.getenv('DATABASE_URL')

def get_replicate_token():
    return os.getenv('REPLICATE_API_TOKEN')

def get_tts_voice():
    return os.getenv('EDGE_TTS_VOICE', 'en-US-AriaNeural')

def get_n8n_url():
    return os.getenv('N8N_WEBHOOK_URL')