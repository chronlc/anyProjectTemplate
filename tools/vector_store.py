# tools/vector_store.py
"""
Persistent vector DB using sqlite. Supports real embeddings via sentence-transformers
and a deterministic fallback embedding when the library is not available.

API:
  init_db()
  ingest(source_id, text, metadata=dict())
  delete_source(source_id)
  query(query_text, top_k=5) -> list of dicts {score, source_id, text, metadata}
  count()
"""

import os
import sqlite3
import json
from pathlib import Path
import math

# Attempt to import a proper embedding model
try:
    from sentence_transformers import SentenceTransformer, util
    _HAS_MODEL = True
    _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:
    _HAS_MODEL = False
    _MODEL = None

ROOT = Path(__file__).resolve().parent.parent
VECTOR_DIR = ROOT / "vector_db"
VECTOR_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = VECTOR_DIR / "vectors.sqlite"

_EMBED_DIM = 384 if _HAS_MODEL else 32  # fallback dim

# --- DB helpers ---
def _connect():
    conn = sqlite3.connect(str(DB_PATH))
    return conn

def init_db():
    conn = _connect()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS vectors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            embedding BLOB NOT NULL
        )"""
    )
    conn.commit()
    conn.close()

# --- Embedding helpers ---
def _embed_texts(texts):
    """
    Return list of float32 lists.
    Try to use sentence-transformers if available. Otherwise produce deterministic fallback vectors.
    """
    if _HAS_MODEL:
        embs = _MODEL.encode(texts, convert_to_numpy=True)
        # Ensure they are float32 lists
        return [emb.astype("float32").tolist() for emb in embs]
    # fallback: deterministic hashing -> vector
    import hashlib
    import struct
    out = []
    for t in texts:
        h = hashlib.sha256(t.encode("utf-8")).digest()
        # generate _EMBED_DIM floats from hash by repeating and interpreting bytes
        floats = []
        # expand bytes to enough bytes
        rep = h
        while len(rep) < _EMBED_DIM * 4:
            rep += hashlib.sha256(rep).digest()
        for i in range(_EMBED_DIM):
            start = i * 4
            chunk = rep[start:start+4]
            # interpret chunk as unsigned int and normalize
            val = struct.unpack(">I", chunk)[0]
            floats.append((val % 10000) / 10000.0)  # [0,1)
        # normalize to unit length
        norm = math.sqrt(sum(x*x for x in floats)) or 1.0
        floats = [x / norm for x in floats]
        out.append(floats)
    return out

def _vector_to_blob(vec):
    # store as JSON text -> easy and portable
    return json.dumps(vec).encode("utf-8")

def _blob_to_vector(blob):
    return json.loads(blob.decode("utf-8"))

# --- Public API ---
def ingest(source_id: str, content: str, metadata: dict = None):
    """
    Ingest content associated with a source_id (e.g., 'PROGRAM_FEATURES' or 'RESEARCH_GUIDELINES').
    This function removes any previous vectors for that source_id and inserts new rows.
    """
    if metadata is None:
        metadata = {}

    init_db()
    # chunk content into paragraphs (non-empty)
    chunks = [p.strip() for p in content.split("\n\n") if p.strip()]
    if not chunks:
        return 0

    vectors = _embed_texts(chunks)
    conn = _connect()
    cur = conn.cursor()
    # delete previous entries for this source_id
    cur.execute("DELETE FROM vectors WHERE source_id = ?", (source_id,))
    # insert new
    rows = 0
    for txt, vec in zip(chunks, vectors):
        cur.execute(
            "INSERT INTO vectors (source_id, content, metadata, embedding) VALUES (?, ?, ?, ?)",
            (source_id, txt, json.dumps(metadata), _vector_to_blob(vec)),
        )
        rows += 1
    conn.commit()
    conn.close()
    return rows

def delete_source(source_id: str):
    init_db()
    conn = _connect()
    conn.execute("DELETE FROM vectors WHERE source_id = ?", (source_id,))
    conn.commit()
    conn.close()

def query(query_text: str, top_k: int = 5):
    """
    Semantic query: compute embedding for query_text and return top_k closest by cosine similarity.
    Returns list of dicts: {score, source_id, content, metadata}
    """
    init_db()
    conn = _connect()
    cursor = conn.execute("SELECT id, source_id, content, metadata, embedding FROM vectors")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return []

    query_vec = _embed_texts([query_text])[0]

    # compute cosine similarity
    scored = []
    for _id, source_id, content, metadata_json, emb_blob in rows:
        emb = _blob_to_vector(emb_blob)
        # dot / (||a||*||b||)
        dot = sum(a*b for a,b in zip(query_vec, emb))
        norm_q = math.sqrt(sum(a*a for a in query_vec)) or 1.0
        norm_e = math.sqrt(sum(a*a for a in emb)) or 1.0
        score = dot / (norm_q * norm_e)
        meta = json.loads(metadata_json) if metadata_json else {}
        scored.append((score, source_id, content, meta))
    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, source_id, content, meta in scored[:top_k]:
        results.append({"score": float(score), "source_id": source_id, "content": content, "metadata": meta})
    return results

def count():
    init_db()
    conn = _connect()
    try:
        c = conn.execute("SELECT COUNT(*) FROM vectors").fetchone()[0]
    except Exception:
        c = 0
    conn.close()
    return c

# Provide a CLI entry so we can call vector_store.main() from anyProject if desired
def main():
    import argparse
    parser = argparse.ArgumentParser(prog="vector_store")
    parser.add_argument("--count", action="store_true", help="print number of vectors")
    parser.add_argument("--clear", action="store_true", help="clear the DB")
    parser.add_argument("--query", metavar="TEXT", help="query semantically")
    parser.add_argument("--ingest-source", nargs=2, metavar=("SOURCE_ID", "PATH"), help="ingest a file")
    args = parser.parse_args()
    if args.count:
        print("vectors:", count())
    elif args.clear:
        if DB_PATH.exists():
            DB_PATH.unlink()
            print("vector DB removed")
    elif args.query:
        res = query(args.query)
        print(json.dumps(res, indent=2))
    elif args.ingest_source:
        src, path = args.ingest_source
        with open(path, "r") as f:
            txt = f.read()
        n = ingest(src, txt)
        print(f"ingested {n} chunks from {path}")
    else:
        parser.print_help()
