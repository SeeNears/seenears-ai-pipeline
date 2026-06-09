from google import genai
from google.genai import types
import json
import os
from pathlib import Path
from ai.gemini_client import client, GEMINI_MODEL

def analyze_daily_voice(
    audio_file_path: str,
    weather: str,
    user_code: str,
    language: str = "ko"
) -> dict:
    """
    어르신 일일 음성 녹음을 분석하여 감정 점수와 위험도를 반환합니다.
    보안: user_code는 익명 코드만 사용, 실명 미포함
    """
    audio_path = Path(audio_file_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"오디오 파일 없음: {audio_file_path}")

    audio_file = client.files.upload(file=audio_path)

    weather_map = {
        "sunny": "맑음(☀️)",
        "cloudy": "흐림(☁️)",
        "rainy": "비(☔)"
    }
    weather_korean = weather_map.get(weather, "흐림")

    if language == "ko":
        prompt = f"""
당신은 노인 정신건강 전문 AI 분석가입니다.
다음 음성 녹음과 감정 날씨 정보를 분석해주세요.
[오늘의 감정 날씨]: {weather_korean}
반드시 아래 JSON 형식으로만 답하세요.
{{
  "transcription": "음성 전체 내용을 텍스트로 변환한 결과",
  "emotion_label": "positive 또는 negative 또는 neutral 중 하나",
  "emotion_score": 0.0에서 1.0 사이 소수,
  "final_score": 음성분석(60%)과 날씨선택(맑음=1.0/흐림=0.5/비=0.0)(40%) 결합한 최종점수,
  "risk_keywords": ["발견된 위험 키워드 목록, 없으면 빈 배열"],
  "risk_level": "CRITICAL 또는 HIGH 또는 MEDIUM 또는 NORMAL 중 하나",
  "risk_reason": "위험 판단 이유",
  "welfare_summary": "복지사를 위한 오늘 상태 한 줄 요약 (30자 이내)"
}}
"""
    else:
        prompt = f"""
あなたは高齢者のメンタルヘルス専門AIアナリストです。
以下の音声録音と感情天気情報を分析してください。
[今日の感情天気]: {weather_korean}
必ず以下のJSON形式のみで回答してください。
{{
  "transcription": "音声の文字起こし全文",
  "emotion_label": "positive または negative または neutral",
  "emotion_score": 0.0から1.0の小数,
  "final_score": 音声分析(60%)と天気選択(晴れ=1.0/曇り=0.5/雨=0.0)(40%)の複合スコア,
  "risk_keywords": ["検出されたリスクキーワード"],
  "risk_level": "CRITICAL または HIGH または MEDIUM または NORMAL",
  "risk_reason": "リスク判断の理由",
  "welfare_summary": "福祉担当者向け今日の状態一言要約"
}}
"""

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[audio_file, prompt],
            config=types.GenerateContentConfig(
                temperature=0.1,
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