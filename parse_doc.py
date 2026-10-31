"""허가정보 API의 문서(XML)에서 사람이 읽는 글자를 꺼내는 모듈."""

import html
import re
import xml.etree.ElementTree as ET

# API 응답 항목 이름과 화면에 보여줄 문서 이름
DOC_FIELDS = {
    "EE_DOC_DATA": "효능효과",
    "UD_DOC_DATA": "용법용량",
    "NB_DOC_DATA": "사용상 주의사항",
}

# 영문자로 시작하는 태그만 지웁니다. ("<표 1>" 같은 본문 글자를 지우지 않기 위함)
HTML_TAG = re.compile(r"</?[a-zA-Z][^>]*>")
CELL_END = re.compile(r"</t[dh]\s*>", re.IGNORECASE)
ROW_END = re.compile(r"</tr\s*>", re.IGNORECASE)
SUP_START = re.compile(r"<sup\s*>", re.IGNORECASE)


def clean_text(text):
    """태그와 특수 기호를 정리합니다.

    표는 한 행을 한 줄로, 칸은 " | "로 구분합니다. 빈 칸도 남겨 두어야
    빈도표에서 어떤 이상반응이 어느 빈도 칸에 있는지 알 수 있습니다.
    """
    text = " ".join(text.split())  # 원문의 줄바꿈은 의미가 없어 먼저 없앱니다.
    text = SUP_START.sub("^", text)  # 10<sup>3</sup>이 103으로 읽히지 않게 합니다.
    text = CELL_END.sub(" | ", text)
    text = ROW_END.sub("\n", text)
    text = HTML_TAG.sub("", text)
    # 태그를 먼저 지운 뒤 바꿔야 "&lt;5"가 태그로 오해되지 않습니다.
    text = html.unescape(text)
    lines = (" ".join(line.split()).rstrip(" |") for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def parse_doc(xml_text):
    """문서 XML을 글로 바꿉니다. 제목과 문단은 문서 순서대로 한 줄씩 놓입니다.

    문서가 없으면 빈 글자를 돌려줍니다. XML이 깨져 있으면 ET.ParseError가 납니다.
    깨진 문서를 빈 글로 처리하면 전체 삭제로 잘못 알릴 수 있어 일부러 숨기지 않습니다.
    """
    if not xml_text:
        return ""
    lines = []
    for element in ET.fromstring(xml_text).iter():
        if element.tag in ("SECTION", "ARTICLE"):
            # 효능효과는 내용이 제목에만 들어 있는 경우가 있어 제목도 꺼냅니다.
            lines.append(clean_text(element.get("title", "")))
        elif element.tag == "PARAGRAPH":
            lines.append(clean_text("".join(element.itertext())))
    return "\n".join(line for line in lines if line)


def item_sections(item):
    """API 품목 응답 하나를 {"효능효과": 글, ...} 형태로 바꿉니다."""
    return {name: parse_doc(item.get(field)) for field, name in DOC_FIELDS.items()}
