# AUTOSAR HLD Document Analysis Assistant

A capstone prototype for exploring automotive High-Level Design (HLD) documents. The Streamlit app processes PDF documents locally, retrieves relevant excerpts, answers questions with source references, and extracts architecture facts for review.

## Features

- Upload and process an HLD PDF, or load the synthetic Vehicle Lighting Controller sample.
- Retrieve relevant document passages using TF-IDF; optional semantic retrieval is available through additional packages.
- Ask questions and inspect answers alongside supporting document excerpts.
- Extract architecture information and review or export the resulting report.
- Run the included sample evaluation and compare documents.

This is an academic prototype. AI-generated findings require qualified human review; the tool is not production-ready, certified, or evidence of compliance with an automotive standard.

## Run the App

Use Python in a terminal and run the following from the repository root:

```powershell
cd Code
python -m venv .venv
```

Activate the virtual environment and install the required packages:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS or Linux
# source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Start the app from the `Code` directory:

```powershell
streamlit run app.py
```

The app works with its local TF-IDF retrieval fallback and does not require external LLM access. To install optional semantic-retrieval packages, run `python -m pip install -r requirements-optional.txt` from `Code`.

## Tests

From the `Code` directory, install the required packages and run:

```powershell
python -m pytest
```

`Evaluation_Results/test_results.md` contains a report from an earlier test run; rerun the tests to verify the current environment.

## Repository Layout

- `Code/`: Streamlit app, processing and retrieval modules, sample data, scripts, requirements, and tests.
- `Input_Data/`: sample HLD document and evaluation questions.
- `Synopsis/`: project synopsis.
- `Documentation/`: source README and technical-report materials.
- `Evaluation_Results/`: recorded evaluation results.
- `Model_Prompts_Config/`: example configuration guidance; do not commit credentials.
- `Declarations/`: declaration templates and AI tool usage declaration.
- `Video/`: demo recording directory; the recording is not included in this GitHub repository because it exceeds GitHub's 100 MB per-file limit.

The sample HLD is synthetic. See [`Code/README.md`](Code/README.md) for additional local run details.
