# Technical Report Outline

1. Title Page
   - Project name
   - Student name
   - Course or panel details
   - Date

2. Abstract
   - Short summary of the HLD analysis problem and prototype solution.

3. Introduction
   - Background on automotive HLD documents.
   - Need for traceable document question answering.

4. Problem Statement
   - Difficulty of manually locating components, interfaces, dependencies, and
     design decisions in large PDFs.

5. Objectives
   - PDF upload and extraction.
   - Local retrieval.
   - Grounded QA with citations.
   - Architecture report export.
   - Responsible AI safeguards.

6. System Design
   - Streamlit UI.
   - PDF processor.
   - Chunker.
   - Retriever.
   - Answer generator.
   - Architecture extractor.

7. Methodology
   - Text extraction.
   - Page-preserving chunking.
   - TF-IDF fallback retrieval.
   - Optional semantic embedding path.
   - Evidence-based answer generation.

8. Implementation
   - Python modules and responsibilities.
   - Error handling.
   - Local data handling.

9. Testing and Evaluation
   - Unit tests.
   - Synthetic evaluation questions.
   - Insufficient-evidence check.
   - Manual demo observations.

10. Responsible AI and Ethics
    - Grounding.
    - Citations.
    - Uncertainty.
    - Human review.
    - Local-first data handling.

11. Results
    - Summarize actual test output.
    - Include screenshots if needed.

12. Limitations
    - No OCR.
    - Pattern-based extraction.
    - TF-IDF limitations.
    - Preliminary comparison.

13. Future Work
    - OCR.
    - Local LLM bundle.
    - Richer evaluations.
    - Diagram and table extraction.

14. References
    - Libraries and documentation used.

15. AI Tool Usage Declaration
    - Include the completed declaration template.

