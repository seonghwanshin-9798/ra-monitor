"""식약처 허가정보 API에서 품목 정보를 받아오는 모듈."""

import os

import requests
from dotenv import load_dotenv

DETAIL_URL = (
    "https://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService08"
    "/getDrugPrdtPrmsnDtlInq08"
)
RENEWAL_URL = (
    "https://apis.data.go.kr/1471000/DrugPrdlstVldPrdInfoService01"
    "/getDrugPrdlstVldPrdInfoService01"
)
TIMEOUT_SECONDS = 30
NUM_OF_ROWS = 100


class ApiError(Exception):
    """API에서 품목을 받지 못했을 때 나는 오류입니다."""


def get_api_key():
    load_dotenv()
    key = os.getenv("DATA_GO_KR_API_KEY")
    if not key:
        raise ApiError(".env에 DATA_GO_KR_API_KEY가 없습니다.")
    return key


def request_item(url, item_seq, query):
    """API를 호출해 응답 중 품목기준코드가 일치하는 품목 하나를 돌려줍니다."""
    params = {
        "serviceKey": get_api_key(),
        "pageNo": 1,
        "numOfRows": NUM_OF_ROWS,
        "type": "json",
        **query,
    }
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        # 원래 오류 메시지에는 API 키가 포함된 주소가 들어 있을 수 있어 종류만 남깁니다.
        raise ApiError(f"품목 {item_seq}: 통신 실패 ({type(error).__name__})") from None

    header = data.get("header", {})
    if header.get("resultCode") != "00":
        raise ApiError(f"품목 {item_seq}: API 오류 ({header.get('resultMsg')})")

    items = data.get("body", {}).get("items") or []
    for item in items:
        if item.get("ITEM_SEQ") == item_seq:
            return item
    raise ApiError(f"품목 {item_seq}: 찾을 수 없습니다.")


def fetch_item(item_seq):
    """품목기준코드로 허가 상세정보 하나를 받아옵니다."""
    return request_item(DETAIL_URL, item_seq, {"item_seq": item_seq})


def fetch_renewal(item_seq, item_name):
    """품목 유효기간 정보를 받아옵니다.

    이 API는 제품명 검색이 부분 일치라서 다른 제품이 섞여 나올 수 있습니다.
    그래서 제품명으로 찾은 뒤 품목기준코드가 같은 것만 고릅니다.
    """
    return request_item(RENEWAL_URL, item_seq, {"ITEM_NAME": item_name})
