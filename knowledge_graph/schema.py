"""Oncology ontology and presentation schema for the Cancer Awareness GraphRAG.

The ontology is deliberately constrained.  The visual template is represented as
a semantic scaffold; only transcript-backed edges are eligible for RAG answers.
"""
ENTITY_TYPES = (
    "CANCER", "SYMPTOM", "TREATMENT", "DRUG", "GENE", "BIOMARKER",
    "RISK_FACTOR", "DIAGNOSTIC_TEST", "SIDE_EFFECT", "ANATOMY",
    "SCREENING_METHOD", "FINDING", "SAMPLE_TYPE", "PURPOSE", "OUTCOME", "OTHER"
)

RELATION_TYPES = (
    "ACHIEVED_THROUGH", "USED_TO_DETECT", "IDENTIFIES", "DETECTS",
    "OFTEN_FOLLOWED_BY", "LEADS_TO",
    "HAS_SYMPTOM", "HAS_RISK_FACTOR", "TREATED_BY", "DIAGNOSED_BY",
    "ASSOCIATED_WITH", "TARGETS", "HAS_SIDE_EFFECT", "AFFECTS",
    "INDICATED_FOR", "BIOMARKER_FOR", "TYPE_OF", "HAS_FINDING",
    "USES_SAMPLE", "HAS_BENEFIT", "HAS_PURPOSE"
)

CANCERS = [
    "breast cancer", "lung cancer", "liver cancer", "prostate cancer",
    "ovarian cancer", "colorectal cancer", "pancreatic cancer",
    "cervical cancer", "skin cancer", "melanoma", "lymphoma", "leukemia",
    "kidney cancer", "renal cancer", "bladder cancer", "thyroid cancer",
    "brain cancer", "brain tumor", "stomach cancer", "gastric cancer",
    "esophageal cancer", "endometrial cancer", "head and neck cancer",
    "oral cancer", "throat cancer", "colon cancer", "uterine cancer",
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
    "tumor mutational burden", "tmb", "biomarker", "biomarkers", "tumor marker",
    "tumor markers", "ctc", "ctcs", "exosome", "exosomes", "dna", "rna",
]

GENES = ["brca1", "brca2", "egfr", "alk", "kras", "nras", "braf", "ras"]

DIAGNOSTICS = [
    "mammography", "mammogram", "biopsy", "fine needle aspiration", "fnac",
    "ct scan", "computed tomography", "mri", "magnetic resonance imaging",
    "colonoscopy", "pet scan", "pet ct", "ultrasound", "sonography",
    "blood test", "blood tests", "genetic testing", "genomic testing",
    "x-ray", "x-rays", "digital rectal exam", "dre", "pap test", "pap smear",
]

TREATMENTS = [
    "immunotherapy", "chemotherapy", "radiation therapy", "radiotherapy",
    "surgery", "targeted therapy", "hormone therapy", "hormonal therapy",
    "stem cell transplant", "bone marrow transplant", "car-t", "treatment",
]

SCREENING_METHODS = [
    "mammography", "mammogram", "colonoscopy", "blood test", "blood tests",
    "fit", "stool test", "dna stool test", "ct colonography",
    "psa blood test", "digital rectal exam", "mri", "pap test", "pap smear",
]

SYMPTOMS = [
    "fatigue", "weight loss", "weight gain", "lump", "bleeding", "pain",
    "cough", "shortness of breath", "fever", "night sweats", "nausea",
    "vomiting", "loss of appetite", "difficulty swallowing", "hoarseness",
    "change in bowel habits", "blood in stool", "blood in urine",
    "bloating", "abdominal pain", "abdominal discomfort", "constipation",
    "diarrhea", "urinary symptoms", "headache", "vision changes",
]

RISK_FACTORS = [
    "smoking", "tobacco", "alcohol", "obesity", "family history",
    "genetic mutation", "brca mutation", "uv exposure", "sun exposure",
    "age", "radiation exposure", "dense breast tissue",
]

