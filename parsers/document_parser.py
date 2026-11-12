"""
parsers/document_parser.py — Text extraction from PDF, DOCX, and TXT files.

Public API:
    • extract_text(file_path)   -> str        (raises typed exceptions)
    • UnsupportedFormatError
    • EmptyDocumentError

Design notes:
    • Each extractor is a small private helper — easy to extend to new formats.
    • PDF: pypdf; DOCX: python-docx; TXT: UTF-8 with fallbacks for legacy
      encodings (cp1251 is common for old Russian files).
    • Scanned PDFs (no text layer) trigger EmptyDocumentError so the GUI can
      show a helpful message instead of silently indexing nothing.

Run the self-test with:
    python -m parsers.document_parser
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Allow `python parsers/document_parser.py` in addition to `-m`.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ──────────────────────── Custom exceptions ────────────────────────

class UnsupportedFormatError(Exception):
    """Raised when the file extension is not one of the supported formats."""


class EmptyDocumentError(Exception):
    """Raised when a document is valid but contains no extractable text."""


# ──────────────────────── Public API ────────────────────────

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".docx", ".txt"})

# Encodings tried in order for .txt files (UTF first, then legacy).
_TXT_ENCODINGS: tuple[str, ...] = ("utf-8", "utf-8-sig", "cp1251", "latin-1")


def extract_text(file_path: str | Path) -> str:
    """
    Extract plain text from a supported document.

    Parameters
    ----------
    file_path : str | Path
        Path to a .pdf, .docx, or .txt file.

    Returns
    -------
    str
        Extracted text, stripped of leading/trailing whitespace.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    UnsupportedFormatError
        If the extension is not in SUPPORTED_EXTENSIONS.
    EmptyDocumentError
        If extraction succeeds but yields no text (e.g. scanned PDF).
    RuntimeError
        If the underlying library fails for any other reason.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFormatError(
            f"Unsupported format: '{ext}'. "
            f"Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    try:
        if ext == ".pdf":
            text = _extract_pdf(path)
        elif ext == ".docx":
            text = _extract_docx(path)
        elif ext == ".txt":
            text = _extract_txt(path)
        else:  # pragma: no cover — defensive, unreachable
            raise UnsupportedFormatError(f"Unsupported format: '{ext}'")
    except (UnsupportedFormatError, EmptyDocumentError):
        raise
    except Exception as exc:
        raise RuntimeError(
            f"Failed to extract text from '{path.name}': {exc}"
        ) from exc

    text = text.strip()
    if not text:
        if ext == ".pdf":
            raise EmptyDocumentError(
                "No text found. Scanned PDFs are not supported."
            )
        raise EmptyDocumentError(f"No text found in document: {path.name}")

    return text


# ──────────────────────── Private extractors ────────────────────────

def _extract_pdf(path: Path) -> str:
    """Extract text from a PDF using pypdf. Returns '' for scanned PDFs."""
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        try:
            content = page.extract_text() or ""
        except Exception:
            # Some malformed pages fail — skip them, don't crash the whole doc.
            content = ""
        if content.strip():
            pages.append(content.strip())
    return "\n\n".join(pages)


def _extract_docx(path: Path) -> str:
    """Extract text from a .docx (paragraphs + table cells) using python-docx."""
    from docx import Document

    doc = Document(str(path))
    parts: list[str] = []

    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            parts.append(paragraph.text)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    parts.append(cell.text)

    return "\n".join(parts)


def _extract_txt(path: Path) -> str:
    """Read a .txt file, trying UTF-8 then common legacy encodings."""
    last_error: UnicodeDecodeError | None = None
    for encoding in _TXT_ENCODINGS:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
    raise RuntimeError(
        f"Could not decode '{path.name}' with any known encoding "
        f"({', '.join(_TXT_ENCODINGS)}). Last error: {last_error}"
    )


# ──────────────────────── Self-test ────────────────────────

_TEST_DIR_NAME: str = "_test_files"


def _create_test_files(test_dir: Path) -> None:
    """Generate fixture files for the self-test."""
    test_dir.mkdir(parents=True, exist_ok=True)

    # 1. Plain text
    (test_dir / "test.txt").write_text(
        "Hello from a TXT file.\nSecond line.", encoding="utf-8"
    )

    # 2. DOCX
    from docx import Document
    doc = Document()
    doc.add_heading("Test DOCX", level=1)
    doc.add_paragraph("Hello from a DOCX file.")
    doc.save(str(test_dir / "test.docx"))

    # 3. PDF with text (needs reportlab — test-only dependency)
    try:
        from reportlab.pdfgen import canvas  # type: ignore[import-not-found]

        pdf_path = test_dir / "test.pdf"
        c = canvas.Canvas(str(pdf_path))
        c.drawString(100, 750, "Hello from a PDF file.")
        c.save()
    except ImportError:
        print(
            "[skip] reportlab not installed — 'test.pdf' will not be created.\n"
            "       Install it with: pip install reportlab"
        )

    # 4. Empty PDF (blank page, no text layer) — for EmptyDocumentError test
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with open(test_dir / "test_empty.pdf", "wb") as f:
        writer.write(f)

    # 5. Unsupported format
    (test_dir / "test.xyz").write_text("unknown", encoding="utf-8")


def _run_case(label: str, fn: Any, expected: str) -> bool:
    """Run one test case. Returns True on pass, False on fail."""
    try:
        result = fn()
        if expected == "success":
            preview = result[:60].replace("\n", " ")
            print(f"  [PASS] {label}: extracted {len(result)} chars — \"{preview}…\"")
            return True
        print(f"  [FAIL] {label}: expected {expected}, but got success")
        return False
    except Exception as exc:
        actual = type(exc).__name__
        if actual == expected:
            print(f"  [PASS] {label}: raised {actual} — {exc}")
            return True
        print(f"  [FAIL] {label}: expected {expected}, got {actual} — {exc}")
        return False


def _run_self_test() -> int:
    test_dir = Path(__file__).resolve().parent / _TEST_DIR_NAME
    print(f"[setup] Generating fixtures in: {test_dir}")
    _create_test_files(test_dir)

    print("\n[run] Test cases:")

    cases: list[tuple[str, Any, str]] = [
        ("test.txt",       lambda: extract_text(test_dir / "test.txt"),       "success"),
        ("test.docx",      lambda: extract_text(test_dir / "test.docx"),      "success"),
        ("test.pdf",       lambda: extract_text(test_dir / "test.pdf"),       "success"),
        ("test_empty.pdf", lambda: extract_text(test_dir / "test_empty.pdf"), "EmptyDocumentError"),
        ("test.xyz",       lambda: extract_text(test_dir / "test.xyz"),       "UnsupportedFormatError"),
        ("missing.pdf",    lambda: extract_text(test_dir / "missing.pdf"),    "FileNotFoundError"),
    ]

    # Skip PDF-with-text case if the fixture was not created (no reportlab).
    if not (test_dir / "test.pdf").exists():
        cases = [c for c in cases if c[0] != "test.pdf"]

    passed = sum(_run_case(*c) for c in cases)
    total = len(cases)

    print(f"\n[summary] {passed}/{total} tests passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(_run_self_test())