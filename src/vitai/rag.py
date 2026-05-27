import os
import pickle
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF
from rank_bm25 import BM25Okapi

def get_rag_dir() -> Path:
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(os.getcwd())
    return base_dir / "docs"

def get_rag_context(query: str, top_k: int = 4) -> str:
    """Returns top_k chunks of text from the BM25 index that match the query."""
    rag_dir = get_rag_dir()
    index_path = rag_dir / "bm25_index.pkl"
    
    if not index_path.exists():
        _build_index(rag_dir, index_path)
    
    if not index_path.exists():
        return ""
    
    try:
        with open(index_path, "rb") as f:
            data = pickle.load(f)
            
        bm25 = data["bm25"]
        chunks = data["chunks"]
        
        tokenized_query = re.findall(r'\w+', query.lower())
        if not tokenized_query:
            return ""
            
        top_chunks = bm25.get_top_n(tokenized_query, chunks, n=top_k)
        return "\n\n".join(top_chunks)
    except Exception as e:
        print(f"Error reading RAG index: {e}")
        return ""

def _build_index(rag_dir: Path, index_path: Path) -> None:
    rag_dir.mkdir(parents=True, exist_ok=True)
    pdf_files = list(rag_dir.glob("*.pdf"))
    if not pdf_files:
        return

    print("Building RAG index. This may take a moment...")
    all_chunks = []
    for pdf_path in pdf_files:
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
                
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            current_chunk = []
            current_len = 0
            for p in paragraphs:
                words = p.split()
                if current_len + len(words) > 300 and current_chunk:
                    all_chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_len = 0
                current_chunk.append(p)
                current_len += len(words)
            if current_chunk:
                all_chunks.append(" ".join(current_chunk))
        except Exception as e:
            print(f"Failed to process {pdf_path}: {e}")

    if not all_chunks:
        return

    # Tokenize
    tokenized_chunks = [re.findall(r'\w+', chunk.lower()) for chunk in all_chunks]
    bm25 = BM25Okapi(tokenized_chunks)
    
    with open(index_path, "wb") as f:
        pickle.dump({"bm25": bm25, "chunks": all_chunks}, f)
    print("RAG index built successfully.")
