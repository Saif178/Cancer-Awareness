"""Constrained oncology ontology used by the local GraphRAG layer."""

ENTITY_TYPES = (
    "CANCER", "SYMPTOM", "TREATMENT", "DRUG", "GENE", "BIOMARKER",
    "RISK_FACTOR", "DIAGNOSTIC_TEST", "SIDE_EFFECT", "ANATOMY", "OTHER"
)

RELATION_TYPES = (
    "HAS_SYMPTOM", "HAS_RISK_FACTOR", "TREATED_BY", "DIAGNOSED_BY",
    "ASSOCIATED_WITH", "TARGETS", "HAS_SIDE_EFFECT", "AFFECTS",
    "INDICATED_FOR", "BIOMARKER_FOR", "TYPE_OF"
)

# Terms are deliberately conservative. Unknown terms are not promoted to
# authoritative medical entities unless they match an ontology/pattern.
CANCERS = [
    "breast cancer", "lung cancer", "liver cancer", "prostate cancer",
    "ovarian cancer", "colorectal cancer", "pancreatic cancer",
    "cervical cancer", "skin cancer", "melanoma", "lymphoma", "leukemia",
    "kidney cancer", "renal cancer", "bladder cancer", "thyroid cancer",
    "brain cancer", "brain tumor", "stomach cancer", "gastric cancer",
    "esophageal cancer", "endometrial cancer", "head and neck cancer",
]

DRUGS = [
    "pembrolizumab", "nivolumab", "ipilimumab", "trastuzumab", "tamoxifen",
    "herceptin", "bevacizumab", "rituximab", "osimertinib", "cetuximab",
    "paclitaxel", "carboplatin", "cisplatin", "doxorubicin", "methotrexate",
    "letrozole", "anastrozole", "olaparib", "palbociclib", "abemaciclib",
]

BIOMARKERS = [
    "her2", "her2-positive", "pd-1", "pd-l1", "egfr", "alk", "ras",
    "kras", "nras", "braf", "brca1", "brca2", "er", "pr", "estrogen receptor",
    "progesterone receptor", "ki-67", "msi", "microsatellite instability",
    "tumor mutational burden", "tmb",
]

GENES = ["brca1", "brca2", "egfr", "alk", "kras", "nras", "braf", "ras"]

DIAGNOSTICS = [
    "mammography", "biopsy", "ct scan", "computed tomography", "mri",
    "magnetic resonance imaging", "colonoscopy", "pet scan", "pet ct",
    "ultrasound", "blood test", "genetic testing", "genomic testing",
]

TREATMENTS = [
    "immunotherapy", "chemotherapy", "radiation therapy", "radiotherapy",
    "surgery", "targeted therapy", "hormone therapy", "hormonal therapy",
    "stem cell transplant", "bone marrow transplant", "car-t", "screening",
]

SYMPTOMS = [
    "fatigue", "weight loss", "weight gain", "lump", "bleeding", "pain",
    "cough", "shortness of breath", "fever", "night sweats", "nausea",
    "vomiting", "loss of appetite", "difficulty swallowing", "hoarseness",
    "change in bowel habits", "blood in stool", "blood in urine",
]

RISK_FACTORS = [
    "smoking", "tobacco", "alcohol", "obesity", "family history",
    "genetic mutation", "brca mutation", "uv exposure", "sun exposure",
    "age", "radiation exposure",
]

ANATOMY = [
    "breast", "lung", "liver", "prostate", "ovary", "ovarian", "pancreas",
    "colon", "rectum", "cervix", "skin", "kidney", "bladder", "thyroid",
]

LEXICON = {
    "CANCER": CANCERS,
    "DRUG": DRUGS,
    "BIOMARKER": BIOMARKERS,
    "GENE": GENES,
    "DIAGNOSTIC_TEST": DIAGNOSTICS,
    "TREATMENT": TREATMENTS,
    "SYMPTOM": SYMPTOMS,
    "RISK_FACTOR": RISK_FACTORS,
    "ANATOMY": ANATOMY,
}
