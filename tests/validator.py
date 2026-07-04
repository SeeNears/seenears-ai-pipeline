import json, re, difflib

FORBIDDEN = ["왜", "무엇 때문에", "뭐 때문에", "걱정되", "걱정 있", "무슨 걱정",
             "우울", "불안하신가", "위험", "자살", "죽고 싶", "죽고싶",
             "고독사", "치매", "인지저하", "진단", "정신과", "상담사", "복지사"]

WH_WORDS = ["언제", "무엇", "뭐", "어떤", "어떻게", "누구", "얼마나", "무슨", "어디"]

CLOSED_PATTERNS = [
    r"있으세요\?*$", r"없으세요\?*$", r"괜찮으세요\?*$", r"이었나요\?*$",
    r"였나요\?*$", r"하셨나요\?*$", r"이신가요\?*$"
]

def sentence_count(q):
    parts = re.split(r"[.!?]", q)
    return len([p for p in parts if p.strip()])

def check_length(q):
    n = len(q)
    if n <= 45:
        return "PASS", n
    elif n <= 55:
        return "WARN", n
    else:
        return "FAIL", n

def check_forbidden(q):
    hits = [w for w in FORBIDDEN if w in q]
    return ("FAIL" if hits else "PASS"), hits

def check_open_ended(q):
    has_wh = any(w in q for w in WH_WORDS)
    closed_match = any(re.search(p, q) for p in CLOSED_PATTERNS)
    if closed_match and not has_wh:
        return "WARN", "wh-word 없이 폐쇄형 종결 패턴 감지 (오탐 가능, 수동 확인 권장)"
    return "PASS", None

def check_overlap(q, recent_questions):
    max_ratio = 0.0
    closest = None
    for rq in recent_questions:
        ratio = difflib.SequenceMatcher(None, q, rq).ratio()
        if ratio > max_ratio:
            max_ratio = ratio
            closest = rq
    if max_ratio >= 0.6:
        return "FAIL", (closest, round(max_ratio, 2))
    elif max_ratio >= 0.4:
        return "WARN", (closest, round(max_ratio, 2))
    return "PASS", (closest, round(max_ratio, 2))

def check_grade_c(q, digital_grade):
    if digital_grade == "C" and len(q) > 30:
        return "WARN", len(q)
    return "PASS", len(q)

def validate_case(case):
    q = case["output"]["question"]
    recent_questions = case.get("recent_questions", [])
    digital_grade = case.get("digital_grade")

    results = {}
    results["문장수(<=2)"] = ("PASS" if sentence_count(q) <= 2 else "FAIL", sentence_count(q))
    results["길이(25~45자 권장)"] = check_length(q)
    results["금지어"] = check_forbidden(q)
    results["열린질문"] = check_open_ended(q)
    results["recent_questions 중복"] = check_overlap(q, recent_questions)
    results["digital_grade C 난이도"] = check_grade_c(q, digital_grade)

    overall = "PASS"
    for k, (status, _) in results.items():
        if status == "FAIL":
            overall = "FAIL"
            break
        if status == "WARN" and overall != "FAIL":
            overall = "WARN"
    return overall, results

if __name__ == "__main__":
    with open("test_cases.json", encoding="utf-8") as f:
        cases = json.load(f)

    print(f"{'ID':4} {'전체':6} 세부")
    for case in cases:
        overall, results = validate_case(case)
        print(f"\n[{case['id']}] {case['desc']}  => 전체판정: {overall}")
        print(f"  question: {case['output']['question']}")
        for k, (status, detail) in results.items():
            print(f"  - {k:22}: {status:5} {detail}")
