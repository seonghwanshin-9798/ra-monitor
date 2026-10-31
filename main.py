"""모니터링 실행 파일. items.txt의 품목을 받아 저장본과 비교하고 보고서를 만듭니다."""

import re
import sys
from pathlib import Path
from xml.etree.ElementTree import ParseError

from diff_text import MODIFIED
from fetch_api import ApiError, fetch_item, fetch_renewal
from renewal import format_renewal, needs_attention
from snapshot import CHANGED, check_item, save_snapshot

BASE_DIR = Path(__file__).parent
ITEMS_FILE = BASE_DIR / "items.txt"
REPORT_TITLE_FILE = BASE_DIR / "report_title.txt"
REPORT_BODY_FILE = BASE_DIR / "report.md"

# GitHub 이슈 본문은 65,536자까지입니다. 초과하면 등록이 계속 실패하므로 미리 자릅니다.
MAX_BODY_CHARS = 60000

CHANGE_ENTRY = re.compile(r"(.+?), (\d{4}-\d{2}-\d{2})(?:/|$)")


def read_items(path=ITEMS_FILE):
    """품목기준코드 목록을 읽습니다. # 뒤의 글자는 설명으로 보고 무시합니다."""
    codes = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        code = line.split("#")[0].strip()
        if code:
            codes.append(code)
    return codes


def latest_change_reason(history):
    """변경 이력 글에서 가장 최근 날짜의 사유만 뽑습니다.

    예: "사용상주의사항변경, 2026-03-23/성상변경, 2019-09-09"
    """
    entries = CHANGE_ENTRY.findall(history or "")
    if not entries:
        return None
    latest = max(day for _, day in entries)
    return ", ".join(reason for reason, day in entries if day == latest)


def format_result(result):
    snapshot = result.snapshot
    lines = [f"[{result.status}] {snapshot['item_name']} ({snapshot['item_seq']})"]
    if result.changes:
        lines.append(f"  허가정보 변경일: {snapshot['change_date']}")
        reason = latest_change_reason(snapshot["change_history"])
        if reason:
            lines.append(f"  최근 변경 사유: {reason}")
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


def build_title(changed, alerts, failures):
    title = f"[허가 모니터링] 변경 {changed}건 / 갱신 임박 {alerts}건"
    if failures:
        title += f" / 실패 {failures}건"
    return title


def build_body(lines):
    """보고서를 코드 블록에 넣습니다. 표의 | 나 * 같은 기호가 서식으로 바뀌지 않습니다."""
    text = "\n".join(lines)
    if len(text) > MAX_BODY_CHARS:
        text = text[:MAX_BODY_CHARS] + "\n... 내용이 길어 잘렸습니다. snapshots 변경 기록을 확인하세요."
    return f"````text\n{text}\n````\n"


def main():
    lines = []
    changed = alerts = failures = 0

    def report(line):
        print(line)
        lines.append(line)

    for item_seq in read_items():
        try:
            result = check_item(fetch_item(item_seq))
        except (ApiError, ParseError) as error:
            report(f"[실패] {item_seq}: {error}")
            failures += 1
            continue
        report(format_result(result))
        changed += result.status == CHANGED
        # 갱신 정보를 못 받아도 허가문서 비교 결과는 저장되어야 합니다.
        try:
            record = fetch_renewal(item_seq, result.snapshot["item_name"])
            report(f"  {format_renewal(record)}")
            alerts += needs_attention(record)
        except ApiError as error:
            report(f"  [실패] 갱신 정보: {error}")
            failures += 1
        save_snapshot(result.snapshot)

    REPORT_TITLE_FILE.write_text(build_title(changed, alerts, failures), encoding="utf-8")
    REPORT_BODY_FILE.write_text(build_body(lines), encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
