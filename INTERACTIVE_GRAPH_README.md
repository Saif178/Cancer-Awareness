# Interactive Oncology Knowledge Graph

This upgrade adds click-to-inspect GraphRAG visualization to the Cancer Awareness project.

## What it does

Click an ontology node in the **Evidence Graph**. The inspector shows:

- connected entity
- relationship type and direction
- extraction confidence
- exact source sentence stored on the graph edge
- exact Chroma transcript chunk using `chunk_id`
- video ID
- video title
- original YouTube link

The graph uses the transcript-backed `MedicalKnowledgeGraph` as the authoritative evidence layer. The existing template graph remains a separate presentation layer.

## Examples

Nodes such as `Mammography`, `PSA`, `Biomarker`, and `Colonoscopy` are retained when present in the transcript-backed graph. The template overview remains available in a separate tab.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run streamlit_app_RAG_cloud_ready.py
```

## Important provenance behavior

A template relationship is never treated as independent medical evidence. Evidence inspection comes from transcript-backed graph edges and the immutable `chunk_id`, `video_id`, `title`, and `link` fields stored with each relationship.


## ChromaDB first-run fix

The Streamlit application now uses `get_or_create_collection()` for `cancer_treatment_rag`. Therefore a missing collection no longer causes a startup RuntimeError.

The collection is still empty until the project's transcript indexing step is run. The original project specifies `chunking_cancer.py` as the component that reads `cancer_treatment_transcripts.json`, uses `all-MiniLM-L6-v2`, and creates the `cancer_treatment_rag` collection.

For a local Windows installation, run from the project root:

```text
python chunking_cancer.py
streamlit run streamlit_app_RAG_cloud_ready.py
```

If your Chroma database is stored elsewhere, set:

```text
CHROMA_DB_PATH=C:\path\to\local_chroma_db
CHROMA_COLLECTION=cancer_treatment_rag
```

You can verify the database with:

```text
python check_chroma.py
```

The application will not attempt RAG retrieval when the collection contains zero vectors.
