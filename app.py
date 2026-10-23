import secrets
import string
from datetime import datetime

import streamlit as st
from fpdf import FPDF

st.set_page_config(page_title="개인정보 보호 자가진단", page_icon="🔒")

# 교육용 소규모 목록입니다. 전체 유출 비밀번호 목록을 검사하지 않습니다.
COMMON_PASSWORDS = {
    "password", "123456", "12345678", "qwerty", "abc123", "monkey",
    "1234567", "letmein", "trustno1", "dragon", "baseball", "111111",
    "iloveyou", "master", "sunshine", "ashley", "bailey", "passw0rd",
    "shadow", "123123", "654321", "superman", "qazwsx", "michael",
    "football", "12345", "1234", "adobe123", "photoshop", "access",
    "000000", "123456789", "welcome", "1234567890", "1qaz2wsx",
    "mustang", "696969", "batman", "princess", "login", "solo",
    "121212", "flower", "hottie", "loveme", "zaq1zaq1", "starwars",
    "admin", "666666", "hello", "freedom", "whatever", "aa123456",
    "charlie", "donald", "password1", "qwertyuiop", "lovely",
    "777777", "888888", "1q2w3e4r", "555555", "123qwe",
    "!@#$%^&*", "pass@123", "aa123456", "admin123",
}

# (질문, 개선 안내, PDF용 영문 안내, 중요도, 해당 없음 허용)
QUESTIONS = [
    (
        "비밀번호 유출·타인 노출이 의심되면 즉시 변경하나요?",
        "유출·노출이 의심되면 해당 비밀번호를 즉시 변경하고, 같은 비밀번호를 쓰는 다른 계정도 변경하세요.",
        "Replace exposed passwords promptly, including reused copies on other accounts.", 1, False,
    ),
    (
        "주요 계정에 2단계 인증을 설정했나요?",
        "주요 계정에서 2단계 인증을 설정하고 복구 코드를 안전하게 보관하세요.",
        "Enable two-factor authentication on important accounts and protect recovery codes.", 1, False,
    ),
    (
        "운영체제·브라우저·보안 프로그램을 최신 상태로 유지하나요?",
        "운영체제·브라우저·보안 프로그램의 자동 업데이트를 켜세요.",
        "Enable automatic updates for your operating system, browser, and security tools.", 2, False,
    ),
    (
        "예상하지 못한 메시지의 링크와 첨부파일은 출처를 확인하나요?",
        "의심스러운 링크 대신 공식 앱이나 직접 입력한 주소로 접속해 내용을 확인하세요.",
        "Verify unexpected messages through an official app or a known website address.", 1, False,
    ),
    (
        "개인정보를 제공하기 전에 요청 목적과 상대방을 확인하나요?",
        "개인정보 요청자의 신원과 필요성을 확인하고, 인증번호는 다른 사람에게 알려주지 마세요.",
        "Verify who requests personal information and never share verification codes.", 2, False,
    ),
    (
        "사이트마다 서로 다른 비밀번호를 사용하나요?",
        "사이트마다 고유한 비밀번호를 사용하세요. 특히 이메일과 금융 계정의 재사용을 피하세요.",
        "Use unique passwords for every service, especially email and financial accounts.", 1, False,
    ),
    (
        "공공 Wi-Fi에서는 네트워크를 확인하고 인증서 경고가 뜨면 접속을 중단하나요?",
        "공공 Wi-Fi 이름을 확인하고 인증서 경고를 무시하지 마세요. 민감한 작업은 신뢰할 수 있는 연결을 이용하세요.",
        "Verify public Wi-Fi networks, heed certificate warnings, and use trusted connections for sensitive tasks.", 2, True,
    ),
    (
        "간편 로그인 연동 앱과 계정 접근 권한을 주기적으로 정리하나요?",
        "계정 설정에서 연결된 앱을 확인하고 사용하지 않는 앱의 접근 권한을 해제하세요.",
        "Review connected applications and revoke access for apps you no longer use.", 3, True,
    ),
    (
        "공용 PC에서 비밀번호를 저장하지 않고 사용 후 로그아웃하나요?",
        "공용 PC에 비밀번호를 저장하지 말고 사용 후 로그아웃하세요. 방문 기록 삭제만으로 계정이 보호되지는 않습니다.",
        "Do not save passwords on shared computers; sign out after use. Clearing history alone is insufficient.", 2, True,
    ),
    (
        "사용하지 않는 계정을 정리하나요?",
        "사용하지 않는 계정은 필요한 데이터를 백업한 뒤 탈퇴하거나 비활성화하세요.",
        "Back up needed data, then close or deactivate unused accounts.", 3, True,
    ),
    (
        "신뢰할 수 있는 비밀번호 관리자를 사용하나요?",
        "신뢰할 수 있는 비밀번호 관리자를 검토하고, 사용한다면 관리자 계정도 강하게 보호하세요.",
        "Consider a trusted password manager and protect the manager account carefully.", 2, False,
    ),
    (
        "지원되는 서비스에서 패스키를 사용하나요?",
        "서비스가 지원한다면 패스키 사용을 검토하고 기기 잠금과 계정 복구 방법도 확인하세요.",
        "Consider passkeys where supported, with secure device locks and recovery options.", 2, True,
    ),
]

