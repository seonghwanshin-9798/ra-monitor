"""diff_text.py 시험. 문구는 모두 가짜입니다."""

import unittest

from diff_text import (
    ADDED,
    MODIFIED,
    REMOVED,
    Change,
    compare_sections,
    compare_text,
    split_sentences,
)


class SplitSentencesTest(unittest.TestCase):
    def test_splits_on_sentence_end(self):
        self.assertEqual(
            split_sentences("첫째 문장이다. 둘째 문장이다."),
            ["첫째 문장이다.", "둘째 문장이다."],
        )

    def test_keeps_numbering_and_decimals(self):
        self.assertEqual(
            split_sentences("1. 경고\n1일 1.5 mg 투여한다."),
            ["1. 경고", "1일 1.5 mg 투여한다."],
        )

    def test_ignores_blank_lines(self):
        self.assertEqual(split_sentences("가나다.\n\n  \n라마바."), ["가나다.", "라마바."])


class CompareTextTest(unittest.TestCase):
    def test_same_text_has_no_changes(self):
        self.assertEqual(compare_text("가나다.", "가나다."), [])

    def test_whitespace_only_difference_is_ignored(self):
        self.assertEqual(compare_text("하루 한 번   복용한다.", "하루 한 번 복용한다."), [])

    def test_line_break_is_a_sentence_boundary(self):
        self.assertEqual(split_sentences("1. 경고\n가나다."), ["1. 경고", "가나다."])
        self.assertNotEqual(compare_text("하루 한 번 복용한다.", "하루 한 번\n복용한다."), [])

    def test_added_sentence(self):
        self.assertEqual(
            compare_text("가나다.", "가나다. 임신부에게 투여하지 않는다."),
            [Change(ADDED, new="임신부에게 투여하지 않는다.")],
        )

    def test_removed_sentence(self):
        self.assertEqual(
            compare_text("가나다. 고령자는 신중히 투여한다.", "가나다."),
            [Change(REMOVED, old="고령자는 신중히 투여한다.")],
        )

    def test_number_change_is_modified(self):
        self.assertEqual(
            compare_text("1일 최대 10 mg을 넘지 않는다.", "1일 최대 20 mg을 넘지 않는다."),
            [Change(MODIFIED, old="1일 최대 10 mg을 넘지 않는다.", new="1일 최대 20 mg을 넘지 않는다.")],
        )

    def test_unrelated_replacement_is_removed_and_added(self):
        self.assertEqual(
            compare_text("고령자는 신중히 투여한다.", "운전을 피해야 한다."),
            [Change(REMOVED, old="고령자는 신중히 투여한다."), Change(ADDED, new="운전을 피해야 한다.")],
        )

    def test_moved_sentence_is_reported(self):
        kinds = sorted(c.kind for c in compare_text("가나다. 라마바. 사아자.", "라마바. 사아자. 가나다."))
        self.assertEqual(kinds, sorted([ADDED, REMOVED]))


class CompareSectionsTest(unittest.TestCase):
    def test_returns_only_changed_sections(self):
        old = {"효능효과": "가나다.", "용법용량": "1회 1정 복용한다."}
        new = {"효능효과": "가나다.", "용법용량": "1회 2정 복용한다."}
        self.assertEqual(list(compare_sections(old, new)), ["용법용량"])

    def test_new_section_counts_as_added(self):
        self.assertEqual(
            compare_sections({}, {"효능효과": "가나다."}),
            {"효능효과": [Change(ADDED, new="가나다.")]},
        )


if __name__ == "__main__":
    unittest.main()
