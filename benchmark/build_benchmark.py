"""Build benchmark questions and reference answers before any system runs on them (Step 7)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.data.config import ACCIDENTS_CLEAN_CSV
from src.tools.retrieval import NarrativeRetriever
from src.tools.trends import PARTIAL_CALENDAR_YEAR, TrendAnalyzer

BENCHMARK_DIR = Path(__file__).resolve().parents[1] / "benchmark"
QUESTIONS_PATH = BENCHMARK_DIR / "questions.json"
REFERENCES_PATH = BENCHMARK_DIR / "reference_answers.json"


def _classification_questions(frame: pd.DataFrame) -> list[dict]:
    sample = frame.sample(20, random_state=42)
    items = []
    for idx, row in sample.iterrows():
        qid = f"CLS-{len(items)+1:02d}"
        question = (
            "Predict injury degree for: "
            f"subunit_cd={row['SUBUNIT_CD']}, classification_cd={row['CLASSIFICATION_CD']}, "
            f"occupation_cd={row['OCCUPATION_CD']}, activity_cd={row['ACTIVITY_CD']}, "
            f"injury_source_cd={row['INJURY_SOURCE_CD']}, nature_injury_cd={row['NATURE_INJURY_CD']}, "
            f"inj_body_part_cd={row['INJ_BODY_PART_CD']}, mining_equip_cd={row['MINING_EQUIP_CD']}, "
            f"coal_metal_ind={row['COAL_METAL_IND']}, accident_type_cd={row['ACCIDENT_TYPE_CD']}."
        )
        items.append(
            {
                "id": qid,
                "category": "classification",
                "question": question,
                "expected_tools": ["classify_injury_risk"],
                "reference": {
                    "type": "degree_code",
                    "value": str(row["DEGREE_INJURY_CD"]).strip().zfill(2),
                    "document_no": str(row["DOCUMENT_NO"]),
                },
            }
        )
    return items


def _trend_questions(analyzer: TrendAnalyzer) -> list[dict]:
    specs = [
        ("TRD-01", "How many MSHA fatalities (degree code 01) occurred in 2015?", {"degree_code": "01"}, 2015),
        ("TRD-02", "How many MSHA fatalities occurred in 2020?", {"degree_code": "01"}, 2020),
        ("TRD-03", "How many coal mine injuries occurred in Texas in 2022?", {"coal_metal": "C", "state": "TX"}, 2022),
        ("TRD-04", "How many handling-of-materials injuries occurred in 2019?", {"classification": "HANDLING OF MATERIALS"}, 2019),
        ("TRD-05", "How many roof bolter injuries occurred in 2018?", {"occupation": "Roof bolter"}, 2018),
        ("TRD-06", "How many injuries occurred at metal/non-metal mines in Nevada in 2021?", {"coal_metal": "M", "state": "NV"}, 2021),
        ("TRD-07", "How many degree-code-03 injuries occurred in 2016?", {"degree_code": "03"}, 2016),
        ("TRD-08", "How many degree-code-06 injuries occurred in 2014?", {"degree_code": "06"}, 2014),
        ("TRD-09", "How many powered haulage classification injuries occurred in 2017?", {"classification": "POWERED HAULAGE"}, 2017),
        ("TRD-10", "How many fall of roof classification injuries occurred in 2013?", {"classification": "FALL OF ROOF OR BACK"}, 2013),
    ]
    items = []
    for qid, question, filters, year in specs:
        count = int(
            analyzer.count_by_year(filters).data.loc[
                lambda d: d["CAL_YR"] == year, "injury_count"
            ].iloc[0]
        )
        items.append(
            {
                "id": qid,
                "category": "trend",
                "question": question,
                "expected_tools": ["analyze_trends"],
                "reference": {"type": "count", "year": year, "value": count, "filters": filters},
            }
        )
    # Period comparisons
    comp_specs = [
        ("TRD-11", "Compare coal mine injury counts between 2010-2014 and 2015-2019.", {"coal_metal": "C"}, (2010, 2014), (2015, 2019)),
        ("TRD-12", "Compare fatality counts between 2005-2009 and 2010-2014.", {"degree_code": "01"}, (2005, 2009), (2010, 2014)),
    ]
    for qid, question, filters, pa, pb in comp_specs:
        result = analyzer.compare_periods(pa, pb, filters)
        items.append(
            {
                "id": qid,
                "category": "trend",
                "question": question,
                "expected_tools": ["analyze_trends"],
                "reference": {
                    "type": "period_compare",
                    "period_a": pa,
                    "period_b": pb,
                    "counts": result.data.to_dict(orient="records"),
                    "filters": filters,
                },
            }
        )
    # Fill remaining trend slots with year-count variants
    idx = 13
    for year in range(2010, 2021):
        if len(items) >= 20:
            break
        qid = f"TRD-{idx:02d}"
        idx += 1
        filters = {"degree_code": "02"}
        count = int(
            analyzer.count_by_year(filters).data.loc[
                lambda d: d["CAL_YR"] == year, "injury_count"
            ].iloc[0]
        )
        items.append(
            {
                "id": qid,
                "category": "trend",
                "question": f"How many permanent disability injuries (degree code 02) occurred in {year}?",
                "expected_tools": ["analyze_trends"],
                "reference": {"type": "count", "year": year, "value": count, "filters": filters},
            }
        )
    return items[:20]


def _case_questions(retriever: NarrativeRetriever, frame: pd.DataFrame) -> list[dict]:
    seed_queries = [
        ("CASE-01", "roof fall underground coal miner pinned"),
        ("CASE-02", "electrical shock continuous miner cable"),
        ("CASE-03", "haul truck backed into rib operator"),
        ("CASE-04", "methane ignition explosion underground"),
        ("CASE-05", "ladder fall surface mine maintenance"),
        ("CASE-06", "conveyor belt entanglement amputation"),
        ("CASE-07", "roof bolter hit by falling rock"),
        ("CASE-08", "dozer rollover surface coal mine"),
        ("CASE-09", "welding burn hand injury"),
        ("CASE-10", "slip fall icy walkway surface mine"),
    ]
    items = []
    for qid, query in seed_queries:
        hits = retriever.search(query, top_k=5)
        items.append(
            {
                "id": qid,
                "category": "case_grounded",
                "question": f"Find historical MSHA incidents similar to: {query}",
                "expected_tools": ["search_narratives"],
                "reference": {
                    "type": "document_set",
                    "query": query,
                    "document_numbers": [h.document_no for h in hits],
                    "top_narrative": hits[0].narrative if hits else "",
                },
            }
        )
    # Add ten more from high-signal narratives in data
    sample = frame[frame["NARRATIVE"].str.len() > 80].sample(10, random_state=7)
    for _, row in sample.iterrows():
        qid = f"CASE-{len(items)+1:02d}"
        snippet = str(row["NARRATIVE"])[:80]
        query = snippet
        hits = retriever.search(query, top_k=5)
        items.append(
            {
                "id": qid,
                "category": "case_grounded",
                "question": f"Find incidents similar to this narrative snippet: {snippet}",
                "expected_tools": ["search_narratives"],
                "reference": {
                    "type": "document_set",
                    "query": query,
                    "document_numbers": [h.document_no for h in hits],
                    "must_include": str(row["DOCUMENT_NO"]),
                },
            }
        )
    return items[:20]


def build_benchmark() -> dict:
    frame = pd.read_csv(ACCIDENTS_CLEAN_CSV, low_memory=False)
    analyzer = TrendAnalyzer(frame)
    retriever = NarrativeRetriever()
    questions = (
        _classification_questions(frame)
        + _trend_questions(analyzer)
        + _case_questions(retriever, frame)
    )
    payload = {
        "version": 1,
        "total_questions": len(questions),
        "category_counts": {
            "classification": sum(1 for q in questions if q["category"] == "classification"),
            "trend": sum(1 for q in questions if q["category"] == "trend"),
            "case_grounded": sum(1 for q in questions if q["category"] == "case_grounded"),
        },
        "notes": [
            f"Reference answers derived from cleaned data and tools, not from agent outputs.",
            f"Partial year {PARTIAL_CALENDAR_YEAR} excluded from trend count references where applicable.",
        ],
        "questions": questions,
    }
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    with QUESTIONS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    references = {q["id"]: q["reference"] for q in questions}
    with REFERENCES_PATH.open("w", encoding="utf-8") as handle:
        json.dump(references, handle, indent=2, ensure_ascii=False)
    return payload


if __name__ == "__main__":
    result = build_benchmark()
    print(f"Wrote {result['total_questions']} questions to {QUESTIONS_PATH}")
