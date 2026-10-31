"""snapshot.py와 main.py 시험. 임시 폴더만 사용하고 문구는 모두 가짜입니다."""

import tempfile
import unittest
from pathlib import Path

from diff_text import MODIFIED
from main import (
    MAX_BODY_CHARS,
    build_body,
    build_title,
    format_result,
    latest_change_reason,
    read_items,
)
from snapshot import (
    CHANGED,
    FIRST_RUN,
    UNCHANGED,
    check_item,
    load_snapshot,
    save_snapshot,
)


def doc(text):
    return f'<DOC><SECTION title=""><ARTICLE title=""><PARAGRAPH tagName="p"><![CDATA[{text}]]></PARAGRAPH></ARTICLE></SECTION></DOC>'


def item(warning="1일 최대 10 mg을 넘지 않는다."):
    return {
        "ITEM_SEQ": "111",
        "ITEM_NAME": "시험약",
        "CHANGE_DATE": "20260101",
        "GBN_NAME": "",
        "EE_DOC_DATA": doc("효능 문구이다."),
        "UD_DOC_DATA": doc("용법 문구이다."),
        "NB_DOC_DATA": doc(warning) if warning else None,
    }


class CheckItemTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.directory = Path(folder.name) / "snapshots"

    def test_first_run_reports_no_changes(self):
        result = check_item(item(), self.directory)
        self.assertEqual(result.status, FIRST_RUN)
        self.assertEqual(result.changes, {})

    def test_check_does_not_save(self):
        check_item(item(), self.directory)
        self.assertIsNone(load_snapshot("111", self.directory))

    def test_unchanged(self):
        save_snapshot(check_item(item(), self.directory).snapshot, self.directory)
        self.assertEqual(check_item(item(), self.directory).status, UNCHANGED)

    def test_changed(self):
        save_snapshot(check_item(item(), self.directory).snapshot, self.directory)
        result = check_item(item("1일 최대 20 mg을 넘지 않는다."), self.directory)
        self.assertEqual(result.status, CHANGED)
        self.assertEqual(result.changes["사용상 주의사항"][0].kind, MODIFIED)

    def test_empty_document_keeps_old_text_and_warns(self):
        save_snapshot(check_item(item(), self.directory).snapshot, self.directory)
        result = check_item(item(warning=None), self.directory)
        self.assertEqual(result.status, UNCHANGED)
        self.assertEqual(result.missing_sections, ["사용상 주의사항"])
        self.assertIn("10 mg", result.snapshot["sections"]["사용상 주의사항"])

    def test_saved_snapshot_round_trip(self):
        snapshot = check_item(item(), self.directory).snapshot
        save_snapshot(snapshot, self.directory)
        self.assertEqual(load_snapshot("111", self.directory), snapshot)


class MainHelpersTest(unittest.TestCase):
    def test_read_items_ignores_comments(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "items.txt"
            path.write_text("# 설명\n111  # 시험약\n\n222\n", encoding="utf-8")
            self.assertEqual(read_items(path), ["111", "222"])

    def test_format_result_shows_warning(self):
        with tempfile.TemporaryDirectory() as folder:
            save_snapshot(check_item(item(), folder).snapshot, folder)
            result = check_item(item(warning=None), folder)
        self.assertIn("[경고] 사용상 주의사항", format_result(result))

    def test_latest_change_reason_keeps_all_reasons_of_latest_date(self):
        history = "주의사항변경(부작용포함), 2026-03-23/성상변경, 2026-03-23/용법변경, 2019-09-09"
        self.assertEqual(latest_change_reason(history), "주의사항변경(부작용포함), 성상변경")

    def test_latest_change_reason_handles_empty(self):
        self.assertIsNone(latest_change_reason(None))
        self.assertIsNone(latest_change_reason(""))

    def test_title_shows_failures_only_when_present(self):
        self.assertEqual(build_title(1, 0, 0), "[허가 모니터링] 변경 1건 / 갱신 임박 0건")
        self.assertEqual(build_title(0, 2, 3), "[허가 모니터링] 변경 0건 / 갱신 임박 2건 / 실패 3건")

    def test_long_body_is_cut_and_code_block_is_closed(self):
        body = build_body(["가" * (MAX_BODY_CHARS + 100)])
        self.assertLess(len(body), 65536)
        self.assertIn("잘렸습니다", body)
        self.assertTrue(body.endswith("````\n"))


if __name__ == "__main__":
    unittest.main()
