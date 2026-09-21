import string
import random
import streamlit as st
import streamlit.components.v1 as components
from fpdf import FPDF

# 오디오 재생용 보조 함수
def play_sound(sound_url):
    audio_html = f"""
        <audio autoplay style="display:none;">
            <source src="{sound_url}" type="audio/ogg">
        </audio>
    """
    components.html(audio_html, height=0)

# 흔히 사용되는 비밀번호 목록
COMMON_PASSWORDS = list(set([
    "password", "123456", "12345678", "qwerty", "abc123", "monkey", "1234567",
    "letmein", "trustno1", "dragon", "baseball", "111111", "iloveyou", "master",
    "sunshine", "ashley", "bailey", "passw0rd", "shadow", "123123", "654321",
    "superman", "qazwsx", "michael", "Football", "12345", "1234", "adobe123",
    "photoshop", "access", "000000", "123456789", "welcome", "1234567890",
    "1qaz2wsx", "mustang", "696969", "batman", "football", "princess", "login",
    "solo", "121212", "flower", "sunshine", "hottie", "loveme", "zaq1zaq1",
    "starwars", "admin", "666666", "hello", "freedom", "whatever",
    "aa123456", "charlie", "donald", "password1", "qwertyuiop",
    "lovely", "777777", "888888", "1q2w3e4r", "555555", "123qwe",
    "!@#$%^&*", "Pass@123", "Aa123456", "admin123"
]))

def generate_safe_password(length=12):
    if length < 8:
        length = 8
    all_chars = string.ascii_letters + string.digits + string.punctuation
    # 무작위 추출 후 연속 3개 중복이 없는지 검증
    while True:
        pw = "".join(random.choices(all_chars, k=length))
        if not any(pw[i] == pw[i+1] == pw[i+2] for i in range(len(pw) - 2)):
            return pw

def create_pdf_report(grade_str, total_score, pass_score, habit_score, guide_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=16)
    pdf.cell(200, 10, txt="Security Diagnosis Report", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 10, txt=f"Total Score: {total_score} / 100", ln=True)
    pdf.cell(200, 10, txt=f"Password Score: {pass_score} / 50", ln=True)
    pdf.cell(200, 10, txt=f"Habit Score: {habit_score} / 50", ln=True)
    pdf.cell(200, 10, txt=f"Final Grade: {grade_str}", ln=True)
    pdf.ln(10)
    
    pdf.cell(200, 10, txt="[ Security Improvement Guide ]", ln=True)
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(0, 8, txt=guide_text)
    
    output_res = pdf.output()
    if isinstance(output_res, str):
        return output_res.encode('latin-1')
    return bytes(output_res)

st.set_page_config(page_title="개인정보 보호 체크 프로그램", page_icon="🔒")
st.title("개인정보 보호 체크 프로그램")
st.write("사용 중인 비밀번호와 온라인 보안 습관을 종합 점검해보세요.")

st.divider()

st.subheader("1. 기본 정보 입력 및 실시간 비밀번호 진단")

birth_date = st.text_input("생년월일 8자리", placeholder="예: 20100101")
phone_number = st.text_input("전화번호", placeholder="예: 01012345678")
password = st.text_input("사용 중인 비밀번호 입력", type="password")

birth_digits = "".join(c for c in birth_date if c.isdigit())
phone_digits = "".join(c for c in phone_number if c.isdigit())
phone_middle_last = phone_digits[3:] if len(phone_digits) >= 11 else ""

birth_blocks = [birth_digits[:4], birth_digits[4:]] if len(birth_digits) == 8 else []
phone_blocks = [phone_middle_last[:4], phone_middle_last[4:]] if len(phone_middle_last) == 8 else []

# 비밀번호 조건 검사
cond_length = len(password) >= 8
cond_digit = any(c.isdigit() for c in password)
cond_punct = any(c in string.punctuation for c in password)
cond_upper = any(c.isupper() for c in password)

birth_overlap = any(b in password for b in birth_blocks if b)
phone_overlap = any(p in password for p in phone_blocks if p)
cond_overlap = not (birth_overlap or phone_overlap) if password else False

# 동일한 문자가 3개 연속으로 입력되었는지 확인 (3개 이상 연속시 False)
has_triple_consecutive = any(
    password[i] == password[i+1] == password[i+2] 
    for i in range(len(password) - 2)
) if len(password) >= 3 else False

cond_no_triple_consecutive = not has_triple_consecutive if password else False

met_conditions = sum([
    cond_length, 
    cond_digit, 
    cond_punct, 
    cond_upper, 
    cond_overlap, 
    cond_no_triple_consecutive
])

