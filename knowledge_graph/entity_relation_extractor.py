"""Conservative, dependency-light oncology entity/relation extraction.

The extractor is intentionally provenance-first: every relation is tied to the
source chunk and sentence from which it was extracted. It is suitable for the
bundled transcript corpus and does not require an LLM/API key.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, asdict
from .schema import LEXICON, RELATION_TYPES

_SENTENCE = re.compile(r"(?<=[.!?])\s+")

@dataclass
class Entity:
    name: str
    entity_type: str
    normalized: str

@dataclass
class Relation:
    source: str
    source_type: str
    relation: str
    target: str
    target_type: str
    sentence: str
    confidence: float
    chunk_id: str
    video_id: str
    title: str
    link: str


def normalize(text: str) -> str:
    text = re.sub(r"\s+", " ", str(text).strip().lower())
    return text.strip(" .,;:()[]{}")


def _find_entities(sentence: str):
    found = []
    lower = sentence.lower()
    # Longest first prevents 'breast' from obscuring 'breast cancer'.
    for entity_type, terms in LEXICON.items():
        for term in sorted(terms, key=len, reverse=True):
            for m in re.finditer(r"(?<!\w)" + re.escape(term) + r"(?!\w)", lower):
                found.append(Entity(sentence[m.start():m.end()], entity_type, normalize(term)))
    # Deduplicate overlapping occurrences by normalized name/type.
    unique = {}
    for e in found:
        unique[(e.normalized, e.entity_type)] = e
    return list(unique.values())


def _relation_candidates(entities, sentence):
    s = sentence.lower()
    pairs = []
    for a in entities:
        for b in entities:
            if a.normalized == b.normalized and a.entity_type == b.entity_type:
                continue
            # Only infer a relationship when a recognized lexical trigger occurs.
            rel = None
            conf = 0.72
            if re.search(r"\b(treat(?:ed|s|ing)?|therapy|treatment|used to treat|manage|managed)\b", s):
                if a.entity_type == "CANCER" and b.entity_type in {"DRUG", "TREATMENT"}:
                    rel, conf = "TREATED_BY", 0.82
                elif a.entity_type in {"DRUG", "TREATMENT"} and b.entity_type == "CANCER":
                    rel, conf = "INDICATED_FOR", 0.78
            if rel is None and re.search(r"\b(target|targets|targeted|inhibit|inhibits)\b", s):
                if a.entity_type in {"DRUG", "TREATMENT"} and b.entity_type in {"BIOMARKER", "GENE"}:
                    rel, conf = "TARGETS", 0.84
            if rel is None and re.search(r"\b(diagnos(?:e|ed|is|tic)|detected|detecting|test(?:ing)?)\b", s):
                if a.entity_type == "CANCER" and b.entity_type == "DIAGNOSTIC_TEST":
                    rel, conf = "DIAGNOSED_BY", 0.80
            if rel is None and re.search(r"\b(side effect|adverse effect|caus(?:e|es|ed)|causing)\b", s):
                if a.entity_type in {"DRUG", "TREATMENT"} and b.entity_type in {"SYMPTOM", "SIDE_EFFECT"}:
                    rel, conf = "HAS_SIDE_EFFECT", 0.76
            if rel is None and re.search(r"\b(risk factor|risk|associated with|linked to|association)\b", s):
                if a.entity_type == "CANCER" and b.entity_type == "RISK_FACTOR":
                    rel, conf = "HAS_RISK_FACTOR", 0.75
            if rel is None and re.search(r"\b(biomarker|marker|positive|mutation|expression)\b", s):
                if a.entity_type == "CANCER" and b.entity_type in {"BIOMARKER", "GENE"}:
                    rel, conf = "BIOMARKER_FOR", 0.74
            if rel is None and re.search(r"\b(symptom|symptoms|sign|signs|present(?:s|ing)?|experienc(?:e|es|ed))\b", s):
                if a.entity_type == "CANCER" and b.entity_type == "SYMPTOM":
                    rel, conf = "HAS_SYMPTOM", 0.73
            if rel is None and re.search(r"\b(affect(?:s|ed|ing)?|involves?)\b", s):
                if a.entity_type == "CANCER" and b.entity_type == "ANATOMY":
                    rel, conf = "AFFECTS", 0.72
            if rel:
                pairs.append((a, b, rel, conf))
    return pairs


def extract_from_chunk(text: str, chunk_id: str, metadata: dict):
    relations = []
    entities = []
    seen = set()
    for sentence in [x.strip() for x in _SENTENCE.split(text) if x.strip()]:
        ents = _find_entities(sentence)
        for e in ents:
            key = (e.normalized, e.entity_type)
            if key not in seen:
                entities.append(e); seen.add(key)
        for a, b, rel, conf in _relation_candidates(ents, sentence):
            relations.append(Relation(
                source=a.normalized, source_type=a.entity_type,
                relation=rel, target=b.normalized, target_type=b.entity_type,
                sentence=sentence, confidence=conf, chunk_id=str(chunk_id),
                video_id=str(metadata.get("video_id", "")),
                title=str(metadata.get("title", "")), link=str(metadata.get("link", "")),
            ))
    return entities, relations


def relation_to_dict(r: Relation):
    return asdict(r)
