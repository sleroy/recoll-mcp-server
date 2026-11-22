#!/usr/bin/env python3
"""Read-only MCP access to a specific Recoll index."""

import os
from pathlib import Path
from urllib.parse import unquote, urlsplit

from mcp.server.fastmcp import FastMCP
from recoll import recoll, rclextract


CONFIG_DIR = Path(os.environ.get("RECOLL_CONFDIR", "~/.recoll")).expanduser().resolve()
ALLOWED_ROOT = Path(os.environ.get("RECOLL_ALLOWED_ROOT", "~")).expanduser().resolve()
server = FastMCP("recoll-search")


def _inside_allowed_root(doc) -> bool:
    parsed = urlsplit(doc.url)
    if parsed.scheme != "file":
        return False
    path = Path(unquote(parsed.path)).resolve()
    return path.is_relative_to(ALLOWED_ROOT)


def _connection():
    return recoll.connect(confdir=str(CONFIG_DIR))


@server.tool()
def search_filesystem(query: str, max_results: int = 10) -> dict:
    """Search indexed documents with Recoll syntax. Returns paths and short previews.

    Use AND, OR, quoted phrases, and wildcards. Search only covers the configured
    Recoll index and the allowed root directory. No files are changed.
    """
    if not query or len(query) > 500:
        raise ValueError("query must be between 1 and 500 characters")
    limit = max(1, min(int(max_results), 20))
    db = _connection()
    cursor = db.query()
    total = cursor.execute(query)
    results = []
    for _ in range(min(total, 200)):
        doc = cursor.fetchone()
        if _inside_allowed_root(doc):
            results.append({
                "document_id": doc.rcludi,
                "filename": doc.filename,
                "url": doc.url,
                "mimetype": doc.mimetype,
                "preview": (doc.abstract or "")[:500],
            })
        if len(results) >= limit:
            break
    return {"query": query, "total_results": total, "results": results}


@server.tool()
def get_document_content(document_id: str, max_chars: int = 12000) -> dict:
    """Extract bounded text from a document_id returned by search_filesystem.

    Handles PDFs and Office documents through Recoll's own extractors. The
    document must belong to the configured index and allowed root directory.
    """
    if not document_id or len(document_id) > 2000:
        raise ValueError("invalid document_id")
    limit = max(1, min(int(max_chars), 20000))
    db = _connection()
    doc = db.getDoc(document_id)
    if doc is None or not _inside_allowed_root(doc):
        raise ValueError("document is outside the allowed index")
    parsed = urlsplit(doc.url)
    path = Path(unquote(parsed.path)).resolve()
    if path.stat().st_size > 25_000_000:
        raise ValueError("source file is too large for MCP text extraction")
    extracted = rclextract.Extractor(doc).textextract(doc.ipath)
    content = extracted.text or ""
    return {
        "document_id": document_id,
        "url": doc.url,
        "content": content[:limit],
        "truncated": len(content) > limit,
    }


if __name__ == "__main__":
    server.run(transport="stdio")
