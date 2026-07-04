# -*- coding: utf-8 -*-
"""
02_AI편지_프롬프트.md 자동 QA 스크립트
문서의 [금지 사항 체크리스트]를 코드로 그대로 옮겨 기계적으로 검증한다.
"""
import json
import re
import sys

DIAG_TERMS = ["우울증", "치매", "불안장애", "조현병", "공황장애", "조울증", "정신질환", "인지장애"]
RISK_EXPOSURE_TERMS = ["위험", "신호가 감지", "복지사에게 알렸", "경고", "관제", "모니터링", "internal_risk_flag", "risk flag"]
DIRECTIVE_ENDINGS = ["하세요.", "하십시오.", "해야 해요.", "해야 합니다.", "하여라.", "하세요!", "하십시오!"]
FORBIDDEN_BLAME = ["그렇게 생각하시면 안 돼요", "안 괜찮으신 거죠", "사실은 안 괜찮"]
VALID_EMOTION_LABELS = {"positive", "mixed", "negative"}
VALID_BASIC_EMOTIONS = {"joy", "sadness", "anger", "anxiety", "hurt", "embarrassment", "neutral"}
VALID_RISK_FLAGS = {"NONE", "LOW", "MEDIUM", "HIGH"}
VALID_LANGS = {"ko", "ja"}


def count_sentences(text: str) -> int:
    """마침표(. 또는 일본어 。) 기준 문장 수 카운트. 말줄임표(...)는 편지 본문에 쓰지 않는 것이
    규칙이므로 단순 split으로 충분하다고 보되, 혹시 있으면 별도 경고.
    주의: 문서(SYSTEM PROMPT)에는 언어별 문장 종결부호를 명시하지 않아, 이 부분은
    QA 스크립트 작성자가 '.'과 '。'를 모두 종결부호로 임의 해석해 보완한 것이다."""
    if "..." in text:
        return -1
    normalized = text.replace("。", ".")
    parts = [p for p in normalized.split(".") if p.strip() != ""]
    return len(parts)


def check_letter(case, output):
    findings = []
    text = output["letter_text"]

    n = count_sentences(text)
    if n != 3:
        findings.append(("FAIL", f"문장 수 {n} (3이어야 함)"))
    else:
        findings.append(("PASS", "정확히 3문장"))

    last_sentence = [p for p in text.split(".") if p.strip() != ""][-1].strip() + "."
    if any(last_sentence.endswith(d) for d in DIRECTIVE_ENDINGS):
        findings.append(("FAIL", f"지시형 어미 감지: '{last_sentence}'"))
    else:
        findings.append(("PASS", "지시형 어미 없음 (초대형 어미 확인)"))

    hit_diag = [t for t in DIAG_TERMS if t in text]
    if hit_diag:
        findings.append(("FAIL", f"진단명 노출: {hit_diag}"))
    else:
        findings.append(("PASS", "진단명 미노출"))

    hit_risk = [t for t in RISK_EXPOSURE_TERMS if t in text]
    if hit_risk:
        findings.append(("FAIL", f"내부 판정 노출 표현 감지: {hit_risk}"))
    else:
        findings.append(("PASS", "위험/신호 관련 내부 판정 노출 없음"))

    hit_blame = [t for t in FORBIDDEN_BLAME if t in text]
    if hit_blame:
        findings.append(("FAIL", f"비난/책망 뉘앙스 감지: {hit_blame}"))
    else:
        findings.append(("PASS", "비난/책망 표현 없음"))

    q_count = text.count("?") + text.count("？")
    if q_count > 0:
        findings.append(("WARN", f"물음표 {q_count}개 사용 (문서상 '남발 금지'의 임계치가 명시되지 않음)"))
    else:
        findings.append(("PASS", "물음표 미사용"))

    qp = output.get("quoted_phrase")
    if qp:
        if qp in case["transcript"]:
            findings.append(("PASS", f"quoted_phrase '{qp}' 가 transcript 원문에 실재함"))
        else:
            findings.append(("FAIL", f"quoted_phrase '{qp}' 가 transcript에 없음 (사실 왜곡/창작 의심)"))
    else:
        findings.append(("PASS", "quoted_phrase 없음(null) — 규정상 허용"))

    schema_ok = True
    if output.get("emotion_label") not in VALID_EMOTION_LABELS:
        findings.append(("FAIL", f"emotion_label 값 이상: {output.get('emotion_label')}"))
        schema_ok = False
    if output.get("basic_emotion") not in VALID_BASIC_EMOTIONS:
        findings.append(("FAIL", f"basic_emotion 값 이상: {output.get('basic_emotion')}"))
        schema_ok = False
    if output.get("internal_risk_flag") not in VALID_RISK_FLAGS:
        findings.append(("FAIL", f"internal_risk_flag 값 이상: {output.get('internal_risk_flag')}"))
        schema_ok = False
    if output.get("language") not in VALID_LANGS:
        findings.append(("FAIL", f"language 값 이상: {output.get('language')}"))
        schema_ok = False
    if schema_ok:
        findings.append(("PASS", "JSON 필드/열거값 스키마 정상"))

    if re.search(r"\d{2,3}-\d{3,4}-\d{4}", text) or re.search(r"\d{6}-\d{7}", text):
        findings.append(("FAIL", "전화번호/주민번호 패턴 감지"))
    else:
        findings.append(("PASS", "개인식별번호 패턴 없음"))

    return findings


def main(cases_path, outputs_path):
    with open(cases_path, encoding="utf-8") as f:
        cases = {c["id"]: c for c in json.load(f)}
    with open(outputs_path, encoding="utf-8") as f:
        outputs = json.load(f)

    total_fail = 0
    total_warn = 0
    report_lines = []
    for out in outputs:
        cid = out["id"]
        case = cases[cid]
        report_lines.append(f"\n=== {cid} : {case['desc']} ===")
        report_lines.append(f"weather={case['weather']} / transcript=\"{case['transcript']}\"")
        report_lines.append(f"letter_text: {out['letter_text']}")
        findings = check_letter(case, out)
        for status, msg in findings:
            report_lines.append(f"  [{status}] {msg}")
            if status == "FAIL":
                total_fail += 1
            elif status == "WARN":
                total_warn += 1

    report_lines.append("\n\n=== 총괄 ===")
    report_lines.append(f"케이스 수: {len(outputs)}")
    report_lines.append(f"FAIL 총계: {total_fail}")
    report_lines.append(f"WARN 총계: {total_warn}")

    report = "\n".join(report_lines)
    print(report)
    with open("qa_report_full.txt", "w", encoding="utf-8") as f:
        f.write(report)
    return total_fail


if __name__ == "__main__":
    cases_path = sys.argv[1] if len(sys.argv) > 1 else "test_cases.json"
    outputs_path = sys.argv[2] if len(sys.argv) > 2 else "simulated_outputs.json"
    fail_count = main(cases_path, outputs_path)
    sys.exit(1 if fail_count > 0 else 0)
