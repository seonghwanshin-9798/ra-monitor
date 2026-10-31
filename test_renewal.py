"""renewal.py 시험. 오늘 날짜를 고정해 언제 돌려도 결과가 같습니다."""

import unittest
from datetime import date

from renewal import WARNING_DAYS, format_renewal, parse_date

TODAY = date(2026, 1, 1)


def record(deadline, valid_until="2029-03-27"):
    return {"VALID_TERM_DATE": valid_until, "VALID_TERM_DATE_CUTLINE": deadline}


def days_later(days):
    return date.fromordinal(TODAY.toordinal() + days).isoformat()


class ParseDateTest(unittest.TestCase):
    def test_valid_date(self):
        self.assertEqual(parse_date("2028-09-27"), date(2028, 9, 27))

    def test_empty_or_wrong_values(self):
        for value in (None, "", "미정"):
            self.assertIsNone(parse_date(value))


class FormatRenewalTest(unittest.TestCase):
    def test_far_deadline(self):
        line = format_renewal(record(days_later(WARNING_DAYS + 1)), TODAY)
        self.assertTrue(line.startswith("[갱신] "))
        self.assertIn(f"D-{WARNING_DAYS + 1}", line)

    def test_boundary_is_warning(self):
        line = format_renewal(record(days_later(WARNING_DAYS)), TODAY)
        self.assertTrue(line.startswith("[갱신 임박] "))

    def test_today_is_d_day(self):
        line = format_renewal(record(days_later(0)), TODAY)
        self.assertTrue(line.startswith("[갱신 임박] "))
        self.assertIn("(D-day)", line)

    def test_passed_deadline(self):
        line = format_renewal(record(days_later(-3)), TODAY)
        self.assertTrue(line.startswith("[갱신 기한 지남] "))
        self.assertIn("(D+3)", line)

    def test_missing_dates(self):
        line = format_renewal({"VALID_TERM_DATE": None, "VALID_TERM_DATE_CUTLINE": ""}, TODAY)
        self.assertEqual(line, "[갱신 날짜 없음] 유효기간: 없음")


if __name__ == "__main__":
    unittest.main()
