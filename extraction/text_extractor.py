# -*- coding: utf-8 -*-
"""Text processing utilities for chunking extracted content."""
from __future__ import annotations

from typing import List, Optional

from pdfminer.high_level import extract_text

from extraction.paddleocr_mcp_client import PaddleOCRVLClient


def chunk_text(text: str, max_chars: int = 2000) -> List[str]:
    """Split text into chunks by line, respecting max character limit.
    
    Args:
        text: Input text to chunk
        max_chars: Maximum characters per chunk
        
    Returns:
        List of text chunks
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be a positive integer")

    chunks: List[str] = []
    buf: List[str] = []
    count = 0

    for line in text.splitlines():
        if not line:
            line = ""
        if len(line) > max_chars:
            if buf:
                chunks.append("\n".join(buf))
                buf = []
                count = 0
            for i in range(0, len(line), max_chars):
                chunks.append(line[i:i + max_chars])
            continue

        if count + len(line) > max_chars and buf:
            chunks.append("\n".join(buf))
            buf = []
            count = 0

        buf.append(line)
        count += len(line)

    if buf:
        chunks.append("\n".join(buf))

    return chunks


def extract_text_from_pdf(
    pdf_path: str,
    *,
    ocr_fallback: bool = True,
    min_chars: int = 200,
) -> str:
    """Extract text from a PDF with a lightweight fallback to OCR.

    Args:
        pdf_path: Path to the PDF file.
        ocr_fallback: If True, attempt OCR when PDF text is empty/too short.
        min_chars: Minimum length to consider extraction successful.

    Returns:
        Extracted text (may be empty if both methods fail).
    """
    text = ""
    try:
        text = extract_text(pdf_path) or ""
        text = text.strip()
    except Exception as exc:
        print(f"[extract_text_from_pdf] PDFMiner error: {exc}")

    if text and len(text) >= min_chars:
        return text

    if not ocr_fallback:
        return text

    try:
        ocr_client = PaddleOCRVLClient()
        if not ocr_client.access_token:
            print("[extract_text_from_pdf] OCR token missing; skipping OCR fallback.")
            return text
        ocr_result = ocr_client.parse_document_sync(pdf_path)
        if ocr_result.get("success") and ocr_result.get("markdown"):
            return ocr_result["markdown"].strip()
    except Exception as exc:
        print(f"[extract_text_from_pdf] OCR fallback failed: {exc}")

    return text