if password:
    st.markdown("#### 📊 비밀번호 실시간 복잡도")
    progress_val = met_conditions / 6.0
    st.progress(progress_val)
    
    if password in COMMON_PASSWORDS:
        st.error("🚨 **위험:** 자주 사용되는 취약한 비밀번호 목록에 해당합니다. 즉시 재설정해주세요!")
    elif has_triple_consecutive:
        st.error("🚨 **위험:** 동일한 문자가 3개 이상 연속으로 포함되어 있습니다. (예: aaa, 111, !!!)")
    elif met_conditions <= 2:
        st.error(f"🔴 현재 상태: **위험** (충족 조건: {met_conditions}/6개)")
    elif met_conditions <= 5:
        st.warning(f"🟡 현재 상태: **보통** (충족 조건: {met_conditions}/6개)")
    else:
        st.success(f"🟢 현재 상태: **안전** (충족 조건: 6/6개 모두 완료)")

st.write("")

if st.button("기본 정보 유효성 검사", type="primary"):
    if len(birth_digits) != 8:
        st.error("✘ 생년월일은 8자리 숫자로 입력해주세요.")
        st.stop()

    year, month, day = int(birth_digits[:4]), int(birth_digits[4:6]), int(birth_digits[6:8])
    if not (1900 <= year <= 2026 and 1 <= month <= 12 and 1 <= day <= 31):
        st.error("✘ 올바른 생년월일 범위가 아닙니다.")
        st.stop()

    if len(phone_digits) != 11 or not phone_digits.startswith("010"):
        st.error("✘ 전화번호는 010으로 시작하는 11자리 숫자여야 합니다.")
        st.stop()

    if phone_middle_last and phone_middle_last[0] == "0":
        st.error("✘ 전화번호 010 다음 첫 번째 자리에는 0이 올 수 없습니다.")
        st.stop()

    if password in COMMON_PASSWORDS:
        st.error("✘ 자주 사용되는 해킹 취약 비밀번호에 해당합니다. 비밀번호를 재설정해주세요.")
        recommended_pw = generate_safe_password(12)
        st.info("💡 **추천 안전 비밀번호:**")
        st.code(recommended_pw, language="")
        st.stop()

    if birth_overlap or phone_overlap:
        st.error("✘ 비밀번호에 생년월일이나 전화번호와 중복되는 숫자가 포함되어 있습니다.")
        recommended_pw = generate_safe_password(12)
        st.info("💡 **추천 안전 비밀번호:**")
        st.code(recommended_pw, language="")
        st.stop()

    if has_triple_consecutive:
        st.error("✘ 동일한 문자가 3개 이상 연속으로 사용할 수 없습니다. (예: aaa, 111 등)")
        recommended_pw = generate_safe_password(12)
        st.info("💡 **추천 안전 비밀번호:**")
        st.code(recommended_pw, language="")
        st.stop()

    if met_conditions < 6:
        st.warning("⚠️ 비밀번호 6가지 조건을 모두 충족해야 다음 단계로 진행할 수 있습니다.")
        recommended_pw = generate_safe_password(12)
        st.info("💡 **추천 안전 비밀번호:**")
        st.code(recommended_pw, language="")
        st.stop()

    password_score = int((met_conditions / 6.0) * 50)
    st.session_state["info_passed"] = True
    st.session_state["password_score"] = password_score
    st.success("✔ 모든 기본 정보 및 비밀번호 검사를 통과했습니다. 아래 2번 항목으로 이동하세요.")