ANATOMY = [
    "breast", "lung", "liver", "prostate", "ovary", "ovarian", "pancreas",
    "colon", "rectum", "cervix", "skin", "kidney", "bladder", "thyroid",
    "uterus", "oral cavity", "throat", "stomach", "esophagus",
]

FINDINGS = [
    "microcalcifications", "calcifications", "small tumors", "early signs",
    "lumps", "tumor", "tumour", "polyps", "adenomas", "lesions",
    "breast abnormalities", "prostate abnormalities", "abnormal bleeding",
]

SAMPLE_TYPES = ["blood", "urine", "saliva", "stool", "tissue"]

LEXICON = {
    "CANCER": CANCERS,
    "DRUG": DRUGS,
    "BIOMARKER": BIOMARKERS,
    "GENE": GENES,
    "DIAGNOSTIC_TEST": DIAGNOSTICS,
    "SCREENING_METHOD": SCREENING_METHODS,
    "TREATMENT": TREATMENTS,
    "SYMPTOM": SYMPTOMS,
    "RISK_FACTOR": RISK_FACTORS,
    "ANATOMY": ANATOMY,
    "FINDING": FINDINGS,
    "SAMPLE_TYPE": SAMPLE_TYPES,
}

# The five top-level method cards from the user-supplied visual template.
TEMPLATE_MODULES = {
    "blood_biomarkers": {
        "title": "1. Blood Tests & Biomarkers",
        "color": "green",
        "evidence_hint": ["blood test", "blood tests", "biomarker", "biomarkers", "tumor marker", "tumor markers"],
        "subgroups": {
            "Sample Types": ["blood", "urine", "saliva"],
            "Key Features": ["biomarker", "biomarkers"],
            "Benefits": ["early detection"],
        },
    },
    "mammography": {
        "title": "2. Mammography for Breast Cancer",
        "color": "blue",
        "evidence_hint": ["mammography", "mammogram", "breast cancer"],
        "subgroups": {
            "Method": ["mammography", "mammogram", "3-d mammography", "tomosynthesis"],
            "Detects": ["microcalcifications", "calcifications", "small tumors", "early signs"],
            "Benefits": ["early detection", "reduced mortality"],
        },
    },
    "prostate": {
        "title": "3. Prostate Cancer Detection",
        "color": "purple",
        "evidence_hint": ["prostate cancer", "psa", "digital rectal exam", "mri"],
        "subgroups": {
            "Who": ["age", "family history", "genetic risk"],
            "Screening Methods": ["psa blood test", "digital rectal exam", "mri"],
            "Benefits": ["early detection", "screening"],
        },
    },
    "colorectal": {
        "title": "4. Colorectal Cancer Screening",
        "color": "orange",
        "evidence_hint": ["colorectal cancer", "colon cancer", "colonoscopy", "stool"],
        "subgroups": {
            "Screening Methods": ["colonoscopy", "fit", "stool test", "ct colonography"],
            "Who & When": ["age", "higher risk", "family history"],
            "Benefits": ["polyps", "early cancer", "prevention"],
        },
    },
    "diagnostics": {
        "title": "5. General Diagnostic Tests",
        "color": "teal",
        "evidence_hint": ["diagnosis", "diagnostic", "biopsy", "mri", "ct scan", "ultrasound"],
        "subgroups": {
            "Imaging Tests": ["ultrasound", "x-rays", "ct scan", "mri", "pet scan"],
            "Laboratory Tests": ["blood tests", "urine tests", "tumor markers"],
            "Tissue Sampling": ["biopsy", "fine needle aspiration", "fnac"],
            "Purpose": ["confirm diagnosis", "determine cancer type", "assess stage", "guide treatment"],
            "Outcome": ["accurate diagnosis", "treatment planning", "monitor response"],
        },
    },
}
