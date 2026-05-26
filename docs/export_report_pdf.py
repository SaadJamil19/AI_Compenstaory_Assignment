"""Export docs/PROJECT_REPORT.md to docs/AI_CRM_Project_Report.pdf.

The script prefers Pandoc when available. If Pandoc is not installed, it uses
a built-in pure-Python fallback that creates a readable PDF with screenshot
placeholder boxes. No third-party package is required for the fallback.

Usage:
    python docs/export_report_pdf.py
"""
from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import textwrap


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "PROJECT_REPORT.md"
TARGET = ROOT / "docs" / "AI_CRM_Project_Report.pdf"

PAGE_WIDTH = 595
PAGE_HEIGHT = 842
MARGIN = 54
LINE_HEIGHT = 14
FONT_SIZE = 10
TITLE_SIZE = 16


def run_pandoc() -> bool:
    if not shutil.which("pandoc"):
        return False
    command = [
        "pandoc",
        str(SOURCE),
        "-o",
        str(TARGET),
        "--from",
        "markdown",
        "--toc",
        "--number-sections",
    ]
    print("Using Pandoc:", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)
    return True


def strip_markdown(line: str) -> str:
    line = line.strip()
    line = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", line)
    line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
    line = line.replace("**", "").replace("__", "").replace("`", "")
    line = line.replace("|", " | ")
    return line


def md_to_blocks(markdown: str) -> list[dict]:
    blocks = []
    in_code = False
    code_buffer: list[str] = []

    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                if code_buffer:
                    blocks.append({"type": "code", "text": "\n".join(code_buffer)})
                code_buffer = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_buffer.append(line)
            continue

        stripped = line.strip()
        if not stripped:
            blocks.append({"type": "space"})
            continue
        if "Screenshot to insert" in stripped or "Screenshot to be inserted" in stripped:
            text = strip_markdown(stripped.replace("> ", ""))
            blocks.append({"type": "screenshot", "text": text})
            continue
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            blocks.append({"type": "heading", "level": min(level, 3), "text": strip_markdown(stripped[level:].strip())})
            continue
        if stripped.startswith("- "):
            blocks.append({"type": "paragraph", "text": "- " + strip_markdown(stripped[2:])})
            continue
        blocks.append({"type": "paragraph", "text": strip_markdown(stripped)})
    return blocks


def pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class SimplePDF:
    def __init__(self):
        self.pages: list[list[str]] = []
        self.current: list[str] = []
        self.y = PAGE_HEIGHT - MARGIN
        self.new_page()

    def new_page(self):
        if self.current:
            self.pages.append(self.current)
        self.current = []
        self.y = PAGE_HEIGHT - MARGIN

    def ensure(self, height: int):
        if self.y - height < MARGIN:
            self.new_page()

    def text(self, value: str, size: int = FONT_SIZE, x: int = MARGIN, leading: int = LINE_HEIGHT):
        self.ensure(leading)
        self.current.append(f"BT /F1 {size} Tf {x} {self.y} Td ({pdf_escape(value)}) Tj ET")
        self.y -= leading

    def wrapped(self, value: str, width: int = 88, size: int = FONT_SIZE):
        for part in textwrap.wrap(value, width=width) or [""]:
            self.text(part, size=size)

    def heading(self, value: str, level: int):
        size = TITLE_SIZE if level == 1 else 13 if level == 2 else 11
        self.ensure(26)
        self.text(value, size=size, leading=20)

    def screenshot_box(self, value: str):
        self.ensure(78)
        x = MARGIN
        y = self.y - 50
        w = PAGE_WIDTH - (MARGIN * 2)
        h = 54
        self.current.append(f"{x} {y} {w} {h} re S")
        self.current.append(f"BT /F1 10 Tf {x + 12} {y + 32} Td (Screenshot to be inserted) Tj ET")
        for idx, line in enumerate(textwrap.wrap(value, width=76)[:2]):
            self.current.append(f"BT /F1 8 Tf {x + 12} {y + 18 - (idx * 10)} Td ({pdf_escape(line)}) Tj ET")
        self.y -= 68

    def finish(self):
        if self.current:
            self.pages.append(self.current)

    def render(self) -> bytes:
        self.finish()
        objects: list[bytes] = []
        catalog_id = 1
        pages_id = 2
        font_id = 3
        next_id = 4
        page_ids = []
        content_ids = []

        for _ in self.pages:
            page_ids.append(next_id)
            content_ids.append(next_id + 1)
            next_id += 2

        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        kids = " ".join(f"{pid} 0 R" for pid in page_ids)
        objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii"))
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

        for page_id, content_id, commands in zip(page_ids, content_ids, self.pages):
            page_obj = (
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>"
            )
            stream = "\n".join(commands).encode("latin-1", errors="replace")
            content_obj = b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"
            objects.append(page_obj.encode("ascii"))
            objects.append(content_obj)

        output = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for idx, obj in enumerate(objects, start=1):
            offsets.append(len(output))
            output.extend(f"{idx} 0 obj\n".encode("ascii"))
            output.extend(obj)
            output.extend(b"\nendobj\n")
        xref = len(output)
        output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        output.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        output.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
        )
        return bytes(output)


def run_builtin_export() -> None:
    print("Pandoc not found; using built-in PDF exporter.")
    blocks = md_to_blocks(SOURCE.read_text(encoding="utf-8"))
    pdf = SimplePDF()
    for block in blocks:
        kind = block["type"]
        if kind == "space":
            pdf.y -= 6
        elif kind == "heading":
            pdf.heading(block["text"], block["level"])
        elif kind == "screenshot":
            pdf.screenshot_box(block["text"])
        elif kind == "code":
            for line in block["text"].splitlines():
                pdf.wrapped("    " + line, width=80, size=8)
        else:
            pdf.wrapped(block["text"])
    TARGET.write_bytes(pdf.render())


def main() -> int:
    if not SOURCE.exists():
        print(f"Missing source report: {SOURCE}")
        return 1
    if not run_pandoc():
        run_builtin_export()
    print(f"Exported {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
