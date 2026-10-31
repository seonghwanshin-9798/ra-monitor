"""품목 갱신 신청 기한의 D-day를 계산하는 모듈."""

from datetime import date

# 갱신 신청 기한까지 남은 날이 이 값 이하면 "임박"으로 표시합니다.
WARNING_DAYS = 180


def parse_date(text):
    """"2028-09-27" 형태의 글자를 날짜로 바꿉니다. 비어 있거나 형식이 다르면 None입니다."""
    try:
        return date.fromisoformat(text)
    except (TypeError, ValueError):
        return None


def format_dday(days_left):
    if days_left > 0:
        return f"D-{days_left}"
    if days_left == 0:
        return "D-day"
    return f"D+{-days_left}"


def format_renewal(record, today=None):
    """유효기간 API 응답 하나를 알림 한 줄로 바꿉니다."""
    today = today or date.today()
    valid_until = record.get("VALID_TERM_DATE") or "없음"
    deadline = parse_date(record.get("VALID_TERM_DATE_CUTLINE"))
    if deadline is None:
        return f"[갱신 날짜 없음] 유효기간: {valid_until}"

    days_left = (deadline - today).days
    if days_left < 0:
        label = "갱신 기한 지남"
    elif days_left <= WARNING_DAYS:
        label = "갱신 임박"
    else:
        label = "갱신"
    return f"[{label}] 신청 기한: {deadline} ({format_dday(days_left)}) / 유효기간: {valid_until}"
