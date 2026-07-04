# 01_감정유도질문_프롬프트 / 02_AI편지_프롬프트 테스트 도구

이 폴더에는 두 프롬프트의 테스트 도구가 함께 있다. 파일명 충돌을 피하기 위해
02_AI편지 쪽 파일은 모두 `02_AI편지_` 접두사를 붙였다 (`test_cases.json` 등
접두사 없는 파일은 전부 01_감정유도질문용).

## 01_감정유도질문_프롬프트 테스트 도구

- `test_inputs.json` — 10개 테스트 시나리오 **입력값만** (weather/맥락/등급/최근질문/언어 조합). `run_gemini_test.py`가 실제 API 호출 시 사용.
- `test_cases.json` — 위 10개 시나리오 + 시뮬레이션에서 생성한 `output.question` 포함. `python3 validator.py` 단독 실행 시 이 파일을 읽어 즉시 재검증 가능(재현성 확보용, API 키 불필요).
- `validator.py` — 금지사항 체크리스트 + 핵심원칙을 코드로 옮긴 자동 채점기 (단독 실행 시 `test_cases.json` 대상, `run_gemini_test.py`에서는 모듈로 import되어 재사용됨)
- `run_gemini_test.py` — 실제 Gemini 2.5 Flash API에 프롬프트를 태워 응답을 받고 자동 채점

## 실행 방법

**시뮬레이션 결과 재검증 (API 키 불필요, 지금 바로 실행 가능)**
```bash
python3 validator.py
```
→ TC1~TC10 판정 재현: 9 PASS / 1 WARN(TC7, 경미) — 확인 완료(2026-07-04).

**실제 Gemini API 회귀 테스트**
```bash
export GEMINI_API_KEY="발급받은_키"
pip install requests --break-system-packages
python3 run_gemini_test.py
```

결과는 콘솔 출력 + `results.csv`로 저장된다. 프롬프트를 수정할 때마다 다시 돌려서 이전 `results.csv`와 비교하면 회귀 여부를 확인할 수 있다.

자세한 시뮬레이션 테스트 해석은 상위 폴더의 `01_감정유도질문_테스트결과.md` 참고.

---

## 02_AI편지_프롬프트 테스트 도구

- `02_AI편지_test_cases.json` — 10개 테스트 시나리오 입력값 (weather/transcript/language/recent_letters_summary)
- `02_AI편지_simulated_outputs.json` — 위 시나리오에 대한 시뮬레이션 편지(letter_text) + JSON 출력
- `02_AI편지_checker.py` — 문서의 [금지 사항 체크리스트] 9개 항목을 코드로 옮긴 자동 채점기

```bash
python3 02_AI편지_checker.py 02_AI편지_test_cases.json 02_AI편지_simulated_outputs.json
```

결과 해석은 상위 폴더의 `02_AI편지_테스트결과.md` 참고 (10/10 PASS, 개선 제안 5건).
실제 API 회귀 테스트 스크립트(`run_gemini_test.py`에 대응하는 버전)는 아직 없음 — 필요 시 추가 제작 가능.