if st.session_state.get("info_passed", False):
    st.divider()
    st.subheader("2. 온라인 개인정보 보호 습관 체크")

    st.markdown("#### **2-1. 기본 보안 수칙**")
    q1 = st.checkbox("1. 비밀번호를 3개월마다 변경하나요?")
    q2 = st.checkbox("2. 2단계 인증을 사용하나요?")
    q3 = st.checkbox("3. 백신 프로그램을 최신 상태로 유지하나요?")
    q4 = st.checkbox("4. 모르는 사람이 보낸 링크를 함부로 누르지 않나요?")
    q5 = st.checkbox("5. 개인정보를 함부로 다른 사람에게 알려주지 않나요?")

    st.markdown("#### **2-2. 일상 속 개인정보 보호 습관**")
    q6 = st.checkbox("6. 사이트마다 서로 다른 비밀번호를 사용하여 관리하나요?")
    q7 = st.checkbox("7. 공공 Wi-Fi에서 금융 거래나 로그인을 하지 않나요?")
    q8 = st.checkbox("8. 간편 로그인 연동 앱 목록을 주기적으로 정리하나요?")
    q9 = st.checkbox("9. 공용 PC 사용 후 로그아웃 및 방문 기록을 삭제하나요?")
    q10 = st.checkbox("10. 이용하지 않는 웹사이트 회원 탈퇴를 하나요?")

    st.divider()

    if st.button("최종 보안 점수 진단하기"):
        password_score = st.session_state.get("password_score", 50)
        habit_questions = [q1, q2, q3, q4, q5, q6, q7, q8, q9, q10]
        habit_score = sum(5 for q in habit_questions if q)
        total_score = password_score + habit_score

        st.subheader("📊 최종 진단 결과")
        col1, col2, col3 = st.columns(3)
        col1.metric("비밀번호 점수", f"{password_score} / 50점")
        col2.metric("보안 습관 점수", f"{habit_score} / 50점")
        col3.metric("최종 보안 점수", f"{total_score} / 100점")

        if total_score >= 80:
            grade_str = "1 Grade (Very Safe)"
            st.balloons()
            st.success("🎉 **최종 등급 : 1등급 (매우 안전)**")
            guide_text_kr = (
                "훌륭한 보안 의식을 가지고 계십니다! 현재 보안 습관을 지속해 주세요:\n"
                "- 3개월마다 주기적으로 비밀번호를 변경해 주세요.\n"
                "- 주요 계정에는 2단계 인증(2FA)을 꼭 유지해 주세요."
            )
            guide_text_pdf = (
                "Excellent security awareness! Maintain current habits:\n"
                "- Change passwords periodically every 3 months.\n"
                "- Keep 2-factor authentication active on all vital accounts."
            )
            play_sound("https://actions.google.com/sounds/v1/cheers/crowd_cheer.ogg")

        elif total_score >= 60:
            grade_str = "2 Grade (Safe)"
            st.info("🔵 **최종 등급 : 2등급 (안전)**")
            guide_text_kr = (
                "전반적으로 양호한 보안 상태입니다. 몇 가지만 보완해 보세요:\n"
                "- 소셜 미디어 및 주요 사이트에 2단계 인증을 설정하세요.\n"
                "- 사용하지 않는 간편 로그인 연동 앱 권한을 정기적으로 정리하세요."
            )
            guide_text_pdf = (
                "Good overall security with minor areas to improve:\n"
                "- Turn on 2FA (Two-Factor Authentication) for social media.\n"
                "- Clean up unused OAuth linked app permissions regularly."
            )
            play_sound("https://actions.google.com/sounds/v1/cartoon/clime_up_reverb.ogg")

        elif total_score >= 40:
            grade_str = "3 Grade (Moderate)"
            st.warning("🟡 **최종 등급 : 3등급 (보통)**")
            guide_text_kr = (
                "보안 위험이 일부 감지되었습니다. 아래 조치를 권장합니다:\n"
                "- 여러 사이트에 동일한 비밀번호를 재사용하지 마세요.\n"
                "- 암호가 없는 공공 Wi-Fi 환경에서는 금융 거래를 자제해 주세요."
            )
            guide_text_pdf = (
                "Moderate risk detected! Action recommended:\n"
                "- Stop reusing passwords across multiple online services.\n"
                "- Avoid logging into sensitive accounts on public Wi-Fi."
            )
            play_sound("https://actions.google.com/sounds/v1/cartoon/boing.ogg")

        else:
            grade_str = "4-5 Grade (High Risk)"
            st.error("🚨 **최종 등급 : 위험/매우 위험**")
            guide_text_kr = (
                "취약한 보안 상태입니다! 즉각적인 조치가 필요합니다:\n"
                "- 쉬운 비밀번호를 대소문자, 숫자, 특수문자 조합으로 즉시 변경하세요.\n"
                "- 최신 백신 프로그램을 설치하고 바이러스 정밀 검사를 진행하세요."
            )
            guide_text_pdf = (
                "Urgent action required! High vulnerability:\n"
                "- Replace weak passwords with complex combinations immediately.\n"
                "- Install up-to-date antivirus software and run full system scans."
            )
            st.warning("💡 **새로운 비밀번호 추천:**")
            st.code(generate_safe_password(12), language="")
            play_sound("https://actions.google.com/sounds/v1/emergency/alarm_clock.ogg")

        st.markdown("---")
        st.subheader("💡 등급별 맞춤 보안 개선 가이드")
        st.info(guide_text_kr)

        pdf_bytes = create_pdf_report(
            grade_str, total_score, password_score, habit_score, guide_text_pdf
        )
        st.download_button(
            label="📄 진단 결과 PDF 리포트 다운로드",
            data=pdf_bytes,
            file_name="security_diagnosis_report.pdf",
            mime="application/pdf"
        )
