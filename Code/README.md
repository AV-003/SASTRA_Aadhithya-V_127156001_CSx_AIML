# Code and local run instructions

The full source is included: `app.py`, `src/`, `scripts/`, `tests/`, and `data/`.

## Run on Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

The sample PDF is already included in `data/sample_documents/`. If needed, regenerate it with `python scripts/create_sample_pdf.py`. Optional semantic-retrieval packages are listed in `requirements-optional.txt`. External LLM access is not needed for the local fallback. Do not add secrets to the submission.

The included `Evaluation_Results/test_results.md` records the project’s earlier test run; tests were not rerun while preparing this submission ZIP.
