"""Simple architecture fact extraction from retrieved document chunks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
import io
import json
import re
from typing import Iterable

from .chunking import DocumentChunk


@dataclass(frozen=True)
class ArchitectureItem:
    category: str
    name: str
    fact_type: str
    document_name: str
    page_number: int
    excerpt: str


KEYWORDS = {
    "components": ["component", "software component", "application component"],
    "interfaces": ["interface", "port", "signal"],
    "dependencies": ["depends on", "dependency", "requires", "accepting"],
    "functional_flows": ["functional flow", "flow", "reads", "evaluates", "publishes"],
}


def extract_architecture(chunks: Iterable[DocumentChunk]) -> dict[str, list[ArchitectureItem]]:
    buckets: dict[str, list[ArchitectureItem]] = {
        "components": [],
        "interfaces": [],
        "dependencies": [],
        "functional_flows": [],
        "possible_interpretations": [],
    }
    seen: set[tuple[str, str, int]] = set()

    for chunk in chunks:
        for sentence in _candidate_sentences(chunk.text):
            lower = sentence.lower()
            matched = False
            for category, keywords in KEYWORDS.items():
                if any(keyword in lower for keyword in keywords):
                    name = _name_for_sentence(category, sentence)
                    item = ArchitectureItem(
                        category=category,
                        name=name,
                        fact_type="explicit",
                        document_name=chunk.document_name,
                        page_number=chunk.page_number,
                        excerpt=sentence,
                    )
                    _append_unique(buckets[category], item, seen)
                    matched = True
            if not matched and _looks_like_interpretation(sentence):
                item = ArchitectureItem(
                    category="possible_interpretations",
                    name="Possible architecture interpretation",
                    fact_type="interpretation",
                    document_name=chunk.document_name,
                    page_number=chunk.page_number,
                    excerpt=sentence,
                )
                _append_unique(buckets["possible_interpretations"], item, seen)

    return buckets


def report_to_json(report: dict[str, list[ArchitectureItem]]) -> str:
    serializable = {
        category: [asdict(item) for item in items] for category, items in report.items()
    }
    return json.dumps(serializable, indent=2)


def report_to_csv(report: dict[str, list[ArchitectureItem]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "category",
            "name",
            "fact_type",
            "document_name",
            "page_number",
            "excerpt",
        ],
    )
    writer.writeheader()
    for items in report.values():
        for item in items:
            writer.writerow(asdict(item))
    return output.getvalue()


def _candidate_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [part.strip(" -0123456789.") for part in parts if len(part.strip()) > 20]


def _name_for_sentence(category: str, sentence: str) -> str:
    if category == "components":
        patterns = [
            r"\b([A-Z][A-Za-z0-9_ ]{2,70}?)\s+(?:application\s+)?component\b",
            r"\bcomponent\s+named\s+([A-Z][A-Za-z0-9_ ]{2,70})\b",
            r"\b([A-Z][A-Za-z0-9_ ]{2,70}?)\s+software component\b",
        ]
    elif category == "interfaces":
        patterns = [
            r"\b(?:signal|port|interface)\s+([A-Z][A-Za-z0-9_]{2,70})\b",
            r"\b([A-Z][A-Za-z0-9_]{2,70})\s+(?:signal|port|interface)\b",
        ]
    else:
        patterns = []

    for pattern in patterns:
        match = re.search(pattern, sentence)
        if match:
            return " ".join(match.group(1).split())
    return sentence[:80].strip()


def _looks_like_interpretation(sentence: str) -> bool:
    lower = sentence.lower()
    return any(term in lower for term in ["so that", "therefore", "implies", "suggests"])


def _append_unique(
    bucket: list[ArchitectureItem],
    item: ArchitectureItem,
    seen: set[tuple[str, str, int]],
) -> None:
    key = (item.category, item.excerpt.lower(), item.page_number)
    if key not in seen:
        bucket.append(item)
        seen.add(key)

