"""모니터링 실행 파일. items.txt의 품목을 받아 저장본과 비교하고 결과를 출력합니다."""

import sys
from pathlib import Path
from xml.etree.ElementTree import ParseError

from diff_text import MODIFIED
from fetch_api import ApiError, fetch_item, fetch_renewal
from renewal import format_renewal
from snapshot import check_item, save_snapshot

ITEMS_FILE = Path(__file__).parent / "items.txt"


def read_items(path=ITEMS_FILE):
    """품목기준코드 목록을 읽습니다. # 뒤의 글자는 설명으로 보고 무시합니다."""
    codes = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        code = line.split("#")[0].strip()
        if code:
            codes.append(code)
    return codes


def format_result(result):
    snapshot = result.snapshot
    lines = [f"[{result.status}] {snapshot['item_name']} ({snapshot['item_seq']})"]
    if result.changes:
        lines.append(f"  허가정보 변경일: {snapshot['change_date']}")
    for section, changes in result.changes.items():
        lines.append(f"  <{section}>")
        for change in changes:
            if change.kind == MODIFIED:
                lines.append(f"  [{change.kind}] {change.old}")
                lines.append(f"      -> {change.new}")
            else:
                lines.append(f"  [{change.kind}] {change.old or change.new}")
    for section in result.missing_sections:
        lines.append(f"  [경고] {section} 문서가 비어서 왔습니다. 예전 저장본을 유지합니다.")
    return "\n".join(lines)


def main():
    failures = 0
    for item_seq in read_items():
        try:
            result = check_item(fetch_item(item_seq))
        except (ApiError, ParseError) as error:
            print(f"[실패] {item_seq}: {error}")
            failures += 1
            continue
        print(format_result(result))
        # 갱신 정보를 못 받아도 허가문서 비교 결과는 저장되어야 합니다.
        try:
            record = fetch_renewal(item_seq, result.snapshot["item_name"])
            print(f"  {format_renewal(record)}")
        except ApiError as error:
            print(f"  [실패] 갱신 정보: {error}")
            failures += 1
        save_snapshot(result.snapshot)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
