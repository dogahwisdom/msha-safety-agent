"""CLI to build the narrative retrieval index."""

from __future__ import annotations

import argparse

from src.tools.retrieval import NarrativeRetriever, RETRIEVAL_META_JSON


def main() -> None:
    parser = argparse.ArgumentParser(description="Build MSHA narrative retrieval index.")
    parser.add_argument("--batch-size", type=int, default=512)
    args = parser.parse_args()
    retriever = NarrativeRetriever()
    meta = retriever.build_index(batch_size=args.batch_size)
    print(f"Indexed {meta['total_indexed']:,} narratives using {meta['embedding_model']}")
    print(f"Wrote metadata to {RETRIEVAL_META_JSON}")


if __name__ == "__main__":
    main()
