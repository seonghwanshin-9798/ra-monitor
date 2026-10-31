"""두 문서를 문장 단위로 비교해 바뀐 문장만 뽑는 모듈.

이 모듈은 문서가 어떤 성분이나 품목의 것인지 모릅니다. 호출하는 쪽에서
품목기준코드별로 문서를 넘겨주면 그대로 품목 단위 비교가 됩니다.
"""

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

ADDED = "추가"
REMOVED = "삭제"
MODIFIED = "변경"

# 두 문장이 이 값 이상 비슷하면 "변경", 아니면 별개의 "삭제"와 "추가"로 봅니다. (0~1)
SIMILARITY_THRESHOLD = 0.6

# 마침표 등의 앞 글자가 숫자면 나누지 않습니다. ("1. 경고"가 쪼개지지 않게 하기 위함)
SENTENCE_END = re.compile(r"(?<=[^\d\s][.!?])\s+")


@dataclass(frozen=True)
class Change:
    kind: str
    old: str | None = None
    new: str | None = None


def split_sentences(text):
    """글을 문장 목록으로 나눕니다.

    띄어쓰기 개수 차이는 무시합니다. 줄바꿈은 제목과 본문을 가르기 위해 문장 경계로 봅니다.
    """
    sentences = []
    for line in text.splitlines():
        line = " ".join(line.split())
        sentences.extend(s for s in SENTENCE_END.split(line) if s)
    return sentences


def similarity(a, b):
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def pair_replaced(old_sentences, new_sentences):
    """바뀐 구간에서 서로 비슷한 문장끼리 짝지어 변경으로 묶습니다."""
    changes = []
    unused_new = list(new_sentences)
    for old in old_sentences:
        best = max(unused_new, key=lambda new: similarity(old, new), default=None)
        if best is not None and similarity(old, best) >= SIMILARITY_THRESHOLD:
            changes.append(Change(MODIFIED, old=old, new=best))
            unused_new.remove(best)
        else:
            changes.append(Change(REMOVED, old=old))
    changes.extend(Change(ADDED, new=new) for new in unused_new)
    return changes


def compare_text(old_text, new_text):
    """예전 글과 새 글을 비교해 Change 목록을 돌려줍니다.

    문장의 위치가 옮겨지면 일부러 삭제와 추가로 함께 보여줍니다.
    예를 들어 "일반적 주의"의 문장이 "경고"로 옮겨진 것은 중요한 변경이기 때문입니다.
    """
    old_sentences = split_sentences(old_text)
    new_sentences = split_sentences(new_text)
    matcher = SequenceMatcher(None, old_sentences, new_sentences, autojunk=False)

    changes = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "delete":
            changes.extend(Change(REMOVED, old=s) for s in old_sentences[i1:i2])
        elif tag == "insert":
            changes.extend(Change(ADDED, new=s) for s in new_sentences[j1:j2])
        elif tag == "replace":
            changes.extend(pair_replaced(old_sentences[i1:i2], new_sentences[j1:j2]))
    return changes


def compare_sections(old_sections, new_sections):
    """항목별 문서 묶음을 비교합니다. 바뀐 항목만 돌려줍니다.

    예: {"효능효과": "...", "용법용량": "...", "사용상 주의사항": "..."}
    """
    results = {}
    for section in {**old_sections, **new_sections}:
        changes = compare_text(
            old_sections.get(section, ""), new_sections.get(section, "")
        )
        if changes:
            results[section] = changes
    return results


if __name__ == "__main__":
    # 동작을 눈으로 확인하기 위한 가짜 문구입니다. 실제 허가 내용이 아닙니다.
    old = """1. 경고
시험약은 간 손상을 일으킬 수 있다.
2. 일반적 주의
1일 최대 10 mg을 넘지 않는다.
고령자는 신중히 투여한다."""
    new = """1. 경고
시험약은 간 손상을 일으킬 수 있다.
임신부에게 투여하지 않는다.
2. 일반적 주의
1일 최대 20 mg을 넘지 않는다."""

    for change in compare_text(old, new):
        if change.kind == MODIFIED:
            print(f"[{change.kind}] {change.old}\n    -> {change.new}")
        else:
            print(f"[{change.kind}] {change.old or change.new}")
