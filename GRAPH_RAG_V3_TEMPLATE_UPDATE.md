# GraphRAG v3 Template Update

- Reorganized the knowledge graph around the supplied Cancer Early Detection infographic.
- Added five fixed method modules: Blood Tests & Biomarkers, Mammography for Breast Cancer, Prostate Cancer Detection, Colorectal Cancer Screening, and General Diagnostic Tests.
- Added central Early Detection of Cancer and Better Outcomes nodes.
- Added template subgroup cards for methods, detects/findings, who/when, benefits, imaging, laboratory tests, tissue sampling, purpose and outcomes.
- Added deterministic E1–E6 evidence source cards mapped to the project's transcript corpus.
- Kept transcript-backed graph edges separate from template scaffold edges.
- Preserved provenance for every evidence edge back to transcript chunk/video/title/link.
- Updated Streamlit to render the full template graph plus question-specific graph paths.
- Updated graph builder to emit JSON, DOT and PNG outputs.
