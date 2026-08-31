"""Conservative oncology entity/relation extraction with template-aligned relations.

Every evidence edge is tied to its source transcript chunk and sentence.
No template-only scaffold edge is used as medical evidence.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, asdict
from .schema import LEXICON

_SENTENCE = re.compile(r"(?<=[.!?])\s+")
CANONICAL = {
    "mammogram": "mammography",
    "her2-positive": "her2",
    "tumor markers": "tumor marker",
    "tumour": "tumor",
    "computed tomography": "ct scan",
    "magnetic resonance imaging": "mri",
    "sonography": "ultrasound",
    "x-rays": "x-ray",
    "psa blood test": "psa blood test",
    "fine needle aspiration": "fine needle aspiration",
    "fnac": "fine needle aspiration",
}

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
    text = text.strip(" .,;:()[]{}")
    return CANONICAL.get(text, text)

def _find_entities(sentence: str):
    found=[]
    lower=sentence.lower()
    for entity_type, terms in LEXICON.items():
        for term in sorted(set(terms), key=len, reverse=True):
            for m in re.finditer(r"(?<!\w)" + re.escape(term) + r"(?!\w)", lower):
                found.append(
                    Entity(
                        sentence[m.start():m.end()],
                        entity_type,
                        normalize(term),
                    )
                )
    unique={}
    for e in found:
        unique[(e.normalized, e.entity_type)] = e
    return list(unique.values())

def _has(s, *patterns):
    return any(re.search(p, s) for p in patterns)

def _relation_candidates(entities, sentence):
    s=sentence.lower()
    pairs=[]
    for a in entities:
        for b in entities:
            if a is b or (a.normalized == b.normalized and a.entity_type == b.entity_type):
                continue
            rel=None; conf=0.70

            if _has(s, r"\b(treat(?:ed|s|ing)?|therapy|treatment|used to treat|manage|managed)\b"):
                if a.entity_type=="CANCER" and b.entity_type in {"DRUG","TREATMENT"}:
                    rel,conf="TREATED_BY",0.82
                elif a.entity_type in {"DRUG","TREATMENT"} and b.entity_type=="CANCER":
                    rel,conf="INDICATED_FOR",0.78

            if rel is None and _has(s, r"\b(target|targets|targeted|inhibit|inhibits)\b"):
                if a.entity_type in {"DRUG","TREATMENT"} and b.entity_type in {"BIOMARKER","GENE"}:
                    rel,conf="TARGETS",0.84

            # Template: screening/imaging method -> finding.
            if rel is None and _has(s, r"\b(identify|identifies|identifying|detect|detects|detected|find|finds|finding|shows|showed)\b"):
                if a.entity_type in {"DIAGNOSTIC_TEST","SCREENING_METHOD"} and b.entity_type=="FINDING":
                    rel,conf="DETECTS",0.82
                elif a.entity_type=="CANCER" and b.entity_type in {"DIAGNOSTIC_TEST","SCREENING_METHOD"}:
                    rel,conf="DIAGNOSED_BY",0.80

            # Template: screening method -> cancer.
            if rel is None and _has(s, r"\b(screen|screening|screened)\b"):
                if a.entity_type in {"DIAGNOSTIC_TEST","SCREENING_METHOD"} and b.entity_type=="CANCER":
                    rel,conf="INDICATED_FOR",0.79
                elif a.entity_type=="CANCER" and b.entity_type in {"DIAGNOSTIC_TEST","SCREENING_METHOD"}:
                    rel,conf="DIAGNOSED_BY",0.79

            if rel is None and _has(s, r"\b(side effect|adverse effect|caus(?:e|es|ed)|causing)\b"):
                if a.entity_type in {"DRUG","TREATMENT"} and b.entity_type in {"SYMPTOM","SIDE_EFFECT"}:
                    rel,conf="HAS_SIDE_EFFECT",0.76

            if rel is None and _has(s, r"\b(risk factor|risk|associated with|linked to|association|risk for)\b"):
                if a.entity_type=="CANCER" and b.entity_type=="RISK_FACTOR":
                    rel,conf="HAS_RISK_FACTOR",0.75

            if rel is None and _has(s, r"\b(biomarker|marker|positive|mutation|expression)\b"):
                if a.entity_type=="CANCER" and b.entity_type in {"BIOMARKER","GENE"}:
                    rel,conf="BIOMARKER_FOR",0.74
                elif a.entity_type=="DIAGNOSTIC_TEST" and b.entity_type in {"BIOMARKER","GENE"}:
                    rel,conf="IDENTIFIES",0.76

            if rel is None and _has(s, r"\b(symptom|symptoms|sign|signs|present(?:s|ing)?|experienc(?:e|es|ed))\b"):
                if a.entity_type=="CANCER" and b.entity_type=="SYMPTOM":
                    rel,conf="HAS_SYMPTOM",0.73

            if rel is None and _has(s, r"\b(affect(?:s|ed|ing)?|involves?)\b"):
                if a.entity_type=="CANCER" and b.entity_type=="ANATOMY":
                    rel,conf="AFFECTS",0.72

            if rel is None and _has(s, r"\b(sample|samples|fluid|fluids|blood|urine|saliva|stool)\b"):
                if a.entity_type in {"DIAGNOSTIC_TEST","SCREENING_METHOD"} and b.entity_type=="SAMPLE_TYPE":
                    rel,conf="USES_SAMPLE",0.75

            if rel:
                pairs.append((a,b,rel,conf))
    return pairs

def extract_from_chunk(text: str, chunk_id: str, metadata: dict):
    relations=[]; entities=[]; seen=set()
    for sentence in [x.strip() for x in _SENTENCE.split(text) if x.strip()]:
        ents=_find_entities(sentence)
        for e in ents:
            key=(e.normalized,e.entity_type)
            if key not in seen:
                entities.append(e); seen.add(key)
        for a,b,rel,conf in _relation_candidates(ents,sentence):
            relations.append(Relation(
                source=a.normalized, source_type=a.entity_type,
                relation=rel, target=b.normalized, target_type=b.entity_type,
                sentence=sentence, confidence=conf, chunk_id=str(chunk_id),
                video_id=str(metadata.get("video_id","")),
                title=str(metadata.get("title","")), link=str(metadata.get("link","")),
            ))
    return entities, relations

def relation_to_dict(r: Relation):
    return asdict(r)
