# Test Results

Date: 2026-10-10

Environment:

- Python: 3.13.1
- Local virtual environment: `.venv`
- Streamlit: installed and started successfully
- PyMuPDF: installed and verified
- Retrieval used for verification: scikit-learn TF-IDF fallback
- LLM credentials found: none

## Automated Software Tests

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Result:

```text
........                                                                 [100%]
8 passed in 2.91s
```

Coverage focus:

- Unsupported file handling.
- Synthetic PDF extraction with page numbers.
- Page-preserving chunking.
- TF-IDF retrieval.
- Insufficient-evidence behavior.

## Syntax Check

Command:

```powershell
.\.venv\Scripts\python.exe -m compileall app.py src scripts tests
```

Result: passed.

## End-to-End Smoke Check

Verified by command-line execution:

- Generated synthetic sample PDF.
- Extracted 3 pages with PyMuPDF.
- Created 4 chunks.
- Built TF-IDF retriever.
- Asked: "What signal reports the lamp status?"
- Answer method: evidence-based fallback.
- Citation included `vehicle_lighting_hld_sample.pdf`, page 2.
- Asked: "What is the brake pressure calibration threshold?"
- Result: insufficient evidence, with no invented citation.

## Sample Evaluation

Command:

```powershell
python -c "from src.evaluation import run_sample_evaluation; import json; print(json.dumps(run_sample_evaluation(False), indent=2))"
```

Result:

- Backend: TF-IDF.
- Overall result: passed.
- Five evidence questions retrieved expected supporting pages.
- One insufficient-evidence question returned `insufficient-evidence`.

## Manual Demonstration Observations

Verified:

- Synthetic PDF renders correctly using Poppler.
- Text is readable and aligned on all 3 pages.
- Poppler emitted font-substitution warnings, but rendered output was usable.
- Streamlit app started at `http://localhost:8501`.
- HTTP probe returned status code 200.

Not verified in this environment:

- Sentence Transformers or FAISS semantic retrieval, because optional packages are not installed.
- External LLM generation, because no provider was configured and no credentials were present.
- OCR on scanned PDFs, because OCR is intentionally not bundled.
