# Project Synopsis — AUTOSAR HLD Document Analysis Assistant

## Problem statement
Automotive software engineers and students need to understand long High-Level Design (HLD) PDFs while tracing answers to the original pages. Manually locating components, interfaces, signals, dependencies, and design decisions can be slow.

## Intended users
- Automotive software engineering students preparing design reviews.
- Engineers reviewing HLD components, ports, interfaces, signals, dependencies, and flows.
- Evaluators reviewing a local, explainable AI prototype.

## Proposed solution
A Streamlit dashboard processes an uploaded HLD PDF, extracts page text, creates page-preserving chunks, retrieves relevant evidence, and answers questions with document/page citations. It also has architecture extraction, sample evaluation, document comparison, and CSV/JSON export features.

## Data and AI approach
The project includes a synthetic Vehicle Lighting Controller HLD sample. TF-IDF is the local retrieval fallback; semantic retrieval and Ollama/OpenAI answer generation are optional configurations. The sample is not real AUTOSAR, OEM, supplier, or production documentation.

## Responsible AI measures
The project documents evidence-grounded answers, page citations, insufficient-evidence handling, local processing by default, explicit opt-in for external LLM calls, reset controls, and human review for safety or architecture decisions.
