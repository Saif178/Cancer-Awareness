# Cancer Awareness Project

## Overview

The **Cancer Awareness Project** is a local Retrieval-Augmented Generation (RAG) application for exploring cancer and oncology information contained in YouTube video transcripts.

The project combines:

- YouTube video discovery using `yt-dlp`
- YouTube transcript extraction
- Local text chunking
- Local semantic embeddings using Sentence Transformers
- Persistent vector storage with ChromaDB
- Semantic retrieval of relevant oncology transcript passages
- Local LLM generation through Ollama
- A Streamlit web interface for interactive medical research queries

The RAG pipeline is designed to keep the retrieval and answer-generation workflow local after the source transcripts and models have been obtained.

> **Medical disclaimer:** This project is an educational/research application and is **not a medical diagnostic or treatment system**. Its responses are limited to information retrieved from the indexed source transcripts and should not be used as a substitute for advice from a qualified healthcare professional.

---

## Project Architecture

```text
YouTube Search
     |
     v
youtube_agent.py
     |
     |-- Discover cancer/oncology videos
     |-- Extract English transcripts
     v
cancer_treatment_transcripts.json
     |
     v
chunking_cancer.py
     |
     |-- Split transcripts into overlapping chunks
     |-- Generate local embeddings
     |-- Store vectors + metadata
     v
local_chroma_db/
     |
     v
MedicalRAGRetriever.py
     |
     |-- Embed user query
     |-- Retrieve top-K relevant chunks
     v
offline_RAG.py
     |
     |-- Retrieve context
     |-- Send context to local Ollama LLM
     |-- Generate grounded answer
     v
streamlit_app_RAG.py
     |
     v
Interactive Web Application
```

---

## Repository Structure

```text
Cancer_Awareness_Project/
│
├── cancer_treatment_transcripts.json
│   └── Extracted YouTube video metadata and transcripts
│
├── youtube_agent.py
│   └── Searches YouTube and extracts English transcripts
│
├── chunking_cancer.py
│   └── Chunks transcripts and indexes them in ChromaDB
│
├── MedicalRAGRetriever.py
│   └── Retrieves the most relevant transcript chunks
│
├── offline_RAG.py
│   └── Runs local RAG retrieval and Ollama-based answer generation
│
├── streamlit_app_RAG.py
│   └── Interactive Streamlit RAG application
│
├── local_chroma_db/
│   └── Persistent ChromaDB vector database
│
└── README.md
```

---

## Key Components

### 1. YouTube Transcript Agent

`youtube_agent.py` implements `CancerTranscriptAgentYTDLP`.

It:

1. Searches YouTube using a configurable oncology-related query.
2. Collects video IDs, titles, URLs and other metadata.
3. Retrieves English transcripts using `youtube-transcript-api`.
4. Cleans transcript text.
5. Saves the resulting dataset to:

```text
cancer_treatment_transcripts.json
```

The default execution example searches for:

```text
immunotherapy cancer treatment oncology
```

and processes up to 100 videos.

---

### 2. Transcript Chunking and Vector Indexing

`chunking_cancer.py` implements `MedicalOpenSourceIngestionPipeline`.

The ingestion process:

1. Loads `cancer_treatment_transcripts.json`.
2. Splits transcripts using `RecursiveCharacterTextSplitter`.
3. Uses a chunk size of **800 characters**.
4. Uses **150 characters of overlap** between chunks.
5. Generates embeddings using:

```text
all-MiniLM-L6-v2
```

6. Stores vectors in a persistent ChromaDB collection named:

```text
cancer_treatment_rag
```

7. Stores useful metadata including:

- YouTube video ID
- Video title
- Video URL
- Chunk index
- Medical domain

ChromaDB uses cosine similarity for semantic matching.

---

### 3. Medical Retriever

`MedicalRAGRetriever.py` provides the retrieval layer.

Given a user question, it:

1. Converts the query into an embedding.
2. Searches the local ChromaDB collection.
3. Retrieves the top-K matching chunks.
4. Returns the matching transcript text, metadata and similarity score.

Example:

```python
retriever = MedicalRAGRetriever()

results = retriever.query_medical_context(
    user_query="What are the clinical outcomes of lung cancer immunotherapy?",
    top_k=3
)
```

