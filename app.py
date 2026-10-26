import secrets
import string
from datetime import datetime

import streamlit as st
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

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
        "비밀번호가 유출되거나 다른 사람에게 알려진 것 같으면 바로 바꾸나요?",
        "비밀번호가 알려진 것 같다면 바로 바꿔주세요. 같은 비밀번호를 쓰는 다른 계정도 함께 바꾸면 좋아요.",
        "Replace exposed passwords promptly, including reused copies on other accounts.", 1, False,
    ),
    (
        "자주 쓰는 중요한 계정에 2단계 인증을 켜두었나요?",
        "중요한 계정에는 2단계 인증을 켜주세요. 복구 코드도 안전한 곳에 보관해두세요.",
        "Enable two-factor authentication on important accounts and protect recovery codes.", 1, False,
    ),
    (
        "기기와 브라우저, 보안 프로그램을 꾸준히 업데이트하나요?",
        "업데이트를 놓치지 않도록 기기와 브라우저, 보안 프로그램의 자동 업데이트를 켜보세요.",
        "Enable automatic updates for your operating system, browser, and security tools.", 2, False,
    ),
    (
        "낯선 메시지의 링크나 첨부파일은 출처를 확인한 뒤 여나요?",
        "수상한 링크는 누르지 말고, 공식 앱이나 직접 입력한 주소로 접속해 확인해보세요.",
        "Verify unexpected messages through an official app or a known website address.", 1, False,
    ),
    (
        "개인정보를 알려주기 전에 누가, 왜 필요한지 확인하나요?",
        "개인정보를 요청하는 사람이 누구인지, 왜 필요한지 먼저 확인해보세요. 인증번호는 다른 사람에게 알려주지 마세요.",
        "Verify who requests personal information and never share verification codes.", 2, False,
    ),
    (
        "사이트마다 서로 다른 비밀번호를 사용하나요?",
        "사이트마다 다른 비밀번호를 사용해보세요. 특히 이메일과 금융 계정은 꼭 따로 설정해주세요.",
        "Use unique passwords for every service, especially email and financial accounts.", 1, False,
    ),
    (
        "공공 Wi-Fi에 연결할 때 이름을 확인하고, 인증서 경고가 뜨면 접속을 멈추나요?",
        "공공 Wi-Fi 이름을 먼저 확인해주세요. 인증서 경고가 뜨면 접속을 멈추고, 중요한 작업은 믿을 수 있는 연결에서 해주세요.",
        "Verify public Wi-Fi networks, heed certificate warnings, and use trusted connections for sensitive tasks.", 2, True,
    ),
    (
        "내 계정에 연결된 앱을 확인하고, 안 쓰는 앱의 연결을 해제하나요?",
        "계정 설정에서 연결된 앱을 살펴보세요. 더 이상 쓰지 않는 앱은 연결을 해제하면 좋아요.",
        "Review connected applications and revoke access for apps you no longer use.", 3, True,
    ),
    (
        "공용 PC에서는 비밀번호를 저장하지 않고, 사용 후 로그아웃하나요?",
        "공용 PC에서는 비밀번호를 저장하지 말고, 사용 후 꼭 로그아웃해주세요. 방문 기록만 지우는 것으로는 부족해요.",
        "Do not save passwords on shared computers; sign out after use. Clearing history alone is insufficient.", 2, True,
    ),
    (
        "더 이상 쓰지 않는 계정은 정리하나요?",
        "안 쓰는 계정은 필요한 자료를 먼저 백업하고, 탈퇴하거나 비활성화해보세요.",
        "Back up needed data, then close or deactivate unused accounts.", 3, True,
    ),
    (
        "믿을 수 있는 비밀번호 관리자를 사용하나요?",
        "비밀번호가 많아 기억하기 어렵다면 비밀번호 관리자를 알아보세요. 관리자 계정의 보안 설정도 꼭 챙겨주세요.",
        "Consider a trusted password manager and protect the manager account carefully.", 2, False,
    ),
    (
        "패스키를 지원하는 서비스에서는 패스키를 사용하나요?",
        "패스키를 지원하는 서비스라면 사용해보세요. 기기 잠금과 계정 복구 방법도 함께 확인해주세요.",
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
        ("비밀번호 길이", length_points, 25),
        ("앱의 흔한 비밀번호 목록에 없는지", 10 if password and not known_weak else 0, 10),
        ("같은 문자가 3번 이상 이어지지 않는지", 5 if no_triple else 0, 5),
        ("개인정보가 없다고 답했는지", 10 if no_personal else 0, 10),
    ]
    raw_score = sum(item[1] for item in checks)
    # 흔한 비밀번호는 다른 조건을 만족해도 점수가 높아지지 않도록 제한합니다.
    score = min(raw_score, 10) if known_weak else raw_score
    warnings = []
    actions = []
    if known_weak:
        warnings.append("흔히 쓰이는 비밀번호예요. 쉽게 추측될 수 있어 비밀번호 점수는 최대 10점까지만 받을 수 있어요.")
        actions.append((0, "흔한 비밀번호 대신 나만의 길고 고유한 비밀번호를 만들어보세요.",
                        "Replace common passwords with long, unique passwords."))
    if len(password) < 12:
        warnings.append("비밀번호가 조금 짧아요. 더 길게 만들거나 여러 단어를 조합해보세요.")
        actions.append((1, "비밀번호를 더 길게 만들어보세요. 이 앱에서는 16자 이상이면 길이 점수를 모두 받을 수 있어요.",
                        "Use a longer password or passphrase; this educational rubric awards full length points at 16 characters."))
    elif len(password) < 16:
        actions.append((3, "비밀번호를 조금 더 길게 만들거나 나만의 암호문구를 사용해보세요.",
                        "Consider a longer unique password or passphrase."))
    if password and not no_triple:
        actions.append((2, "같은 문자가 연달아 반복되는 단순한 패턴은 피해보세요.",
                        "Avoid simple repeated-character patterns."))
    if personal_status in {"포함됨", "모름"}:
        if personal_status == "포함됨":
            warnings.append("개인정보가 들어 있다고 답했어요. 다른 사람이 추측하기 쉬울 수 있어요.")
        actions.append((1, "이름이나 생일, 전화번호처럼 추측하기 쉬운 정보는 빼주세요.",
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
        return "좋은 습관을 잘 지키고 있어요!", "High self-assessment adherence"
    if score >= 60:
        return "몇 가지만 더 챙겨볼까요?", "Some improvement needed"
    if score >= 40:
        return "하나씩 바꿔나가면 좋아요", "Several improvements needed"
    return "지금부터 함께 점검해봐요", "Priority improvements needed"


def create_pdf_report(result):
    """Create an in-memory PDF. No passwords are passed to this function."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=(210 * mm, 297 * mm),
        rightMargin=20 * mm, leftMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
        title="My Security Check", author="Privacy Self-Check",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportBody", fontName="Helvetica", fontSize=10,
        leading=15, spaceAfter=8, textColor=colors.HexColor("#26334D"),
    ))
    story = []

    def add(text, style="ReportBody"):
        # Escape user-independent strings as well to avoid XML parsing errors.
        story.append(Paragraph(escape(str(text)), styles[style]))

    add("My Security Check", "Title")
    add(f"Created (server time): {result['created_at']}")
    story.append(Spacer(1, 5 * mm))
    add(f"Total score: {result['total_score']} / 100", "Heading2")
    add(f"Test password: {result['password_score']} / 50")
    add(f"Security habits: {result['habit_score']} / 50")
    add(f"Result: {result['grade_en']}")
    add(f"Habits practiced: {result['yes_count']} / {result['applicable_count']}")
    add(f"Not sure: {result['unknown_count']} | Not applicable: {result['na_count']}")
    add("Try these first", "Heading2")
    if result["has_warning"]:
        add("Please review the test-password issues shown in the app, regardless of the total score.")
    if result["actions"]:
        for i, action in enumerate(result["actions"][:3], 1):
            add(f"{i}. {action[2]}")
        if len(result["actions"]) > 3:
            add("More tips", "Heading2")
            for i, action in enumerate(result["actions"][3:], 4):
                add(f"{i}. {action[2]}")
    else:
        add("Keep up your good habits and check your account settings regularly.")
    add("About this check", "Heading2")
    add("This educational self-check uses a test password and your answers. It does not measure the security of your real accounts or guarantee protection.")
    add("Scoring: test password 50 points; habits 50 points. Habit score = round(50 x Yes / applicable questions). Not applicable answers are excluded; No and Not sure earn no points.")
    add("Password scoring: length up to 25; small local common-password list check 10; repeated-character check 5; self-reported absence of personal information 10. Listed common passwords are capped at 10 points. This is not a leaked-password lookup.")
    add("Your password is not included in this report.")
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    if not pdf_bytes.startswith(b"%PDF-"):
        raise ValueError("The report could not be created as a PDF.")
    return pdf_bytes


st.title("🔒 개인정보 보호 자가진단")
st.write("내 보안 습관은 어떨까요? 간단히 확인하고, 오늘부터 바꿀 수 있는 습관을 찾아보세요.")
st.warning("실제 비밀번호 대신 연습용 비밀번호를 입력해주세요. 가려진 입력값도 서버로 전달돼요.")
with st.expander("입력한 정보는 어떻게 처리되나요?"):
    st.write("생년월일과 전화번호는 받지 않아요. 입력한 비밀번호는 앱에서 파일이나 PDF로 저장하지 않지만, 실행 중에는 서버 메모리에 있어요.")
    st.caption("배포 환경의 로그와 모니터링 설정은 운영자가 별도로 확인해야 해요. 초기화해도 이미 내려받은 파일이나 외부 로그는 지워지지 않아요.")
st.button("처음부터 다시 하기", on_click=reset_all)

st.header("1. 연습용 비밀번호를 확인해볼까요?")
password = st.text_input(
    "연습용 비밀번호", type="password", key="diag_password",
    max_chars=256, on_change=invalidate_result,
    help="실제로 쓰지 않는 비밀번호로 테스트해주세요.",
)
personal_status = st.radio(
    "이 비밀번호에 이름이나 생일, 전화번호가 들어 있나요?",
    PERSONAL_OPTIONS, key="diag_personal", on_change=invalidate_result,
)
assessment = evaluate_password(password, personal_status)
if password:
    st.progress(assessment["score"] / 50)
    st.write(f"연습용 비밀번호 점수: **{assessment['score']} / 50점**")
    for label, points, maximum in assessment["checks"]:
        st.text(f"{'✓' if points == maximum else '•'} {label} · {points}/{maximum}점")
    for warning in assessment["warnings"]:
        st.warning(warning)
    if personal_status == "선택하세요":
        st.info("개인정보가 들어 있는지도 선택해주세요.")
    st.caption("이 앱의 목록에 없더라도 안전한 비밀번호라고 단정할 수는 없어요.")

with st.expander("어떤 비밀번호를 만들면 좋을까요?"):
    st.write("버튼을 누르면 연습용 예시가 나와요. 실제 계정에 쓸 비밀번호는 믿을 수 있는 비밀번호 관리자에서 만들어주세요.")
    if st.button("예시 만들어보기"):
        st.session_state["diag_example"] = generate_example()
    if st.session_state.get("diag_example"):
        st.code(st.session_state["diag_example"], language=None)

st.header("2. 평소 습관을 체크해보세요")
st.caption("평소 내 모습에 가까운 답을 골라주세요. 이용하지 않는 기능이나 환경은 ‘해당 없음’을 선택하면 돼요.")
answers = []
for i, (question, _, _, _, allow_na) in enumerate(QUESTIONS):
    options = ANSWER_OPTIONS + (["해당 없음"] if allow_na else [])
    answers.append(st.radio(
        f"{i + 1}. {question}", options, horizontal=True,
        key=f"diag_q_{i}", on_change=invalidate_result,
    ))

with st.expander("점수는 어떻게 계산하나요?"):
    st.markdown(
        "- **연습용 비밀번호 50점:** 길이 25점 + 흔한 비밀번호 확인 10점 + 반복 문자 확인 5점 + 개인정보 없음 응답 10점.\n"
        "- **길이:** 8자 미만 0점 / 8–11자 10점 / 12–15자 20점 / 16자 이상 25점.\n"
        "- 앱의 흔한 비밀번호 목록에 있으면 비밀번호 점수는 최대 10점이에요.\n"
        "- **보안 습관 50점:** 해당하는 문항 중 ‘예’라고 답한 비율에 따라 계산해요. 소수점은 반올림해요.\n"
        "- ‘아니요’와 ‘모름’은 0점이고, ‘해당 없음’은 계산에서 빼요.\n"
        "- 개인정보 포함 여부는 직접 답한 내용을 반영해요.\n"
        "- 결과 구간은 80점 이상, 60점 이상, 40점 이상, 40점 미만으로 나눠요.\n"
        "- 이 점수는 학습을 위한 참고용이에요. 실제 비밀번호의 강도나 해킹 가능성을 측정하지 않아요."
    )

if st.button("내 결과 확인하기", type="primary"):
    invalidate_result()
    if not password:
        st.error("먼저 연습용 비밀번호를 입력해주세요.")
    elif personal_status == "선택하세요":
        st.error("비밀번호에 개인정보가 들어 있는지 선택해주세요.")
    elif "선택하세요" in answers:
        missing = [str(i + 1) for i, answer in enumerate(answers) if answer == "선택하세요"]
        st.error("아직 답하지 않은 문항이 있어요: " + ", ".join(missing))
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
                prefix = "설정되어 있는지 먼저 확인해보세요. " if answer == "모름" else ""
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
    st.header("3. 나의 점검 결과")
    c1, c2, c3 = st.columns(3)
    c1.metric("연습용 비밀번호", f"{result['password_score']} / 50")
    c2.metric("보안 습관", f"{result['habit_score']} / 50")
    c3.metric("전체 점수", f"{result['total_score']} / 100")
    st.info(result["grade_kr"])
    st.caption("연습용 비밀번호와 직접 답한 습관을 바탕으로 한 참고용 결과예요. 실제 계정의 안전을 보장하지는 않아요.")
    st.caption(
        f"적용 문항 {result['applicable_count']}개 중 실천 {result['yes_count']}개 · "
        f"모름 {result['unknown_count']}개 · 해당 없음 {result['na_count']}개"
    )
    for warning in result["warnings"]:
        st.warning(warning)
    st.subheader("💡 이것부터 해보세요")
    if result["actions"]:
        for i, (_, guide_kr, _) in enumerate(result["actions"][:3], 1):
            st.write(f"**{i}.** {guide_kr}")
        with st.expander("다른 개선 팁도 보기"):
            for i, (_, guide_kr, _) in enumerate(result["actions"], 1):
                st.write(f"{i}. {guide_kr}")
    else:
        st.success("이번 점검에서 추가로 안내할 항목은 없어요. 지금처럼 좋은 습관을 이어가주세요!")

    st.subheader("📄 결과를 저장해두세요")
    st.caption("점수와 개선 팁을 영문 PDF로 저장할 수 있어요. 입력한 비밀번호는 담지 않아요.")
    try:
        if "report_pdf" not in st.session_state:
            st.session_state["report_pdf"] = create_pdf_report(result)
        st.download_button(
            "결과 PDF 내려받기",
            data=st.session_state["report_pdf"],
            file_name="security_self_assessment.pdf", mime="application/pdf",
        )
    except Exception as exc:
        st.error("PDF를 만들지 못했어요. 아래 오류 내용을 확인한 뒤 다시 시도해주세요. 점검 결과는 그대로 남아 있어요.")
        with st.expander("오류 내용 확인하기"):
            st.code(f"{type(exc).__name__}: {exc}", language=None)
            st.caption("수정본의 requirements.txt로 패키지를 설치한 뒤 앱을 다시 실행해주세요.")
        if st.button("PDF 다시 만들기"):
            st.session_state.pop("report_pdf", None)
            st.rerun()
