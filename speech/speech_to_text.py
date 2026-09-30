import whisper
import streamlit as st

@st.cache_resource
def get_whisper_model():
    """Load and cache the OpenAI Whisper model to avoid blocking application startup."""
    return whisper.load_model("base")

def speech_to_text(audio_file):
    """Transcribe cleaned audio file to text using Whisper."""
    model = get_whisper_model()
    result = model.transcribe(audio_file)
    return result["text"].strip()