"""
utils.py
--------
PDF utility helpers using PyMuPDF (fitz).

  extract_pages()         – returns {page_num: PageData} for every page
  pages_to_text()         – joins text from selected pages into one string
  pages_to_vision_msgs()  – builds OpenAI image_url content blocks
"""

import base64
import fitz
from models import PageData


def extract_pages(pdf_path: str) -> dict:
    """
    Open a PDF and extract text + a PNG image for every page.
    Returns dict keyed by 1-based page numbers.
    """
    doc = fitz.open(pdf_path)
    pages = {}

    for idx in range(len(doc)):
        page = doc[idx]
        page_num = idx + 1

        text = page.get_text("text").strip()

        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        img_b64 = base64.b64encode(pix.tobytes("png")).decode()

        pages[page_num] = PageData(
            page_number=page_num,
            text=text,
            image_b64=img_b64,
        )
    print("pages", pages)
    doc.close()
    return pages


def pages_to_text(pages: dict, page_numbers: list) -> str:
    """Combine extracted text from the given page numbers."""
    parts = []
    for pn in sorted(page_numbers):
        if pn in pages:
            parts.append(
                f"=== Page {pn} ===\n{pages[pn]['text'] or '[image-only page]'}"
            )
    return "\n\n".join(parts)


def pages_to_vision_msgs(pages: dict, page_numbers: list) -> list:
    """
    Build a list of OpenAI content blocks (image_url type) for the
    given page numbers. These go inside the user message content list.
    """
    blocks = []
    for pn in sorted(page_numbers):
        if pn in pages:
            b64 = pages[pn]["image_b64"]
            blocks.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64}",
                        "detail": "high",
                    },
                }
            )
    return blocks
