import os
import pickle
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None


def get_rag_dir() -> Path:
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(os.getcwd())
    return base_dir / "docs"


def get_rag_context(query: str, top_k: int = 4) -> str:
    """Returns top_k chunks of text from the BM25 index that match the query."""
    if fitz is None or BM25Okapi is None:
        return ""

    rag_dir = get_rag_dir()
    if not rag_dir.exists():
        return ""

    index_path = rag_dir / "bm25_index.pkl"
    current_pdf_info = {p.name: p.stat().st_size for p in rag_dir.glob("*.pdf")}
    if not current_pdf_info:
        return ""

    if not index_path.exists():
        return build_bm25_index(rag_dir, index_path)

    try:
        with open(index_path, "rb") as f:
            data = pickle.load(f)
            if data.get("pdf_info") != current_pdf_info:
                return build_bm25_index(rag_dir, index_path)
            bm25 = data["bm25"]
            chunks = data["chunks"]
    except Exception:
        return build_bm25_index(rag_dir, index_path)

    tokenized_query = re.findall(r"\w+", query.lower())
    if not tokenized_query:
        return ""

    scores = bm25.get_scores(tokenized_query)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            results.append(chunks[idx])

    return "\n\n".join(results)


def build_bm25_index(rag_dir: Path, index_path: Path) -> str:
    if fitz is None or BM25Okapi is None:
        return ""

    pdf_files = list(rag_dir.glob("*.pdf"))
    if not pdf_files:
        return ""

    chunks = []
    pdf_info = {p.name: p.stat().st_size for p in pdf_files}

    for pdf_path in pdf_files:
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text = page.get_text()
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                page_text = " ".join(lines)
                for i in range(0, len(page_text), 500):
                    chunk = page_text[i:i + 500]
                    if len(chunk) > 50:
                        chunks.append(chunk)
        except Exception:
            continue

    if not chunks:
        return ""

    corpus = [re.findall(r"\w+", chunk.lower()) for chunk in chunks]
    bm25 = BM25Okapi(corpus)

    try:
        with open(index_path, "wb") as f:
            pickle.dump({"bm25": bm25, "chunks": chunks, "pdf_info": pdf_info}, f)
    except Exception:
        pass

    return ""
