import re
from typing import List, Dict, Any

class ChunkingEngine:
    def __init__(self, chunk_size: int = 1000, overlap: int = 200, strategy: str = "recursive"):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.strategy = strategy

    def chunk_document(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes a list of dictionaries: [{"content": "...", "page_number": 1}]
        Returns a list of chunk dictionaries with metadata inherited.
        """
        chunks = []
        for page in pages:
            text = page.get("content", "")
            page_num = page.get("page_number", 1)
            
            if self.strategy == "semantic":
                # Mock Semantic Chunking (split by paragraph, combine until chunk_size)
                # In a real enterprise system, this uses a small NLP model or sentence boundary detection.
                paragraphs = re.split(r'\n\s*\n', text)
                current_chunk = ""
                for p in paragraphs:
                    if len(current_chunk) + len(p) > self.chunk_size and current_chunk:
                        chunks.append({"content": current_chunk.strip(), "page_number": page_num})
                        current_chunk = p
                    else:
                        current_chunk += "\n\n" + p if current_chunk else p
                if current_chunk:
                    chunks.append({"content": current_chunk.strip(), "page_number": page_num})
                    
            elif self.strategy == "parent-child":
                # Mock Parent-Child Chunking
                # The "content" is a small chunk, but we attach the full page as "parent_content"
                # For simplicity here, we just use recursive splitting and mark a parent.
                splits = self._recursive_split(text)
                for split in splits:
                    chunks.append({
                        "content": split,
                        "page_number": page_num,
                        "parent_content": text[:2000] # store top-level context
                    })
                    
            else:
                # Default: RecursiveCharacterTextSplitter-style
                splits = self._recursive_split(text)
                for split in splits:
                    chunks.append({"content": split, "page_number": page_num})
                    
        return chunks

    def _recursive_split(self, text: str) -> List[str]:
        """Simple recursive character splitter fallback."""
        if len(text) <= self.chunk_size:
            return [text]
            
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            if end < len(text):
                # Try to find a nice break point (period or newline)
                break_point = max(text.rfind('\n', start, end), text.rfind('. ', start, end))
                if break_point != -1 and break_point > start + (self.chunk_size // 2):
                    end = break_point + 1
            chunks.append(text[start:end].strip())
            start = end - self.overlap
            
        return chunks
