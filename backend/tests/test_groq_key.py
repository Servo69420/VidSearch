import sys
import io
import httpx
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from app.config import settings


def test_groq_api_key():
    key = settings.GROQ_API_KEY
    assert key, "GROQ_API_KEY is not set in .env"

    r = httpx.get(
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {key}"},
    )
    assert r.status_code == 200, f"Models list failed (HTTP {r.status_code}): {r.text}"
    print(f"[OK] Chat/models — key is valid, {len(r.json()['data'])} models available")


def test_groq_audio_access():
    """Tests whether the account has Whisper/audio transcription access."""
    key = settings.GROQ_API_KEY
    assert key, "GROQ_API_KEY is not set in .env"

    # Minimal silent WAV: 44-byte header + 0 audio samples
    wav = (
        b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00"
        b"\x01\x00\x01\x00\x80\x3e\x00\x00\x00\x7d\x00\x00"
        b"\x02\x00\x10\x00data\x00\x00\x00\x00"
    )

    r = httpx.post(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {key}"},
        files={"file": ("test.wav", io.BytesIO(wav), "audio/wav")},
        data={"model": "whisper-large-v3-turbo"},
        timeout=30,
    )
    if r.status_code == 200:
        print("[OK] Audio transcription — account has Whisper access")
    elif r.status_code == 401:
        print(f"[FAIL] Audio API rejected the key — account may need phone/billing verification")
        print(f"       Response: {r.text}")
    else:
        print(f"[INFO] Audio API returned HTTP {r.status_code}: {r.text}")


if __name__ == "__main__":
    test_groq_api_key()
    test_groq_audio_access()
