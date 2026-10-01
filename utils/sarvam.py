"""
Sarvam AI integration — STT, Translate, TTS for Indian languages.
Docs: https://docs.sarvam.ai
"""
import requests
from config.settings import SARVAM_API_KEY

SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
SARVAM_TRANSLATE_URL = "https://api.sarvam.ai/translate"

# Languages supported by TTS (bulbul)
TTS_SUPPORTED = {
    "bn-IN", "en-IN", "gu-IN", "hi-IN", "kn-IN",
    "ml-IN", "mr-IN", "od-IN", "pa-IN", "ta-IN", "te-IN",
}

# Friendly language names for UI display
LANGUAGE_NAMES = {
    "hi-IN": "Hindi", "ta-IN": "Tamil", "te-IN": "Telugu",
    "kn-IN": "Kannada", "ml-IN": "Malayalam", "bn-IN": "Bengali",
    "gu-IN": "Gujarati", "mr-IN": "Marathi", "pa-IN": "Punjabi",
    "od-IN": "Odia", "en-IN": "English",
}


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    """
    Convert audio to text using Sarvam Saarika v2.5.
    Returns: { transcript, language_code, language_probability }
    """
    headers = {"api-subscription-key": SARVAM_API_KEY}

    # Determine mime type from filename
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "webm"
    mime_map = {
        "webm": "audio/webm", "wav": "audio/wav", "mp3": "audio/mpeg",
        "ogg": "audio/ogg", "m4a": "audio/mp4", "mp4": "audio/mp4",
        "flac": "audio/flac", "aac": "audio/aac",
    }
    mime = mime_map.get(ext, "audio/webm")

    files = {"file": (filename, audio_bytes, mime)}
    data = {"model": "saarika:v2.5"}  # auto-detect language (language_code omitted)

    resp = requests.post(SARVAM_STT_URL, headers=headers, files=files, data=data, timeout=30)
    resp.raise_for_status()
    return resp.json()


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translate text using Sarvam Mayura / sarvam-translate.
    Handles texts up to 2000 chars by chunking at sentence boundaries.
    """
    if source_lang == target_lang:
        return text

    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json",
    }

    # sarvam-translate:v1 supports all 22 languages, 2000 char limit
    model = "sarvam-translate:v1"
    max_chars = 1900

    if len(text) <= max_chars:
        chunks = [text]
    else:
        # Split at sentence boundaries
        import re
        sentences = re.split(r"(?<=[.!?\n])\s+", text)
        chunks, current = [], ""
        for s in sentences:
            if len(current) + len(s) < max_chars:
                current += s + " "
            else:
                if current:
                    chunks.append(current.strip())
                current = s + " "
        if current:
            chunks.append(current.strip())

    translated_parts = []
    for chunk in chunks:
        payload = {
            "input": chunk,
            "source_language_code": source_lang,
            "target_language_code": target_lang,
            "model": model,
        }
        resp = requests.post(SARVAM_TRANSLATE_URL, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        translated_parts.append(resp.json()["translated_text"])

    return " ".join(translated_parts)


def synthesize_speech(text: str, language_code: str) -> str:
    """
    Convert text to speech using Sarvam Bulbul v3.
    Returns base64-encoded MP3 string.
    """
    # Fall back to Hindi if language not supported for TTS
    if language_code not in TTS_SUPPORTED:
        language_code = "hi-IN"

    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json",
    }

    # Bulbul v3 max 2500 chars — truncate cleanly at word boundary
    if len(text) > 2400:
        text = text[:2400].rsplit(" ", 1)[0] + "…"

    payload = {
        "text": text,
        "target_language_code": language_code,
        "model": "bulbul:v3",
        "output_audio_codec": "mp3",
        "speech_sample_rate": "22050",
        "pace": 1.0,
    }

    resp = requests.post(SARVAM_TTS_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["audios"][0]  # base64 MP3
