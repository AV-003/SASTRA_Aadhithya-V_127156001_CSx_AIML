"""Streamlit app for the AUTOSAR HLD Document Analysis Assistant."""

from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import difflib
import sys

from src.answer_generator import generate_answer
from src.architecture_extractor import extract_architecture, report_to_csv, report_to_json
from src.chunking import chunk_pages
from src.evaluation import run_sample_evaluation
from src.pdf_processor import PdfProcessingError, extract_pdf_bytes
from src.retrieval import LocalRetriever


BASE_DIR = Path(__file__).resolve().parent
SAMPLE_PDF = BASE_DIR / "data" / "sample_documents" / "vehicle_lighting_hld_sample.pdf"


def main() -> None:
    try:
        import streamlit as st
    except ImportError:
        print(
            "Streamlit is not installed. Run: python -m pip install -r requirements.txt"
        )
        sys.exit(1)

    st.set_page_config(
        page_title="AUTOSAR HLD Analysis Assistant",
        page_icon="HLD",
        layout="wide",
    )
    _apply_style(st)
    _init_state(st)

    st.title("AUTOSAR HLD Document Analysis Assistant")
    st.caption(
        "Local PDF extraction, retrieval-grounded question answering, citations, "
        "and architecture facts for academic HLD analysis."
    )
    st.warning(
        "AI-generated findings require qualified human review. This prototype is "
        "not certified, not production-ready, and not compliant evidence for any "
        "automotive standard."
    )

    with st.sidebar:
        st.header("Run Settings")
        prefer_semantic = st.checkbox(
            "Try semantic embeddings if installed",
            value=False,
            help="Falls back to TF-IDF if sentence-transformers or the model is unavailable.",
        )
        chunk_size = st.slider("Chunk size (words)", 80, 260, 140, step=20)
        overlap = st.slider("Chunk overlap (words)", 10, 80, 35, step=5)
        top_k = st.slider("Retrieved excerpts", 2, 8, 4)
        if st.button("Reset current document"):
            _reset_document(st)
            st.success("Current document and index were cleared.")

        if st.session_state.get("retriever"):
            st.divider()
            st.metric("Retrieval backend", st.session_state["retriever"].backend)
            st.metric("Chunks", len(st.session_state.get("chunks", [])))

    tabs = st.tabs(
        [
            "Document",
            "Ask",
            "Architecture",
            "Evaluation",
            "Compare",
            "Limitations",
        ]
    )

    with tabs[0]:
        _document_tab(st, prefer_semantic, chunk_size, overlap)

    with tabs[1]:
        _ask_tab(st, top_k)

    with tabs[2]:
        _architecture_tab(st)

    with tabs[3]:
        _evaluation_tab(st)

    with tabs[4]:
        _compare_tab(st)

    with tabs[5]:
        _limitations_tab(st)


