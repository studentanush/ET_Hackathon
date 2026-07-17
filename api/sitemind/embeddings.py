"""Local embeddings via fastembed (bge-small-en-v1.5, 384-dim, L2-normalized).

Zero network, zero API key. Vectors come back unit-normalized, so cosine
similarity is a plain dot product — which is what repository.vector_search uses.
"""
from __future__ import annotations

import numpy as np

from . import config

_model = None


def _get():
    global _model
    if _model is None:
        from fastembed import TextEmbedding

        _model = TextEmbedding(config.EMBED_MODEL)
    return _model


def embed(texts: list[str]) -> np.ndarray:
    """Return an (n, EMBED_DIM) float32 array of unit vectors."""
    vecs = list(_get().embed(texts))
    return np.asarray(vecs, dtype=np.float32)


def embed_one(text: str) -> np.ndarray:
    return embed([text])[0]


def to_blob(vec: np.ndarray) -> bytes:
    return np.asarray(vec, dtype=np.float32).tobytes()


def from_blob(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)
