"""parse_doc.py 시험. 구조는 실제 응답과 같고 문구는 모두 가짜입니다."""

import unittest
import xml.etree.ElementTree as ET

from diff_text import MODIFIED, compare_sections
from parse_doc import clean_text, item_sections, parse_doc


def doc(body):
    return f'<DOC title="시험" type="NB"><SECTION title="">{body}</SECTION></DOC>'


def paragraph(text, tag_name="p"):
    return f'<PARAGRAPH tagName="{tag_name}"><![CDATA[{text}]]></PARAGRAPH>'


class CleanTextTest(unittest.TestCase):
    def test_removes_html_tags(self):
        self.assertEqual(clean_text("비타민 B<sub>1</sub> 결핍"), "비타민 B1 결핍")

    def test_marks_superscript(self):
        self.assertEqual(clean_text("10<sup>3</sup> 개"), "10^3 개")

    def test_keeps_comparison_signs(self):
        self.assertEqual(clean_text("크레아티닌 &lt;30 mL/min"), "크레아티닌 <30 mL/min")

    def test_keeps_korean_angle_brackets(self):
        self.assertEqual(clean_text("<표 1> 이상반응"), "<표 1> 이상반응")

    def test_normalizes_nbsp(self):
        self.assertEqual(clean_text("1일&nbsp;&nbsp;1회"), "1일 1회")

    def test_table_row_becomes_one_line(self):
        table = "<table><tr><th>구분</th><th>빈도</th></tr><tr><td>두통</td><td>흔함</td></tr></table>"
        self.assertEqual(clean_text(table), "구분 | 빈도\n두통 | 흔함")

    def test_table_with_line_breaks_between_cells(self):
        table = "<tbody> \n <tr> \n  <td> <p>두통</p> </td> \n  <td> <p>흔함</p> </td> \n </tr> \n</tbody>"
        self.assertEqual(clean_text(table), "두통 | 흔함")

    def test_empty_cells_keep_column_position(self):
        common = "<tr><td>두통</td><td>흔함</td><td></td></tr>"
        rare = "<tr><td>두통</td><td></td><td>드묾</td></tr>"
        self.assertEqual(clean_text(common), "두통 | 흔함")
        self.assertEqual(clean_text(rare), "두통 | | 드묾")


class ParseDocTest(unittest.TestCase):
    def test_keeps_titles_and_paragraphs_in_order(self):
        xml = doc(
            f'<ARTICLE title="1. 경고">{paragraph("가나다.")}</ARTICLE>'
            f'<ARTICLE title="2. 금기">{paragraph("라마바.")}</ARTICLE>'
        )
        self.assertEqual(parse_doc(xml), "1. 경고\n가나다.\n2. 금기\n라마바.")

    def test_title_only_article_is_kept(self):
        self.assertEqual(parse_doc(doc('<ARTICLE title="1. 저혈당시의 에너지 보급" />')), "1. 저혈당시의 에너지 보급")

    def test_empty_document(self):
        self.assertEqual(parse_doc(None), "")
        self.assertEqual(parse_doc(""), "")

    def test_broken_xml_raises(self):
        with self.assertRaises(ET.ParseError):
            parse_doc("<DOC><SECTION>")


class ItemSectionsTest(unittest.TestCase):
    def test_maps_fields_and_works_with_compare(self):
        old = {"EE_DOC_DATA": doc(paragraph("1일 1회 10 mg 투여한다.")), "UD_DOC_DATA": None, "NB_DOC_DATA": None}
        new = {"EE_DOC_DATA": doc(paragraph("1일 1회 20 mg 투여한다.")), "UD_DOC_DATA": None, "NB_DOC_DATA": None}
        changes = compare_sections(item_sections(old), item_sections(new))
        self.assertEqual(list(changes), ["효능효과"])
        self.assertEqual(changes["효능효과"][0].kind, MODIFIED)


if __name__ == "__main__":
    unittest.main()