def _init_state(st) -> None:
    defaults = {
        "extraction": None,
        "chunks": [],
        "retriever": None,
        "document_hash": None,
        "architecture_report": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _reset_document(st) -> None:
    st.session_state["extraction"] = None
    st.session_state["chunks"] = []
    st.session_state["retriever"] = None
    st.session_state["document_hash"] = None
    st.session_state["architecture_report"] = None


def _document_tab(st, prefer_semantic: bool, chunk_size: int, overlap: int) -> None:
    col_upload, col_sample = st.columns([2, 1])
    with col_upload:
        uploaded = st.file_uploader("Upload automotive HLD PDF", type=["pdf"])
        if uploaded is not None:
            file_bytes = uploaded.getvalue()
            if st.button("Process uploaded PDF", type="primary"):
                _process_document(
                    st,
                    file_bytes=file_bytes,
                    document_name=uploaded.name,
                    prefer_semantic=prefer_semantic,
                    chunk_size=chunk_size,
                    overlap=overlap,
                )

    with col_sample:
        st.subheader("Demo Document")
        st.write("Synthetic Vehicle Lighting Controller HLD")
        if st.button("Load sample PDF"):
            if not SAMPLE_PDF.exists():
                st.error("Sample PDF is missing. Run scripts/create_sample_pdf.py first.")
            else:
                _process_document(
                    st,
                    file_bytes=SAMPLE_PDF.read_bytes(),
                    document_name=SAMPLE_PDF.name,
                    prefer_semantic=prefer_semantic,
                    chunk_size=chunk_size,
                    overlap=overlap,
                )

    extraction = st.session_state.get("extraction")
    if not extraction:
        st.info("No document is currently processed.")
        return

    st.divider()
    metric_cols = st.columns(4)
    metric_cols[0].metric("Document", extraction.document_name)
    metric_cols[1].metric("Pages", extraction.page_count)
    metric_cols[2].metric("Text characters", extraction.extracted_character_count)
    metric_cols[3].metric("Extractor", extraction.extractor)

    if extraction.warnings:
        for warning in extraction.warnings:
            st.warning(warning)

    st.subheader("Extracted Text Preview")
    st.text_area("Preview", extraction.text_preview, height=220, label_visibility="collapsed")


def _process_document(
    st,
    file_bytes: bytes,
    document_name: str,
    prefer_semantic: bool,
    chunk_size: int,
    overlap: int,
) -> None:
    document_hash = sha256(document_name.encode("utf-8") + file_bytes).hexdigest()
    try:
        extraction = extract_pdf_bytes(file_bytes, document_name)
        chunks = chunk_pages(
            extraction.pages,
            extraction.document_name,
            chunk_size_words=chunk_size,
            overlap_words=overlap,
        )
        if not chunks:
            st.error(
                "The document was read, but no searchable text chunks were created. "
                "It may be scanned or empty."
            )
            return
        retriever = LocalRetriever(prefer_semantic=prefer_semantic)
        retriever.build(chunks)
        architecture_report = extract_architecture(chunks)
    except PdfProcessingError as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        st.error(f"Document processing failed: {exc}")
        return

    st.session_state["extraction"] = extraction
    st.session_state["chunks"] = chunks
    st.session_state["retriever"] = retriever
    st.session_state["document_hash"] = document_hash
    st.session_state["architecture_report"] = architecture_report
    st.success("Document processed and retrieval index refreshed.")

    for warning in retriever.warnings:
        st.warning(warning)


def _ask_tab(st, top_k: int) -> None:
    retriever = st.session_state.get("retriever")
    if retriever is None:
        st.info("Process a document before asking questions.")
        return

    question = st.text_input(
        "Question",
        placeholder="Example: What signal reports the lamp status?",
    )
    if st.button("Ask document", type="primary") and question.strip():
        results = retriever.query(question, top_k=top_k)
        answer = generate_answer(question, results)

        st.subheader("Answer")
        st.write(answer.text)
        st.caption(f"Answer method: {answer.method}")
        for warning in answer.warnings:
            st.warning(warning)

        if answer.citations:
            st.subheader("Supporting Sources")
            for citation in answer.citations:
                label = (
                    f"{citation.document_name}, page {citation.page_number} "
                    f"(score {citation.score:.3f})"
                )
                with st.expander(label):
                    st.write(citation.excerpt)
        else:
            st.info("No citations are shown because evidence was insufficient.")


def _architecture_tab(st) -> None:
    report = st.session_state.get("architecture_report")
    if not report:
        st.info("Process a document to generate the architecture report.")
        return

    st.subheader("Structured Architecture Extraction")
    for category, items in report.items():
        st.markdown(f"**{category.replace('_', ' ').title()}**")
        if not items:
            st.caption("No items detected.")
            continue
        rows = [asdict(item) for item in items]
        st.dataframe(rows, use_container_width=True, hide_index=True)

    col_json, col_csv = st.columns(2)
    col_json.download_button(
        "Download JSON",
        data=report_to_json(report),
        file_name="architecture_report.json",
        mime="application/json",
    )
    col_csv.download_button(
        "Download CSV",
        data=report_to_csv(report),
        file_name="architecture_report.csv",
        mime="text/csv",
    )


def _evaluation_tab(st) -> None:
    st.subheader("Synthetic Sample Evaluation")
    if st.button("Run sample evaluation"):
        result = run_sample_evaluation(prefer_semantic=False)
        st.metric("Evaluation backend", result["backend"])
        st.metric("Overall checks", "PASS" if result["passed"] else "REVIEW")
        for warning in result["warnings"]:
            st.warning(warning)
        st.dataframe(result["rows"], use_container_width=True, hide_index=True)

    st.caption(
        "These checks verify retrieval and citation behavior on the synthetic sample. "
        "They are not model-quality benchmarks for real automotive documents."
    )


def _compare_tab(st) -> None:
    st.subheader("Preliminary Document Comparison")
    st.caption("Comparison output is a review aid and requires engineering review.")

    left_file = st.file_uploader("Baseline PDF", type=["pdf"], key="compare_left")
    right_file = st.file_uploader("Updated PDF", type=["pdf"], key="compare_right")
    if st.button("Compare documents"):
        if left_file is None or right_file is None:
            st.error("Upload both PDFs before comparing.")
            return
        try:
            left = extract_pdf_bytes(left_file.getvalue(), left_file.name)
            right = extract_pdf_bytes(right_file.getvalue(), right_file.name)
        except Exception as exc:
            st.error(f"Comparison failed: {exc}")
            return

        left_lines = _meaningful_lines("\n".join(page.text for page in left.pages))
        right_lines = _meaningful_lines("\n".join(page.text for page in right.pages))
        diff = list(
            difflib.unified_diff(
                left_lines,
                right_lines,
                fromfile=left.document_name,
                tofile=right.document_name,
                lineterm="",
                n=2,
            )
        )
        if diff:
            st.code("\n".join(diff[:300]), language="diff")
        else:
            st.success("No line-level text differences were detected.")


def _limitations_tab(st) -> None:
    st.markdown(
        """
**Current safeguards**

- Answers are grounded in retrieved excerpts from the active document.
- Citations include document name and page number.
- Uploaded document text is treated as evidence, not as application instructions.
- Reset clears the active extraction, chunks, retriever, and architecture report.
- External LLM calls require explicit environment configuration.

**Known limitations**

- OCR is not included, so scanned PDFs need preprocessing.
- TF-IDF fallback is lexical retrieval, not semantic understanding.
- Architecture extraction uses simple pattern matching and needs human review.
- Document comparison is preliminary and line-based.
"""
    )


def _meaningful_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if len(line.strip()) > 20]


def _apply_style(st) -> None:
    st.markdown(
        """
<style>
div[data-testid="stMetric"] {
    border-left: 3px solid #18745a;
    padding: 0.4rem 0.6rem;
    background: #f7faf9;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 0.25rem;
}
</style>
""",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