---

### 4. Offline RAG Engine

`offline_RAG.py` implements `OfflineMedicalRAGEngine`.

The engine combines:

```text
User Question
      |
      v
ChromaDB Retrieval
      |
      v
Relevant Transcript Context
      |
      v
Grounded Prompt
      |
      v
Local Ollama Model
      |
      v
Answer
```

The system prompt instructs the local LLM to:

- Use only the retrieved transcript context.
- Avoid unsupported extrapolation.
- Avoid hallucinating information.
- Explicitly state when the requested information is not available in the local database.
- Produce factual and objective responses.

The default local model is:

```text
llama3
```

Other models supported by the Streamlit interface include:

```text
llama3
llama3.1
llama3.2
mistral
```

---

## Streamlit Application

`streamlit_app_RAG.py` provides the user interface.

Run it with:

```bash
streamlit run streamlit_app_RAG.py
```

The application provides:

- Clinical research query input
- Ollama model selection
- Top-K retrieval control
- ChromaDB vector count
- Local RAG answer generation
- Retrieved transcript references
- Original YouTube source links

The interface displays generated answers alongside the source transcript fragments used to construct the answer.

---

## Requirements

The project requires Python 3.10+ and the following Python packages:

```text
chromadb
langchain-text-splitters
sentence-transformers
streamlit
ollama
yt-dlp
youtube-transcript-api
```

Install them with:

```bash
pip install chromadb langchain-text-splitters sentence-transformers streamlit ollama yt-dlp youtube-transcript-api
```

For reproducible environments, it is recommended to create a `requirements.txt` file and pin package versions after testing the project.

---

## Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd Cancer_Awareness_Project
```

### 2. Create a Virtual Environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install chromadb langchain-text-splitters sentence-transformers streamlit ollama yt-dlp youtube-transcript-api
```

---

## Ollama Setup

The RAG generation layer requires a locally running Ollama installation.

Install Ollama from the official Ollama distribution for your operating system.

After installation, download a supported model.

For example:

```bash
ollama pull llama3
```

Verify that the model is available:

```bash
ollama list
```

You can also test it directly:

```bash
ollama run llama3
```

Keep the Ollama service available when running the RAG application.

---

## Running the Complete Pipeline

### Step 1: Collect YouTube Transcripts

Run:

```bash
python youtube_agent.py
```

This creates:

```text
cancer_treatment_transcripts.json
```

You can modify the search query in the execution section of `youtube_agent.py`.

For example:

```python
agent = CancerTranscriptAgentYTDLP(
    search_query="immunotherapy cancer treatment oncology"
)
```

---

### Step 2: Build the Vector Database

Run:

```bash
python chunking_cancer.py
```

This reads the transcript JSON file and creates/populates:

```text
local_chroma_db/
```

with the collection:

```text
cancer_treatment_rag
```

If you change the source transcripts and rerun ingestion, review the collection strategy carefully because the current ingestion code uses `collection.add()` and does not automatically clear previously indexed vectors.

---

### Step 3: Test Retrieval

Run:

```bash
python MedicalRAGRetriever.py
```

The script performs a sample semantic search and prints:

- Matching transcript chunks
- Similarity scores
- Video titles
- Source URLs
- Transcript snippets

---

### Step 4: Run the Offline RAG Engine

Make sure Ollama is available and the selected model has been downloaded:

```bash
ollama pull llama3
```

Then run:

```bash
python offline_RAG.py
```

The engine retrieves relevant transcript context and asks the local Ollama model to generate a grounded answer.

---

### Step 5: Launch the Streamlit Application

Run:

```bash
streamlit run streamlit_app_RAG.py
```

Then open the Streamlit URL shown in the terminal, typically:

```text
http://localhost:8501
```

---

## Example Queries

Example questions include:

```text
What specific adverse side effects are discussed regarding immunotherapy?
```

```text
What clinical outcomes are discussed for lung cancer immunotherapy?
```

```text
What clinical trial results are mentioned in the indexed transcripts?
```

```text
What treatment approaches are discussed for cancer patients?
```

The answer is generated from the retrieved local transcript context rather than from a general-purpose external search.

---

## RAG Configuration

### Chunking

The current chunking configuration is:

