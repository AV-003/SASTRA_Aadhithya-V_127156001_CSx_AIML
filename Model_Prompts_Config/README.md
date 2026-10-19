# Model and configuration

The app uses local TF-IDF retrieval by default. Optional semantic retrieval uses Sentence Transformers/FAISS when installed. Optional Ollama or OpenAI calls require explicit environment-variable configuration. The provided `.env.example` contains placeholders only. Never add API keys, tokens, passwords, or private endpoints to GitHub.

External LLM mode may send retrieved document excerpts to the configured provider; use it only with permission for the data being processed.
