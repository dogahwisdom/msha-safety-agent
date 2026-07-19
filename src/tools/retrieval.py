"""Semantic retrieval over MSHA injury narratives (Step 4).

Embedding model: sentence-transformers/all-MiniLM-L6-v2
- Widely used general-purpose sentence embedding (384 dimensions).
- Suitable for short occupational safety text; MSHA narratives are capped at 384 characters.
- Documented choice for reproducibility; not fine-tuned on mining data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
import pandas as pd
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from src.data.config import ACCIDENTS_CLEAN_CSV, PROCESSED_DIR

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_DIR = PROCESSED_DIR / "chroma_narratives"
COLLECTION_NAME = "msha_injury_narratives"
RETRIEVAL_META_JSON = PROCESSED_DIR / "retrieval_index_meta.json"

METADATA_COLUMNS = [
    "DOCUMENT_NO",
    "MINE_ID",
    "CAL_YR",
    "OCCUPATION",
    "NATURE_INJURY",
    "CLASSIFICATION",
    "DEGREE_INJURY",
    "STATE",
]


@dataclass
class RetrievedIncident:
    document_no: str
    narrative: str
    score: float
    metadata: dict[str, Any]


class NarrativeRetriever:
    """Build and query a vector index over injury narratives."""

    def __init__(
        self,
        model_name: str = EMBEDDING_MODEL_NAME,
        persist_dir: Path = CHROMA_DIR,
    ) -> None:
        self.model_name = model_name
        self.persist_dir = persist_dir
        self.model = SentenceTransformer(model_name)
        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def _embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return vectors.tolist()

    def build_index(
        self,
        frame: pd.DataFrame | None = None,
        batch_size: int = 512,
    ) -> dict[str, Any]:
        """Embed narratives and store in ChromaDB. One document per MSHA record."""
        if frame is None:
            frame = pd.read_csv(ACCIDENTS_CLEAN_CSV, low_memory=False)
        frame = frame.dropna(subset=["NARRATIVE", "DOCUMENT_NO"]).copy()
        existing = set(self.collection.get(include=[])["ids"])
        to_add = frame[~frame["DOCUMENT_NO"].astype(str).isin(existing)]
        added = 0
        for start in range(0, len(to_add), batch_size):
            batch = to_add.iloc[start : start + batch_size]
            ids = batch["DOCUMENT_NO"].astype(str).tolist()
            documents = batch["NARRATIVE"].astype(str).tolist()
            metadatas = [
                {col: str(row[col]) if col in row and pd.notna(row[col]) else "" for col in METADATA_COLUMNS}
                for _, row in batch.iterrows()
            ]
            embeddings = self._embed(documents)
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
            )
            added += len(ids)
        meta = {
            "embedding_model": self.model_name,
            "collection": COLLECTION_NAME,
            "total_indexed": self.collection.count(),
            "newly_added": added,
            "persist_dir": str(self.persist_dir),
        }
        RETRIEVAL_META_JSON.parent.mkdir(parents=True, exist_ok=True)
        with RETRIEVAL_META_JSON.open("w", encoding="utf-8") as handle:
            json.dump(meta, handle, indent=2)
        return meta

    def search(self, query: str, top_k: int = 5) -> list[RetrievedIncident]:
        """Return top-k narratives by cosine similarity."""
        embedding = self._embed([query])[0]
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        incidents: list[RetrievedIncident] = []
        for doc_id, narrative, metadata, distance in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            # Chroma cosine distance: lower is more similar. Convert to similarity score.
            score = 1.0 - float(distance)
            incidents.append(
                RetrievedIncident(
                    document_no=str(doc_id),
                    narrative=str(narrative),
                    score=round(score, 4),
                    metadata=dict(metadata),
                )
            )
        return incidents

    def search_as_dicts(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return [
            {
                "document_no": item.document_no,
                "narrative": item.narrative,
                "score": item.score,
                "metadata": item.metadata,
            }
            for item in self.search(query, top_k=top_k)
        ]
