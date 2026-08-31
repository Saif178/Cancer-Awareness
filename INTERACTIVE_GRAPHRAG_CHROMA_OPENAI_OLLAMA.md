# Cancer Awareness — Interactive GraphRAG + Chroma + OpenAI/Ollama

This version preserves both LLM providers and adds an interactive provenance-first oncology knowledge graph.

## Providers

The sidebar has an **LLM Provider** selector:

- `ollama`: local/remote Ollama endpoint; no OpenAI key is required.
- `openai`: uses `OPENAI_API_KEY` and `OPENAI_MODEL`; Ollama is not required.

Example local secrets:

```toml
LLM_PROVIDER = "ollama"
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3"
```

For OpenAI:

```toml
LLM_PROVIDER = "openai"
OPENAI_API_KEY = "your-key"
OPENAI_MODEL = "gpt-4o-mini"
```

Never commit `.streamlit/secrets.toml`.

## Chroma bootstrap

The application uses:

```text
./local_chroma_db
cancer_treatment_rag
```

It calls `get_or_create_collection()`. If the collection is missing or empty, it automatically builds the vector index from:

```text
cancer_treatment_transcripts.json
```

using `all-MiniLM-L6-v2` and the same 800/150 chunking scheme as the project's ingestion script.

You can verify/bootstrap manually:

```bash
python check_chroma.py
```

## Interactive graph

The evidence graph is transcript-backed. Click an entity such as:

- Mammography
- PSA blood test
- Biomarker
- Colonoscopy

The inspector shows:

- connected entity
- relationship and direction
- extraction confidence
- supporting sentence
- exact chunk ID
- full transcript chunk from Chroma
- video ID/title
- original YouTube link

The template overview remains available separately.

## Run

```bash
pip install -r requirements.txt
streamlit run streamlit_app_RAG_cloud_ready.py
```

## Important deployment note

The initial index is generated locally from the bundled transcript JSON when the Chroma collection is absent/empty. For Streamlit Community Cloud, this can take time because the embedding model must be initialized. If the repository does not contain a usable `local_chroma_db`, the app will bootstrap from the transcript corpus automatically.
