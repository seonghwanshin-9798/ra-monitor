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


def days_until_deadline(record, today=None):
    """갱신 신청 기한까지 남은 날을 돌려줍니다. 기한을 알 수 없으면 None입니다."""
    deadline = parse_date(record.get("VALID_TERM_DATE_CUTLINE"))
    if deadline is None:
        return None
    return (deadline - (today or date.today())).days


def needs_attention(record, today=None):
    """기한이 임박했거나 이미 지났으면 True입니다."""
    days_left = days_until_deadline(record, today)
    return days_left is not None and days_left <= WARNING_DAYS


def format_dday(days_left):
    if days_left > 0:
        return f"D-{days_left}"
    if days_left == 0:
        return "D-day"
    return f"D+{-days_left}"


def format_renewal(record, today=None):
    """유효기간 API 응답 하나를 알림 한 줄로 바꿉니다."""
    valid_until = record.get("VALID_TERM_DATE") or "없음"
    days_left = days_until_deadline(record, today)
    if days_left is None:
        return f"[갱신 날짜 없음] 유효기간: {valid_until}"

    if days_left < 0:
        label = "갱신 기한 지남"
    elif days_left <= WARNING_DAYS:
        label = "갱신 임박"
    else:
        label = "갱신"
    deadline = record["VALID_TERM_DATE_CUTLINE"]
    return f"[{label}] 신청 기한: {deadline} ({format_dday(days_left)}) / 유효기간: {valid_until}"
