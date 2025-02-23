import streamlit as st
from datetime import datetime, timedelta, date, time
import math

def format_korean_datetime(dt: datetime) -> str:
    """
    datetime 객체를 "YYYY-MM-DD 오후 HH:MM:SS" 형식으로 반환.
    """
    hour_24 = dt.hour
    minute = dt.minute
    second = dt.second

    # 오전/오후 처리
    meridiem = "오전" if hour_24 < 12 else "오후"
    hour_12 = hour_24 % 12
    if hour_12 == 0:
        hour_12 = 12

    date_str = dt.strftime("%Y-%m-%d")
    return f"{date_str} {meridiem} {hour_12:02d}:{minute:02d}:{second:02d}"

def get_usage_period_str(start_dt: datetime, end_dt: datetime) -> str:
    """
    두 시각의 차이를 "X박 X일 X시간 X분" 형식으로 계산하고
    입/퇴실 시각 정보를 함께 문자열로 리턴.
    """
    checkin_str = format_korean_datetime(start_dt)
    checkout_str = format_korean_datetime(end_dt)

    diff = end_dt - start_dt
    total_seconds = diff.total_seconds()
    if total_seconds < 0:
        return "퇴실 시간이 입실 시간과 같거나 더 이릅니다."

    nights = int(total_seconds // 86400)  # 하루=86400초
    remainder_seconds = total_seconds % 86400
    hours = int(remainder_seconds // 3600)
    remainder_seconds %= 3600
    minutes = int(remainder_seconds // 60)

    days = nights + 1 if nights > 0 else 0  # 0박이면 "0일"로 갈 수도 있지만, 취향에 맞게 조정

    usage_str = (
        f"● 입실 시간: {checkin_str}\n"
        f"● 퇴실 시간: {checkout_str}\n"
        f"● 위탁 기간: {nights}박 {days}일 {hours}시간 {minutes}분"
    )
    return usage_str

def calculate_hoteling(checkin_dt: datetime, checkout_dt: datetime, dog_count: int, diaper: bool, bath: bool):
    base_price = 30000  # 1박
    total_hours = (checkout_dt - checkin_dt).total_seconds() / 3600.0

    if total_hours <= 0:
        st.error("퇴실 시간이 입실 시간보다 같거나 빠릅니다.")
        return

    real_nights = int(total_hours // 24)
    remainder = total_hours % 24

    total_price = real_nights * base_price

    # 24시간 초과 후 3시간 넘어가면 +10,000원
    if remainder > 3:
        total_price += 10000

    # 기저귀: 1박당 2,000원 (최소 1일)
    if diaper:
        days_for_diaper = max(real_nights, 1)
        total_price += (2000 * days_for_diaper * dog_count)

    # 목욕 비용 (마리당 20,000원)
    if bath:
        total_price += (20000 * dog_count)

    # 마릿수 곱
    total_price *= dog_count

    # 2마리 이상이면 10% 할인
    if dog_count > 1:
        total_price = int(total_price * 0.9)

    return total_price

def calculate_daycare(start_dt: datetime, end_dt: datetime, dog_count: int, diaper: bool):
    duration_hours = (end_dt - start_dt).total_seconds() / 3600.0

    if duration_hours <= 0:
        st.error("종료 시간이 시작 시간보다 같거나 빠릅니다.")
        return

    # 3시간 이하 => 10,000원
    # 6시간 이하 => 15,000원
    # 6시간 초과 => 20,000원 (추가 요금 없음)
    if duration_hours <= 3:
        base_fee = 10000
    elif duration_hours <= 6:
        base_fee = 15000
    else:
        base_fee = 20000

    total_price = base_fee * dog_count

    # 기저귀 (2,000원/일)
    if diaper:
        total_price += (2000 * dog_count)

    # 2마리 이상이면 10% 할인
    if dog_count > 1:
        total_price = int(total_price * 0.9)

    return total_price


# ------------- Streamlit UI 시작 -------------
st.title("지지밍고 서비스 요금 계산기")

service = st.radio("서비스를 선택하세요", ("호텔링", "데이케어"), horizontal=True)

if service == "호텔링":
    # 호텔링 설정
    st.subheader("애견호텔 (1박 30,000원, 24시간 초과 3시간 이후 +10,000원)")

    col1, col2 = st.columns(2)
    with col1:
        checkin_day = st.date_input("입실 날짜", value=date.today())
        checkin_time = st.time_input("입실 시간", value=time(9, 0))  # 오전 9시 기본
    with col2:
        checkout_day = st.date_input("퇴실 날짜", value=date.today())
        checkout_time = st.time_input("퇴실 시간", value=time(10, 0))  # 오전 10시 기본

    dog_count = st.number_input("마리 수", min_value=1, max_value=50, value=1)
    diaper = st.checkbox("기저귀 필요 (1박당 2,000원)")
    bath = st.checkbox("목욕 (마리당 20,000원 추가)")

    if st.button("계산하기"):
        # datetime 결합
        checkin_dt = datetime.combine(checkin_day, checkin_time)
        checkout_dt = datetime.combine(checkout_day, checkout_time)

        usage_str = get_usage_period_str(checkin_dt, checkout_dt)
        st.write("**이용기간 안내**")
        st.text(usage_str)

        total = calculate_hoteling(checkin_dt, checkout_dt, dog_count, diaper, bath)
        if total is not None:
            st.success(f"최종 요금: {total:,}원")

else:
    # 데이케어 설정
    st.subheader("데이케어 (3시간 이하=10,000원, 6시간 이하=15,000원, 6시간 초과=20,000원)")

    col1, col2 = st.columns(2)
    with col1:
        start_time = st.time_input("시작 시간", value=time(9, 0))
    with col2:
        end_time = st.time_input("종료 시간", value=time(16, 0))

    dog_count = st.number_input("마리 수", min_value=1, max_value=50, value=1)
    diaper_dc = st.checkbox("기저귀 필요 (2,000원/일)")

    if st.button("계산하기"):
        # 데이케어는 당일만 가정하므로 날짜는 동일
        today = date.today()
        start_dt = datetime.combine(today, start_time)
        end_dt = datetime.combine(today, end_time)

        usage_str = get_usage_period_str(start_dt, end_dt)
        st.write("**이용기간 안내**")
        st.text(usage_str)

        total = calculate_daycare(start_dt, end_dt, dog_count, diaper_dc)
        if total is not None:
            st.success(f"최종 요금: {total:,}원")
