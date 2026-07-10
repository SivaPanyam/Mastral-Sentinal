import os
from typing import List, Dict, Any, Iterator
from pypdf import PdfReader

class DocumentChunk(dict):
    """Represents a chunk of extracted text with metadata."""
    pass

class BaseLoader:
    def __init__(self, source_path: str):
        self.source_path = source_path
        self.metadata = {"source_url": source_path}

    def load(self) -> Iterator[Dict[str, Any]]:
        """Yields dictionaries containing 'content' and 'page_number' (if applicable)."""
        raise NotImplementedError

class TXTLoader(BaseLoader):
    def load(self) -> Iterator[Dict[str, Any]]:
        with open(self.source_path, "r", encoding="utf-8") as f:
            content = f.read()
        yield {"content": content, "page_number": 1}

class MarkdownLoader(TXTLoader):
    # For now, behaves like TXTLoader. We can add markdown-specific section splitting later.
    pass

class PDFLoader(BaseLoader):
    def load(self) -> Iterator[Dict[str, Any]]:
        reader = PdfReader(self.source_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                yield {"content": text, "page_number": i + 1}

class HTMLLoader(BaseLoader):
    def load(self) -> Iterator[Dict[str, Any]]:
        # Extremely basic HTML stripper for now, relying on standard library
        import re
        with open(self.source_path, "r", encoding="utf-8") as f:
            html = f.read()
        # Strip script/style
        text = re.sub(r'<(script|style).*?>.*?</\1>', '', html, flags=re.DOTALL)
        # Strip tags
        text = re.sub(r'<[^>]+>', ' ', text)
        yield {"content": text, "page_number": 1}

import json
import urllib.request
from urllib.parse import urlparse
import glob

# --- Newly Implemented Loaders ---

class JSONLoader(BaseLoader):
    def load(self) -> Iterator[Dict[str, Any]]:
        with open(self.source_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Basic flattening of JSON
            yield {"content": json.dumps(data, indent=2), "page_number": 1}

class DocumentationWebsiteLoader(BaseLoader):
    def load(self) -> Iterator[Dict[str, Any]]:
        # This acts on a URL passed as source_path
        if not self.source_path.startswith("http"):
            raise ValueError("DocumentationWebsiteLoader requires a valid HTTP URL.")
            
        try:
            req = urllib.request.Request(self.source_path, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
            
            import re
            text = re.sub(r'<(script|style).*?>.*?</\1>', '', html, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            yield {"content": text, "page_number": 1}
        except Exception as e:
            yield {"content": f"Failed to scrape documentation: {e}", "page_number": 1}

class GitHubLoader(BaseLoader):
    def load(self) -> Iterator[Dict[str, Any]]:
        # This acts on a GitHub API URL or raw github content
        # For simplicity, if passed a raw githubusercontent URL, fetch it.
        # Real enterprise would use PyGithub to traverse repos.
        if "raw.githubusercontent.com" in self.source_path:
            req = urllib.request.Request(self.source_path, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                content = response.read().decode('utf-8')
            yield {"content": content, "page_number": 1}
        else:
            yield {"content": "GitHubLoader currently expects raw githubusercontent URLs for single file ingestion.", "page_number": 1}

class LocalFolderLoader(BaseLoader):
    def load(self) -> Iterator[Dict[str, Any]]:
        if not os.path.isdir(self.source_path):
            raise ValueError("LocalFolderLoader requires a valid directory path.")
            
        files = glob.glob(os.path.join(self.source_path, "**", "*.*"), recursive=True)
        for i, file_path in enumerate(files):
            if os.path.isfile(file_path):
                ext = file_path.split(".")[-1].lower()
                if ext in ["txt", "md", "json", "html"]:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        yield {"content": f.read(), "page_number": i + 1, "metadata": {"file": file_path}}

# --- Scaffolded Future Loaders ---

class ConfluenceLoader(BaseLoader):
    def load(self) -> Iterator[Dict[str, Any]]:
        raise NotImplementedError("ConfluenceLoader is scaffolded for future enterprise integration.")

class SharePointLoader(BaseLoader):
    def load(self) -> Iterator[Dict[str, Any]]:
        raise NotImplementedError("SharePointLoader is scaffolded for future enterprise integration.")

class S3Loader(BaseLoader):
    def load(self) -> Iterator[Dict[str, Any]]:
        raise NotImplementedError("S3Loader is scaffolded for future enterprise integration.")

class GoogleDriveLoader(BaseLoader):
    def load(self) -> Iterator[Dict[str, Any]]:
        raise NotImplementedError("GoogleDriveLoader is scaffolded for future enterprise integration.")

class AzureBlobLoader(BaseLoader):
    def load(self) -> Iterator[Dict[str, Any]]:
        raise NotImplementedError("AzureBlobLoader is scaffolded for future enterprise integration.")

def get_loader(source_path: str) -> BaseLoader:
    if source_path.startswith("http"):
        if "github" in source_path:
            return GitHubLoader(source_path)
        return DocumentationWebsiteLoader(source_path)
        
    if os.path.isdir(source_path):
        return LocalFolderLoader(source_path)
        
    ext = source_path.split(".")[-1].lower()
    if ext == "pdf":
        return PDFLoader(source_path)
    elif ext == "md":
        return MarkdownLoader(source_path)
    elif ext in ["html", "htm"]:
        return HTMLLoader(source_path)
    elif ext == "txt":
        return TXTLoader(source_path)
    elif ext == "json":
        return JSONLoader(source_path)
    else:
        # Fallback to TXT
        return TXTLoader(source_path)
