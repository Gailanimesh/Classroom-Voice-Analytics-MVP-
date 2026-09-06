import os
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")  # small = good speed/accuracy balance for MVP on CPU
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "auto")
