from __future__ import annotations

import copy
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"

ET.register_namespace("w", W_NS)


def w_tag(name: str) -> str:
    return f"{{{W_NS}}}{name}"


def parse_markdown_blocks(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    blocks: list[tuple[str, str]] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(("paragraph", " ".join(part.strip() for part in paragraph if part.strip())))
            paragraph.clear()

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            continue

        heading_match = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if heading_match:
            flush_paragraph()
            level = len(heading_match.group(1))
            text_value = heading_match.group(2).strip()
            if level == 1:
                blocks.append(("title", text_value))
            elif level == 2:
                blocks.append(("heading1", text_value))
            elif level == 3:
                blocks.append(("heading2", text_value))
            else:
                blocks.append(("heading3", text_value))
            continue

        if re.match(r"^(\d+\.\s+|-+\s+)", stripped):
            flush_paragraph()
            blocks.append(("list", stripped))
            continue

        paragraph.append(stripped)

    flush_paragraph()
    return blocks


def add_paragraph(body: ET.Element, text: str, style: str | None = None) -> None:
    p = ET.SubElement(body, w_tag("p"))
    if style:
        p_pr = ET.SubElement(p, w_tag("pPr"))
        p_style = ET.SubElement(p_pr, w_tag("pStyle"))
        p_style.set(w_tag("val"), style)

    r = ET.SubElement(p, w_tag("r"))
    t = ET.SubElement(r, w_tag("t"))
    if text.startswith(" ") or text.endswith(" ") or "  " in text:
        t.set(f"{{{XML_NS}}}space", "preserve")
    t.text = text


def build_docx(template_path: Path, markdown_path: Path, output_path: Path) -> None:
    blocks = parse_markdown_blocks(markdown_path.read_text(encoding="utf-8"))

    with ZipFile(template_path, "r") as src_zip:
        original_doc = ET.fromstring(src_zip.read("word/document.xml"))
        body = original_doc.find(w_tag("body"))
        if body is None:
            raise RuntimeError("Could not find document body in template DOCX.")

        sect_pr = body.find(w_tag("sectPr"))
        sect_pr_copy = copy.deepcopy(sect_pr) if sect_pr is not None else None

        for child in list(body):
            body.remove(child)

        style_map = {
            "title": "Title",
            "heading1": "Heading1",
            "heading2": "Heading2",
            "heading3": "Heading3",
            "paragraph": None,
            "list": None,
        }

        for block_type, text in blocks:
            clean_text = text.replace("`", "")
            add_paragraph(body, clean_text, style_map.get(block_type))

        if sect_pr_copy is not None:
            body.append(sect_pr_copy)

        updated_xml = ET.tostring(original_doc, encoding="utf-8", xml_declaration=True)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as dst_zip:
            for item in src_zip.infolist():
                data = updated_xml if item.filename == "word/document.xml" else src_zip.read(item.filename)
                dst_zip.writestr(item, data)


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    template = base_dir / "invited protocol draft.docx"
    markdown = base_dir / "revised_protocol_mimb.md"
    output = base_dir / "invited protocol draft_adapted.docx"
    build_docx(template, markdown, output)
    print(output)
