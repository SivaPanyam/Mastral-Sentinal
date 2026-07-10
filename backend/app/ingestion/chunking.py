import re
from typing import List

def clean_text(text: str) -> str:
    """Normalizes whitespace and removes null characters."""
    if not text:
        return ""
    text = text.replace('\x00', '')
    # Normalize multiple whitespaces, but preserve paragraph breaks
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Splits raw text into overlapping chunks of a specific size."""
    text = clean_text(text)
    chunks = []
    start = 0
    text_len = len(text)
    
    if text_len == 0:
        return []
        
    while start < text_len:
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= text_len:
            break
        start = end - overlap
        
    return deduplicate_chunks(chunks)

def deduplicate_chunks(chunks: List[str]) -> List[str]:
    """Removes duplicate chunks while preserving order."""
    seen = set()
    result = []
    for chunk in chunks:
        if chunk not in seen:
            seen.add(chunk)
            result.append(chunk)
    return result
