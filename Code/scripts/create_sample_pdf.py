"""Create the synthetic sample PDF using only the Python standard library."""

from __future__ import annotations

from pathlib import Path
import sys
import textwrap

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.sample_data import SAMPLE_PAGES


def escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def page_stream(text: str) -> str:
    lines = []
    for paragraph in text.strip().splitlines():
        paragraph = paragraph.strip()
        if not paragraph:
            lines.append("")
            continue
        wrapped = textwrap.wrap(paragraph, width=88) or [""]
        lines.extend(wrapped)

    y = 760
    commands = ["BT", "/F1 10 Tf", "14 TL"]
    for line in lines:
        if y < 52:
            break
        commands.append(f"1 0 0 1 72 {y} Tm ({escape_pdf_text(line)}) Tj")
        y -= 14
    commands.append("ET")
    return "\n".join(commands)


def create_pdf(output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    objects: list[bytes] = []

    def add_object(body: str) -> int:
        objects.append(body.encode("latin-1"))
        return len(objects)

    add_object("<< /Type /Catalog /Pages 2 0 R >>")
    add_object("<< /Type /Pages /Kids [3 0 R 5 0 R 7 0 R] /Count 3 >>")
    add_object(
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Resources << /Font << /F1 4 0 R >> >> /Contents 9 0 R >>"
    )
    add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    add_object(
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Resources << /Font << /F1 4 0 R >> >> /Contents 10 0 R >>"
    )
    add_object("<< /Length 0 >>\nstream\n\nendstream")
    add_object(
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Resources << /Font << /F1 4 0 R >> >> /Contents 11 0 R >>"
    )
    add_object("<< /Length 0 >>\nstream\n\nendstream")

    streams = [page_stream(page) for page in SAMPLE_PAGES]
    for stream in streams:
        add_object(f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("latin-1"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("latin-1")
    )

    output.write_bytes(bytes(pdf))
    return output


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "data" / "sample_documents" / "vehicle_lighting_hld_sample.pdf"
    written = create_pdf(target)
    print(written)
