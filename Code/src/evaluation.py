"""Small reproducible evaluation for the synthetic sample document."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .answer_generator import generate_answer
from .chunking import chunk_pages
from .pdf_processor import pages_from_strings
from .retrieval import LocalRetriever
from .sample_data import (
    SAMPLE_DOCUMENT_NAME,
    SAMPLE_EVALUATION_QUESTIONS,
    SAMPLE_PAGES,
)


@dataclass(frozen=True)
class EvaluationRow:
    question: str
    expected_pages: list[int]
    retrieved_pages: list[int]
    top_score: float
    passed_retrieval_check: bool
    answer_method: str
    citation_pages: list[int]
    passed_citation_check: bool
    notes: str


def run_sample_evaluation(prefer_semantic: bool = False) -> dict:
    pages = pages_from_strings(SAMPLE_PAGES)
    chunks = chunk_pages(pages, SAMPLE_DOCUMENT_NAME)
    retriever = LocalRetriever(prefer_semantic=prefer_semantic)
    retriever.build(chunks)

    rows: list[EvaluationRow] = []
    for item in SAMPLE_EVALUATION_QUESTIONS:
        results = retriever.query(item["question"], top_k=4)
        answer = generate_answer(item["question"], results)
        retrieved_pages = [result.chunk.page_number for result in results]
        citation_pages = [citation.page_number for citation in answer.citations]
        expected_pages = item["expected_pages"]

        if item.get("insufficient_evidence"):
            passed_retrieval = answer.method == "insufficient-evidence"
            passed_citation = citation_pages == []
            notes = "Expected insufficient evidence."
        else:
            passed_retrieval = bool(set(expected_pages) & set(retrieved_pages[:2]))
            passed_citation = bool(set(expected_pages) & set(citation_pages))
            notes = "Expected page appears in top retrieved evidence." if passed_retrieval else "Expected page was not in the top retrieved evidence."

        rows.append(
            EvaluationRow(
                question=item["question"],
                expected_pages=expected_pages,
                retrieved_pages=retrieved_pages,
                top_score=round(results[0].score, 4) if results else 0.0,
                passed_retrieval_check=passed_retrieval,
                answer_method=answer.method,
                citation_pages=citation_pages,
                passed_citation_check=passed_citation,
                notes=notes,
            )
        )

    return {
        "backend": retriever.backend,
        "warnings": retriever.warnings,
        "rows": [asdict(row) for row in rows],
        "passed": all(row.passed_retrieval_check and row.passed_citation_check for row in rows),
    }

