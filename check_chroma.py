"""Check and, if necessary, bootstrap the Cancer Awareness Chroma index."""
from pathlib import Path
import json
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

DB_PATH = Path("./local_chroma_db")
COLLECTION = "cancer_treatment_rag"
TRANSCRIPTS = Path("./cancer_treatment_transcripts.json")

client = chromadb.PersistentClient(path=str(DB_PATH))
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
collection = client.get_or_create_collection(
    name=COLLECTION,
    embedding_function=ef,
    metadata={"hnsw:space": "cosine"},
)

print(f"Chroma path : {DB_PATH.resolve()}")
print(f"Collection  : {COLLECTION}")
print(f"Vector count: {collection.count()}")

if collection.count() == 0:
    if not TRANSCRIPTS.exists():
        raise SystemExit(f"Transcript file not found: {TRANSCRIPTS.resolve()}")

    raw = json.loads(TRANSCRIPTS.read_text(encoding="utf-8"))
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        length_function=len,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    documents, metadatas, ids = [], [], []

    for video in raw:
        transcript = str(video.get("transcript", "") or "").strip()
        if not transcript:
            continue
        vid = str(video.get("video_id", ""))
        title = str(video.get("title", "Untitled Video"))
        link = str(video.get("link") or f"https://www.youtube.com/watch?v={vid}")
        for i, chunk in enumerate(splitter.split_text(transcript)):
            ids.append(f"{vid}_chunk_{i}")
            documents.append(f"Source Video: {title} | Content: {chunk}")
            metadatas.append({
                "video_id": vid,
                "title": title,
                "link": link,
                "chunk_index": i,
                "medical_domain": "oncology",
            })

    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    print(f"Bootstrapped {collection.count()} vectors from {len(raw)} transcripts.")
