"""품목기준코드별 저장본을 관리하고, 새 문서와 비교하는 모듈."""

import json
from dataclasses import dataclass, field
from pathlib import Path

from diff_text import compare_sections
from parse_doc import item_sections

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"

FIRST_RUN = "첫 저장"
UNCHANGED = "변경 없음"
CHANGED = "변경 있음"


@dataclass
class CheckResult:
    status: str
    snapshot: dict
    changes: dict = field(default_factory=dict)
    missing_sections: list = field(default_factory=list)


def snapshot_path(item_seq, directory):
    return Path(directory) / f"{item_seq}.json"


def load_snapshot(item_seq, directory=SNAPSHOT_DIR):
    """저장본을 읽습니다. 저장본이 없으면 None을 돌려줍니다."""
    path = snapshot_path(item_seq, directory)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_snapshot(snapshot, directory=SNAPSHOT_DIR):
    """임시 파일에 다 쓴 뒤 바꿔치기합니다. 쓰다가 멈춰도 기존 저장본이 망가지지 않습니다."""
    path = snapshot_path(snapshot["item_seq"], directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def build_snapshot(item):
    """API 응답에서 저장할 내용만 골라냅니다."""
    return {
        "item_seq": item["ITEM_SEQ"],
        "item_name": item.get("ITEM_NAME"),
        "change_date": item.get("CHANGE_DATE"),
        "change_history": item.get("GBN_NAME"),
        "sections": item_sections(item),
    }


def check_item(item, directory=SNAPSHOT_DIR):
    """API 응답을 저장본과 비교합니다. 저장은 하지 않습니다.

    메일 발송 등이 실패해도 변경 내용을 잃지 않도록, 보고가 끝난 뒤
    호출하는 쪽에서 save_snapshot으로 저장합니다.
    """
    new = build_snapshot(item)
    old = load_snapshot(new["item_seq"], directory)
    if old is None:
        return CheckResult(FIRST_RUN, new)

    # 내용이 있던 문서가 비어서 오면 일시적인 응답 문제일 수 있습니다.
    # 전체 삭제로 알리지 않고 예전 내용을 그대로 유지합니다.
    missing = [
        name
        for name, text in old["sections"].items()
        if text and not new["sections"].get(name)
    ]
    for name in missing:
        new["sections"][name] = old["sections"][name]

    changes = compare_sections(old["sections"], new["sections"])
    return CheckResult(CHANGED if changes else UNCHANGED, new, changes, missing)
