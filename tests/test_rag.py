import json

from vitai import rag


def test_rag_index_uses_json_not_pickle(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "bm25_index.pkl").write_bytes(b"pickle")
    (docs / "bm25_index.json").write_text(
        json.dumps({"pdf_info": {}, "chunks": ["alpha beta", "gamma", "delta"], "tokenized_chunks": [["alpha", "beta"], ["gamma"], ["delta"]]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(rag, "get_rag_dir", lambda: docs)

    assert rag.get_rag_context("alpha", top_k=1) == "alpha beta"
