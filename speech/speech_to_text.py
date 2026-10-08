import os
import re
import whisper
import streamlit as st
from utils.config_manager import load_config

# Domain prompt primes Whisper with relevant database & healthcare/e-commerce vocabulary
WHISPER_DOMAIN_PROMPT = (
    "Show all the doctors, list doctors, show patients, patient admissions, "
    "ICU admissions, hospital departments, treatment cost, medical billing, "
    "consultation fee, doctors list, products, orders, customers, employees, "
    "SQL query database."
)

KNOWN_HALLUCINATIONS = [
    "let's keep walking",
    "lets keep walking",
    "thank you for watching",
    "thanks for watching",
    "subtitles by",
    "please subscribe",
    "like and subscribe",
    "see you next time",
    "see you in the next video",
    "amara.org",
    "watching!",
    "bye.",
]

@st.cache_resource
def get_whisper_model(model_name: str = "base.en"):
    """Load and cache the OpenAI Whisper model to avoid blocking application startup."""
    return whisper.load_model(model_name)

def is_hallucination(text: str) -> bool:
    """Detect common Whisper hallucination artifacts generated on silence or faint noise."""
    cleaned = text.lower().strip().strip(".").strip("!").strip(",")
    if not cleaned:
        return True
    for phrase in KNOWN_HALLUCINATIONS:
        if cleaned == phrase or cleaned.startswith(phrase):
            return True
    return False

def speech_to_text(audio_file: str) -> str:
    """
    Transcribe audio file to text using Whisper with domain biasing and strict anti-hallucination settings.
    """
    if not os.path.exists(audio_file) or os.path.getsize(audio_file) < 500:
        return ""

    config = load_config()
    model_name = config.get("whisper_model", "base.en")
    
    try:
        model = get_whisper_model(model_name)
    except Exception:
        # Fallback to base.en or base
        try:
            model = get_whisper_model("base.en")
        except Exception:
            model = get_whisper_model("base")

    try:
        result = model.transcribe(
            audio_file,
            language="en",
            temperature=0.0,
            initial_prompt=WHISPER_DOMAIN_PROMPT,
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
            fp16=False,
        )
        text = result.get("text", "").strip()

        # Check for hallucinations on ambient noise
        if is_hallucination(text):
            return ""

        return text
    except Exception as e:
        print(f"Speech recognition error: {e}")
        return ""