ANSWER_OPTIONS = ["선택하세요", "예", "아니요", "모름"]
PERSONAL_OPTIONS = ["선택하세요", "포함되지 않음", "포함됨", "모름"]


def invalidate_result():
    # 입력값이 달라지면 이전 점수와 PDF를 폐기합니다.
    st.session_state.pop("diagnosis", None)
    st.session_state.pop("report_pdf", None)


def reset_all():
    for key in list(st.session_state.keys()):
        if key.startswith("diag_") or key in {"diagnosis", "report_pdf"}:
            del st.session_state[key]


def has_triple(text):
    return any(text[i] == text[i + 1] == text[i + 2] for i in range(len(text) - 2))


def evaluate_password(password, personal_status):
    if not password:
        length_points = 0
    elif len(password) >= 16:
        length_points = 25
    elif len(password) >= 12:
        length_points = 20
    elif len(password) >= 8:
        length_points = 10
    else:
        length_points = 0

    known_weak = bool(password) and password.casefold() in COMMON_PASSWORDS
    no_triple = bool(password) and not has_triple(password)
    no_personal = bool(password) and personal_status == "포함되지 않음"
    checks = [
        ("길이: 8~11자 10점 / 12~15자 20점 / 16자 이상 25점", length_points, 25),
        ("내장된 흔한 비밀번호 목록에 없음", 10 if password and not known_weak else 0, 10),
        ("같은 문자가 3개 이상 연속되지 않음", 5 if no_triple else 0, 5),
        ("추측 가능한 개인정보가 없다고 응답함", 10 if no_personal else 0, 10),
    ]
    raw_score = sum(item[1] for item in checks)
    # 흔한 비밀번호는 다른 조건을 만족해도 점수가 높아지지 않도록 제한합니다.
    score = min(raw_score, 10) if known_weak else raw_score
    warnings = []
    actions = []
    if known_weak:
        warnings.append("내장된 흔한 비밀번호 목록과 일치합니다. 비밀번호 점수는 최대 10점으로 제한됩니다.")
        actions.append((0, "흔한 비밀번호 대신 길고 고유한 비밀번호를 사용하세요.",
                        "Replace common passwords with long, unique passwords."))
    if len(password) < 12:
        warnings.append("테스트 비밀번호가 짧습니다. 더 긴 비밀번호나 암호문구를 검토하세요.")
        actions.append((1, "비밀번호를 더 길게 만드세요. 이 교육용 도구에서는 16자 이상에 길이 만점을 부여합니다.",
                        "Use a longer password or passphrase; this educational rubric awards full length points at 16 characters."))
    elif len(password) < 16:
        actions.append((3, "더 긴 고유 비밀번호 또는 암호문구 사용을 검토하세요.",
                        "Consider a longer unique password or passphrase."))
    if password and not no_triple:
        actions.append((2, "같은 문자가 반복되는 단순한 패턴을 피하세요.",
                        "Avoid simple repeated-character patterns."))
    if personal_status in {"포함됨", "모름"}:
        if personal_status == "포함됨":
            warnings.append("추측 가능한 개인정보가 포함되었다고 응답했습니다.")
        actions.append((1, "이름·생일·전화번호 등 추측 가능한 개인정보가 포함되지 않았는지 확인하세요.",
                        "Check that the password does not contain guessable personal information."))
    return {"score": score, "checks": checks, "warnings": warnings, "actions": actions}


