"""snapshot.py와 main.py 시험. 임시 폴더만 사용하고 문구는 모두 가짜입니다."""

import tempfile
import unittest
from pathlib import Path

from diff_text import MODIFIED
from main import format_result, read_items
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


if __name__ == "__main__":
    unittest.main()
