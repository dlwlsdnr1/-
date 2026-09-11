import string
import streamlit as st

st.set_page_config(page_title="개인정보 보호 체크 프로그램", page_icon="🔒")

st.title("개인정보 보호 체크 프로그램")
st.write("사용 중인 비밀번호와 온라인 보안 습관을 종합 점검해보세요.")

st.divider()

st.subheader("1. 기본 정보 입력")
birth_date = st.text_input("자신의 생년월일 8자리를 입력하세요", placeholder="예: 20100101")
phone_number = st.text_input("자신의 전화번호를 입력하세요", placeholder="예: 01012345678")
password = st.text_input("사용 중인 비밀번호를 입력하세요", type="password")

st.divider()

st.subheader("2. 온라인 개인정보 보호 습관 체크 (실천 중인 항목에 체크하세요)")

q1 = st.checkbox("1. 비밀번호를 3개월마다 변경하나요?")
q2 = st.checkbox("2. 2단계 인증을 사용하나요?")
q3 = st.checkbox("3. 백신 프로그램을 최신 상태로 유지하나요?")
q4 = st.checkbox("4. 모르는 사람이 보낸 링크를 함부로 누르지 않나요?")
q5 = st.checkbox("5. 개인정보를 함부로 다른 사람에게 알려주지 않나요?")
q6 = st.checkbox("6. 사이트마다 서로 다른 비밀번호를 사용하여 관리하나요?")
q7 = st.checkbox("7. 카페나 대중교통 등 암호 없는 공공 Wi-Fi에서 금융 거래나 로그인을 하지 않나요?")
q8 = st.checkbox("8. 네이버/카카오/구글 등으로 간편 로그인한 연동 앱 목록을 주기적으로 확인하고 정리하나요?")
q9 = st.checkbox("9. 공용 PC(학교, PC방 등) 사용 후 반드시 로그아웃과 방문 기록을 삭제하나요?")
q10 = st.checkbox("10. 더 이상 이용하지 않는 웹사이트나 앱의 회원 탈퇴를 주도적으로 하나요?")

st.divider()

if st.button("보안 점수 진단하기", type="primary"):
    birth_digits = "".join(c for c in birth_date if c.isdigit())
    if len(birth_digits) != 8:
        st.error("✘ 생년월일은 8자리 숫자로 입력해주세요. (예: 20100101)")
        st.stop()
    
    year, month, day = int(birth_digits[:4]), int(birth_digits[4:6]), int(birth_digits[6:8])
    if not (1900 <= year <= 2026 and 1 <= month <= 12 and 1 <= day <= 31):
        st.error("✘ 올바른 날짜 범위가 아닙니다. (연도: 1900~2026, 월: 1~12, 일: 1~31)")
        st.stop()

    password_score = 0
    is_valid = True
    
    birth_blocks = [birth_digits[:4], birth_digits[4:]]
    
    phone_digits = "".join(c for c in phone_number if c.isdigit())
    if phone_digits.startswith("010"):
        phone_digits = phone_digits[3:]
    
    phone_blocks = []
    if len(phone_digits) == 8:
        phone_blocks = [phone_digits[:4], phone_digits[4:]]
    elif len(phone_digits) >= 4:
        phone_blocks = [phone_digits[-4:]]

    birth_overlap = any(block in password for block in birth_blocks if block)
    phone_overlap = any(block in password for block in phone_blocks if block)

    st.subheader("비밀번호 보안 검사 결과")

    if birth_overlap or phone_overlap:
        if birth_overlap:
            st.error("✘ 비밀번호는 생년월일과 중복된 숫자를 포함해서는 안됩니다.")
        if phone_overlap:
            st.error("✘ 비밀번호는 전화번호와 중복된 숫자를 포함해서는 안됩니다.")
        st.warning("보안을 위해 비밀번호를 다시 설정한 후 이용해주세요.")
        st.stop()

    st.success("✔ 생년월일 및 전화번호와 중복된 4자리 숫자가 없습니다.")
    password_score += 10

    if len(password) >= 8:
        st.success("✔ 8자 이상입니다.")
        password_score += 10
    else:
        st.error("✘ 비밀번호를 8자 이상으로 설정하세요.")
        is_valid = False

    if any(c.isdigit() for c in password):
        st.success("✔ 숫자를 포함하고 있습니다.")
        password_score += 10
    else:
        st.error("✘ 숫자를 포함해야 합니다.")
        is_valid = False

    if any(c in string.punctuation for c in password):
        st.success("✔ 특수문자를 포함하고 있습니다.")
        password_score += 10
    else:
        st.error("✘ 특수문자를 포함해야 합니다.")
        is_valid = False

    if any(c.isupper() for c in password):
        st.success("✔ 대문자를 포함하고 있습니다.")
        password_score += 10
    else:
        st.info("✘ 대문자를 포함하면 더 안전합니다.")

    if not is_valid:
        st.warning("보안을 위해 비밀번호를 다시 설정한 후 프로그램을 다시 실행하세요.")
        st.stop()

    habit_questions = [q1, q2, q3, q4, q5, q6, q7, q8, q9, q10]
    habit_score = sum(5 for q in habit_questions if q)
    
    total_score = password_score + habit_score

    st.divider()
    st.subheader("최종 진단 결과")
    col1, col2, col3 = st.columns(3)
    col1.metric("비밀번호 점수", f"{password_score} / 50점")
    col2.metric("보안 습관 점수", f"{habit_score} / 50점")
    col3.metric("최종 보안 점수", f"{total_score} / 100점")

    if total_score >= 80:
        st.balloons()
        st.success("*최종 등급 : 1등급 (매우 안전)*")
    elif total_score >= 60:
        st.info("*최종 등급 : 2등급 (안전)*")
    elif total_score >= 40:
        st.warning("*최종 등급 : 3등급 (보통)*")
    elif total_score >= 20:
        st.error("*최종 등급 : 4등급 (위험)*")
    else:
        st.error("*최종 등급 : 5등급 (매우 위험)*")
