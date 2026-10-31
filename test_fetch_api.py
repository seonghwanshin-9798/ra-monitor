"""fetch_api.py 시험. 실제 인터넷 호출 없이 가짜 응답으로 확인합니다."""

import os
import unittest
from unittest.mock import Mock, patch

import requests

from fetch_api import ApiError, fetch_item, fetch_renewal

FAKE_KEY = "FAKE-KEY-FOR-TEST"


def fake_response(payload):
    response = Mock()
    response.json.return_value = payload
    return response


def normal(items):
    return {"header": {"resultCode": "00"}, "body": {"items": items}}


@patch.dict(os.environ, {"DATA_GO_KR_API_KEY": FAKE_KEY})
class FetchItemTest(unittest.TestCase):
    @patch("fetch_api.requests.get")
    def test_returns_exact_item(self, get):
        get.return_value = fake_response(normal([{"ITEM_SEQ": "111"}, {"ITEM_SEQ": "222"}]))
        self.assertEqual(fetch_item("222"), {"ITEM_SEQ": "222"})

    @patch("fetch_api.requests.get")
    def test_missing_item_raises(self, get):
        get.return_value = fake_response(normal([]))
        with self.assertRaises(ApiError):
            fetch_item("222")

    @patch("fetch_api.requests.get")
    def test_api_error_code_raises(self, get):
        get.return_value = fake_response({"header": {"resultCode": "30", "resultMsg": "오류"}})
        with self.assertRaises(ApiError):
            fetch_item("222")

    @patch("fetch_api.requests.get")
    def test_renewal_ignores_other_products_in_name_search(self, get):
        get.return_value = fake_response(
            normal([{"ITEM_SEQ": "999", "ITEM_NAME": "에시험약"}, {"ITEM_SEQ": "222", "ITEM_NAME": "시험약"}])
        )
        self.assertEqual(fetch_renewal("222", "시험약")["ITEM_NAME"], "시험약")

    @patch("fetch_api.requests.get")
    def test_error_message_does_not_leak_key(self, get):
        get.side_effect = requests.ConnectionError(f"url?serviceKey={FAKE_KEY}")
        with self.assertRaises(ApiError) as caught:
            fetch_item("222")
        self.assertNotIn(FAKE_KEY, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
