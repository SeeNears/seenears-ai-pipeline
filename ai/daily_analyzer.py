from google.genai import types
from pathlib import Path
from ai.gemini_client import client, GEMINI_MODEL, GEMINI_TEMPERATURE
import json

PROMPTS_DIR = Path(__file__).parent / "prompts"

WEATHER_MAP = {
    "sunny": "맑음(☀️)",
    "cloudy": "흐림(☁️)",
    "rainy": "비(☔)"
}

def _load_prompt(language: str, weather_korean: str) -> str:
    template = (PROMPTS_DIR / f"{language}.txt").read_text(encoding="utf-8")
    return template.replace("{weather_korean}", weather_korean)

def analyze_daily_voice(
    audio_file_path: str,
    weather: str,
    user_code: str,
    language: str = "ko"
) -> dict:
    audio_path = Path(audio_file_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"오디오 파일 없음: {audio_file_path}")

    weather_korean = WEATHER_MAP.get(weather, "흐림")
    prompt = _load_prompt(language, weather_korean)
    audio_file = client.files.upload(file=audio_path)

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[audio_file, prompt],
            config=types.GenerateContentConfig(
                temperature=GEMINI_TEMPERATURE,
                response_mime_type="application/json"
            )
        )
        result = json.loads(response.text)
        result["user_code"] = user_code
        result["weather"] = weather
        result["language"] = language
        return result
    finally:
        client.files.delete(name=audio_file.name)