# -*- coding: utf-8 -*-
"""Text processing utilities for chunking extracted content."""
from typing import List


def chunk_text(text: str, max_chars: int = 2000) -> List[str]:
    """Split text into chunks by line, respecting max character limit.
    
    Args:
        text: Input text to chunk
        max_chars: Maximum characters per chunk
        
    Returns:
        List of text chunks
    """
    chunks = []
    buf = []
    count = 0
    for line in text.splitlines():
        if count + len(line) > max_chars:
            chunks.append("\n".join(buf))
            buf = []
            count = 0
        buf.append(line)
        count += len(line)
    if buf:
        chunks.append("\n".join(buf))
    return chunks