```python
chunk_size=800
chunk_overlap=150
```

These parameters can be adjusted depending on transcript length and retrieval performance.

### Embedding Model

The project uses:

```text
all-MiniLM-L6-v2
```

This is a lightweight Sentence Transformer model suitable for local semantic search.

### Retrieval

The default retrieval depth is:

```text
Top-K = 3
```

The Streamlit interface allows the user to select between 1 and 5 chunks.

### LLM Temperature

The local generation engine uses a low temperature:

```text
0.1
```

This is intended to encourage more deterministic and source-grounded responses.

---

## Data Privacy

The intended RAG workflow is designed around local processing:

```text
Transcript Data
      ↓
Local Embeddings
      ↓
Local ChromaDB
      ↓
Local Ollama LLM
      ↓
Local Answer
```

No OpenAI API key or cloud LLM API is required by the implemented RAG generation pipeline.

However, the **YouTube discovery and transcript collection stage requires Internet access**.

---

## Source Attribution

Retrieved transcript chunks retain metadata for the original YouTube source:

```text
video_id
title
link
chunk_index
medical_domain
```

The Streamlit interface exposes these references so users can inspect the source material behind retrieved information.

---

## Important Limitations

### Medical Accuracy

The application does not independently validate medical claims in YouTube transcripts.

Retrieved content may be:

- incomplete
- outdated
- inaccurate
- presented without sufficient clinical context
- specific to a particular study or patient population

Always verify important medical information against authoritative clinical sources and consult qualified healthcare professionals.

### Transcript Availability

Some YouTube videos may not have English transcripts. Those videos are skipped by the transcript extraction pipeline.

### Source Quality

The current discovery mechanism searches YouTube based on keywords. It does not automatically establish that a video comes from a medically authoritative institution or clinician.

### Local Model Dependency

The quality of generated answers depends on:

- the Ollama model selected
- the quality of retrieved chunks
- the quality of the indexed transcripts
- embedding similarity
- the completeness of the source material

### Vector Database Duplication

The current ingestion script uses `collection.add()`. Re-running ingestion against the same data can create duplicate records or ID conflicts. Consider clearing/rebuilding the collection when performing a complete re-index.

---

## Recommended Production Improvements

For a more robust production implementation, consider adding:

1. Source credibility filtering for medical institutions and peer-reviewed sources.
2. Transcript deduplication.
3. Document/version tracking.
4. Retrieval similarity thresholds.
5. Hybrid keyword + semantic retrieval.
6. Reranking of retrieved chunks.
7. Explicit source citations in generated answers.
8. Automatic detection of outdated medical information.
9. Evaluation datasets for RAG accuracy.
10. Automated hallucination and grounding tests.
11. Structured logging instead of console-only output.
12. Configuration through environment variables.
13. A pinned `requirements.txt`.
14. Automated tests.
15. A `.gitignore` excluding virtual environments, caches and local databases when appropriate.

---


## Security and Privacy Recommendations

Do not commit:

- API keys
- passwords
- authentication tokens
- private patient information
- confidential medical records
- private datasets
- local virtual environments
- unnecessary database artifacts

This project currently works with public video transcript content and should not be populated with identifiable patient information without appropriate authorization, privacy controls and compliance review.

---

## License

Add the project's intended license before distributing the repository.

For example, a common open-source choice is the MIT License:

```text
MIT License
```

Do not claim a specific license unless it has actually been selected for the project.

---

## Project Workflow Summary

```text
1. Search YouTube
        ↓
2. Extract English transcripts
        ↓
3. Save transcript dataset
        ↓
4. Split transcripts into chunks
        ↓
5. Generate local embeddings
        ↓
6. Store embeddings in ChromaDB
        ↓
7. Enter user question
        ↓
8. Retrieve top-K relevant chunks
        ↓
9. Build grounded context
        ↓
10. Generate answer with Ollama
        ↓
11. Display answer + source references
```

---

## Conclusion

The Cancer Awareness Project provides a local, source-grounded RAG workflow for exploring oncology-related video transcripts. Its primary design goals are **local retrieval, local LLM generation, source traceability and reduced dependence on external AI APIs**.

The system should be treated as a research and educational tool rather than a clinical decision-support system.
