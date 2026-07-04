"""
01_감정유도질문_프롬프트.md 를 실제 Gemini 2.5 Flash API에 태워
test_inputs.json의 10개 시나리오에 대해 자동 검증하는 스크립트.

seenears_ai_pipeline_README.md 기준, 이 프로젝트는 Gemini 2.5 Flash를 사용하므로
동일 모델로 실제 응답을 받아 검증한다.

사용법:
    export GEMINI_API_KEY="발급받은_키"
    pip install requests --break-system-packages   # 이미 있으면 생략
    python3 run_gemini_test.py

결과:
    - 콘솔에 케이스별 PASS/WARN/FAIL 출력
    - results.csv 에 상세 결과 저장 (다음 회귀 테스트와 비교 가능)
"""

import csv
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

from validator import validate_case

HERE = Path(__file__).parent
PROMPT_MD = HERE.parent / "01_감정유도질문_프롬프트.md"
TEST_INPUTS = HERE / "test_inputs.json"
RESULTS_CSV = HERE / "results.csv"

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
API_KEY = os.environ.get("GEMINI_API_KEY")

ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def extract_system_prompt(md_path: Path) -> str:
    """## SYSTEM PROMPT 코드블록만 뽑아온다."""
    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"## SYSTEM PROMPT\s*```\n(.*?)```", text, re.DOTALL)
    if not m:
        raise RuntimeError("SYSTEM PROMPT 코드블록을 md에서 찾지 못했습니다.")
    return m.group(1).strip()


def call_gemini(system_prompt: str, case: dict) -> dict:
    user_input = {
        "weather": case["weather"],
        "language": case["language"],
        "recent_context": case.get("recent_context", ""),
        "digital_grade": case.get("digital_grade"),
        "recent_questions": case.get("recent_questions", []),
    }
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [
            {"role": "user", "parts": [{"text": json.dumps(user_input, ensure_ascii=False)}]}
        ],
        "generationConfig": {"temperature": 0.9, "response_mime_type": "application/json"},
    }
    resp = requests.post(
        ENDPOINT,
        params={"key": API_KEY},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(raw_text)


def main():
    if not API_KEY:
        print("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("export GEMINI_API_KEY=\"발급받은_키\" 이후 다시 실행해 주세요.")
        sys.exit(1)

    system_prompt = extract_system_prompt(PROMPT_MD)
    cases = json.loads(TEST_INPUTS.read_text(encoding="utf-8"))

    rows = []
    summary = {"PASS": 0, "WARN": 0, "FAIL": 0, "ERROR": 0}

    for case in cases:
        print(f"\n[{case['id']}] {case['desc']}")
        try:
            output = call_gemini(system_prompt, case)
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR: API 호출/파싱 실패 - {e}")
            summary["ERROR"] += 1
            rows.append({**case, "question": "", "overall": "ERROR", "detail": str(e)})
            time.sleep(1)
            continue

        case_for_validation = {**case, "output": output}
        overall, results = validate_case(case_for_validation)
        summary[overall] += 1

        print(f"  question: {output.get('question')}")
        print(f"  판정: {overall}")
        for k, (status, detail) in results.items():
            if status != "PASS":
                print(f"    - {k}: {status} {detail}")

        rows.append({
            **case,
            "question": output.get("question"),
            "weather_tone": output.get("weather_tone"),
            "references_context": output.get("references_context"),
            "overall": overall,
            "detail": json.dumps(
                {k: v for k, (v, _) in results.items()}, ensure_ascii=False
            ),
        })
        time.sleep(1)  # 레이트리밋 여유

    with RESULTS_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("\n=== 요약 ===")
    for k, v in summary.items():
        print(f"{k}: {v}")
    print(f"\n상세 결과 저장: {RESULTS_CSV}")


if __name__ == "__main__":
    main()