def generate_example(length=16):
    # random 대신 암호학적 난수 사용. 예시도 내장 목록과 반복 패턴을 검사합니다.
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    while True:
        candidate = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in candidate)
                and any(c.isupper() for c in candidate)
                and any(c.isdigit() for c in candidate)
                and any(c in string.punctuation for c in candidate)
                and not has_triple(candidate)
                and candidate.casefold() not in COMMON_PASSWORDS):
            return candidate


def grade_for(score):
    if score >= 80:
        return "자가진단 기준 충족도 높음", "High self-assessment adherence"
    if score >= 60:
        return "일부 항목 개선 필요", "Some improvement needed"
    if score >= 40:
        return "여러 항목 개선 필요", "Several improvements needed"
    return "우선적인 개선 필요", "Priority improvements needed"


def create_pdf_report(result):
    # 기본 Helvetica는 한글을 지원하지 않으므로 PDF 문자열은 영문만 사용합니다.
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=16)
    pdf.cell(0, 10, text="Privacy and Security Self-Assessment", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    lines = [
        f"Created (server time): {result['created_at']}",
        f"Educational score: {result['total_score']} / 100",
        f"Test password: {result['password_score']} / 50",
        f"Habits: {result['habit_score']} / 50",
        f"Result: {result['grade_en']}",
        f"Yes: {result['yes_count']} / Applicable questions: {result['applicable_count']}",
        f"Not sure: {result['unknown_count']} / Not applicable: {result['na_count']}",
        "",
        "IMPORTANT: This is an educational self-assessment, not a security audit.",
        "The password score is based on a TEST password, not your real accounts.",
        "Scores do not estimate attack probability or guarantee account security.",
        "A small local common-password list is used; this is not a breach check.",
        "Password, date of birth, and phone number are not included in this report.",
        "",
        "Scoring: length 25, local common-password check 10, repetition check 5,",
        "self-reported absence of personal information 10. Common passwords are capped at 10.",
        "Habits: round(50 x Yes / applicable questions). No and Not sure score zero.",
        "Not applicable is excluded from the denominator.",
        "",
        "Improvement actions (priority order):",
    ]
    if result["has_warning"]:
        lines += ["Attention: one or more test-password issues require review."]
    lines += [f"{i}. {action[2]}" for i, action in enumerate(result["actions"], 1)]
    if not result["actions"]:
        lines += ["Maintain your current habits and review account security settings regularly."]
    for line in lines:
        pdf.multi_cell(0, 6, text=line or " ", new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


st.title("🔒 개인정보 보호 자가진단")
st.write("테스트용 비밀번호와 평소 보안 습관을 점검하고, 개선할 행동을 확인하세요.")
st.warning("실제 사용 중인 비밀번호를 입력하지 마세요. 입력값은 가려져 있어도 Streamlit 서버로 전달됩니다.")
st.caption(
    "생년월일과 전화번호는 수집하지 않습니다. 이 코드는 입력 비밀번호를 파일·DB·PDF에 저장하지 않지만, "
    "입력값은 실행 중 서버 메모리에 존재합니다. 배포 환경의 로그·모니터링 설정은 운영자가 별도로 확인해야 합니다."
)
st.button("입력 및 진단 결과 초기화", on_click=reset_all)
st.caption("초기화는 현재 앱 세션의 입력과 결과를 지웁니다. 다운로드한 파일이나 외부 로그까지 삭제하지는 않습니다.")

st.header("1. 테스트용 비밀번호 점검")
password = st.text_input(
    "테스트용 비밀번호", type="password", key="diag_password",
    max_chars=256, on_change=invalidate_result,
    help="실제 계정 비밀번호가 아닌 연습용 문자열을 입력하세요.",
)
personal_status = st.radio(
    "테스트 비밀번호에 이름·생일·전화번호 등 추측 가능한 개인정보가 포함되어 있나요?",
    PERSONAL_OPTIONS, key="diag_personal", on_change=invalidate_result,
)
assessment = evaluate_password(password, personal_status)
if password:
    st.progress(assessment["score"] / 50)
    st.write(f"테스트 비밀번호 점수: **{assessment['score']} / 50점**")
    for label, points, maximum in assessment["checks"]:
        st.write(f"{'✅' if points == maximum else '△'} {label}: {points}/{maximum}점")
    for warning in assessment["warnings"]:
        st.warning(warning)
    if personal_status == "선택하세요":
        st.info("개인정보 포함 여부를 선택하면 해당 항목을 채점합니다.")
    st.caption("목록에 없다는 것이 안전하다는 뜻은 아닙니다. 점검 조건을 충족해도 실제 보안을 보장하지 않습니다.")

with st.expander("무작위 테스트 비밀번호 예시"):
    st.write("예시는 암호학적 난수로 생성하지만 서버에서 생성·표시됩니다. 실제 계정용 비밀번호는 신뢰할 수 있는 비밀번호 관리자에서 생성하세요.")
    if st.button("테스트 예시 생성"):
        st.session_state["diag_example"] = generate_example()
    if st.session_state.get("diag_example"):
        st.code(st.session_state["diag_example"], language=None)

st.header("2. 온라인 개인정보 보호 습관")
st.caption("‘모름’은 0점으로 처리하며 개선 안내를 제공합니다. ‘해당 없음’은 관련 기능·환경을 이용하지 않을 때만 선택하세요.")
answers = []
for i, (question, _, _, _, allow_na) in enumerate(QUESTIONS):
    options = ANSWER_OPTIONS + (["해당 없음"] if allow_na else [])
    answers.append(st.radio(
        f"{i + 1}. {question}", options, horizontal=True,
        key=f"diag_q_{i}", on_change=invalidate_result,
    ))

with st.expander("점수 계산 기준과 한계"):
    st.markdown(
        "- **테스트 비밀번호 50점:** 길이 25점, 내장 목록 확인 10점, 반복 문자 확인 5점, 개인정보 미포함 자가응답 10점.\n"
        "- **길이 점수:** 8자 미만 0점, 8~11자 10점, 12~15자 20점, 16자 이상 25점.\n"
        "- 내장 목록에 있는 흔한 비밀번호는 비밀번호 점수를 **최대 10점**으로 제한합니다.\n"
        "- **습관 50점:** `50 × ‘예’ 개수 ÷ 적용 대상 문항 수`를 정수로 반올림합니다.\n"
        "- ‘아니요’·‘모름’은 0점, ‘해당 없음’은 분모에서 제외합니다.\n"
        "- 개인정보가 포함되어 있는지는 직접 검증하지 않고 자가응답으로 판단합니다.\n"
        "- 이 배점은 교육용으로 설계한 기준이며 검증된 보안 위험 예측 모델이 아닙니다.\n"
        "- 테스트 비밀번호를 사용하므로 **실제 계정의 비밀번호 강도를 평가한 결과가 아닙니다.**\n"
        "- 등급 기준: 80점 이상 / 60점 이상 / 40점 이상 / 40점 미만."
    )

if st.button("최종 자가진단 결과 보기", type="primary"):
    invalidate_result()
    if not password:
        st.error("실제 비밀번호가 아닌 테스트용 비밀번호를 입력하세요.")
    elif personal_status == "선택하세요":
        st.error("테스트 비밀번호의 개인정보 포함 여부를 선택하세요.")
    elif "선택하세요" in answers:
        missing = [str(i + 1) for i, answer in enumerate(answers) if answer == "선택하세요"]
        st.error("응답하지 않은 문항: " + ", ".join(missing))
    else:
        # 이전 통과 상태에 의존하지 않고 현재 입력을 다시 평가합니다.
        assessment = evaluate_password(password, personal_status)
        applicable_count = sum(answer != "해당 없음" for answer in answers)
        yes_count = answers.count("예")
        habit_score = round(50 * yes_count / applicable_count) if applicable_count else 0
        total_score = assessment["score"] + habit_score
        grade_kr, grade_en = grade_for(total_score)
        actions = list(assessment["actions"])
        for answer, (_, guide_kr, guide_en, priority, _) in zip(answers, QUESTIONS):
            if answer in {"아니요", "모름"}:
                prefix = "먼저 설정·사용 여부를 확인하세요. " if answer == "모름" else ""
                actions.append((priority, prefix + guide_kr, guide_en))
        actions.sort(key=lambda action: action[0])
        result = {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "password_score": assessment["score"], "habit_score": habit_score,
            "total_score": total_score, "grade_kr": grade_kr, "grade_en": grade_en,
            "yes_count": yes_count, "applicable_count": applicable_count,
            "unknown_count": answers.count("모름"), "na_count": answers.count("해당 없음"),
            "has_warning": bool(assessment["warnings"]),
            "warnings": assessment["warnings"], "actions": actions,
        }
        # 결과에는 원문 비밀번호를 복사하거나 저장하지 않습니다.
        st.session_state["diagnosis"] = result

result = st.session_state.get("diagnosis")
if result:
    st.divider()
    st.header("3. 자가진단 결과")
    c1, c2, c3 = st.columns(3)
    c1.metric("테스트 비밀번호", f"{result['password_score']} / 50")
    c2.metric("보안 습관", f"{result['habit_score']} / 50")
    c3.metric("교육용 총점", f"{result['total_score']} / 100")
    st.info(f"{result['grade_kr']} — 실제 보안 수준이나 해킹 가능성을 뜻하지 않습니다.")
    st.caption(
        f"적용 문항 {result['applicable_count']}개 중 실천 {result['yes_count']}개 · "
        f"모름 {result['unknown_count']}개 · 해당 없음 {result['na_count']}개"
    )
    for warning in result["warnings"]:
        st.warning(warning)
    st.subheader("💡 우선 실천할 행동 최대 3가지")
    if result["actions"]:
        for i, (_, guide_kr, _) in enumerate(result["actions"][:3], 1):
            st.write(f"**{i}.** {guide_kr}")
        with st.expander("전체 맞춤 개선 가이드"):
            for i, (_, guide_kr, _) in enumerate(result["actions"], 1):
                st.write(f"{i}. {guide_kr}")
    else:
        st.success("이 자가진단 기준에서 추가 개선 항목이 없습니다. 계정 설정과 보안 알림을 지속적으로 확인하세요.")

    st.subheader("📄 결과 PDF 다운로드")
    st.caption("PDF는 영문으로 제공됩니다. 점수·개선 안내만 포함하며 입력 비밀번호는 포함하지 않습니다.")
    try:
        if "report_pdf" not in st.session_state:
            st.session_state["report_pdf"] = create_pdf_report(result)
        st.download_button(
            "영문 진단 결과 PDF 다운로드",
            data=st.session_state["report_pdf"],
            file_name="security_self_assessment.pdf", mime="application/pdf",
        )
    except Exception:
        st.error("PDF 생성에 실패했습니다. fpdf2 설치 상태를 확인하세요. 화면의 진단 결과는 계속 확인할 수 있습니다.")
