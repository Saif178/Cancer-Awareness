"""Template-style Graphviz renderers for the Cancer Awareness GraphRAG."""
from html import escape
from .template_graph import COLOR_HEX

def _q(s):
    return str(s).replace("\\","\\\\").replace('"','\\"').replace("\n"," ")

def _node_id(s):
    return "n_" + "".join(ch if ch.isalnum() else "_" for ch in str(s))

def to_dot(graph_evidence, max_edges=20):
    """Compact query-specific evidence graph."""
    lines=[
        "digraph G {",
        'graph [rankdir=LR, bgcolor="white", overlap=false, splines=true, nodesep=0.5, ranksep=0.8];',
        'node [shape=box, style="rounded,filled", fontname="Arial", fontsize=10, fillcolor="white", color="#777777"];',
        'edge [fontname="Arial", fontsize=8, color="#666666", arrowsize=0.7];'
    ]
    seen=set()
    for item in graph_evidence[:max_edges]:
        a,b=item["source"],item["target"]
        na,nb=_node_id(a),_node_id(b)
        if a not in seen:
            lines.append(f'{na} [label="{_q(a)}"];'); seen.add(a)
        if b not in seen:
            lines.append(f'{nb} [label="{_q(b)}"];'); seen.add(b)
        lines.append(f'{na} -> {nb} [label="{_q(item["relation"].replace("_"," ").lower())}"];')
    lines.append("}")
    return "\n".join(lines)

def template_to_dot(template_graph, show_entity_details=False):
    """
    Render the Cancer Awareness template using standard Graphviz DOT layout.

    Deliberately avoids:
      - neato
      - fixed pos coordinates
      - pin=true
      - HTML labels

    This is more reliable with Streamlit's st.graphviz_chart().
    """

    template_graph = template_graph or {}

    nodes = template_graph.get("nodes", {})
    sources = template_graph.get("sources", [])

    def q(value):
        """Escape a Graphviz quoted string."""
        return (
            str(value)
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\r", "")
            .replace("\n", "\\n")
        )

    def node_id(value):
        return "n_" + "".join(
            ch if ch.isalnum() else "_"
            for ch in str(value)
        )

    def get_node_label(node_key, fallback):
        node = nodes.get(node_key, {})

        if isinstance(node, dict):
            label = node.get("label")

            if label:
                return str(label)

        return fallback

    lines = [
        "digraph CancerAwarenessTemplate {",

        # IMPORTANT:
        # Use dot rather than neato/fixed coordinates.
        'graph [rankdir=TB, bgcolor="white", '
        'pad=0.30, nodesep=0.55, ranksep=0.85, '
        'splines=ortho, overlap=false];',

        'node [shape=box, style="rounded,filled", '
        'fontname="Arial", fontsize=10, '
        'margin="0.12,0.08", color="#666666", '
        'fillcolor="white"];',

        'edge [fontname="Arial", fontsize=8, '
        'color="#777777", arrowsize=0.65];',

        # --------------------------------------------------
        # CENTRAL NODE
        # --------------------------------------------------
        'early_detection ['
        'shape=ellipse, '
        'style="filled", '
        'fillcolor="#F4EEFF", '
        'color="#512DA8", '
        'penwidth=2.5, '
        'fontcolor="#2F1B69", '
        'fontsize=14, '
        'label="EARLY DETECTION OF CANCER\\n\\n'
        'Improves treatment outcomes, survival rates '
        'and quality of life"'
        '];',

        # --------------------------------------------------
        # OUTCOME
        # --------------------------------------------------
        'better_outcomes ['
        'shape=box, '
        'style="rounded,filled", '
        'fillcolor="#EEF8EE", '
        'color="#2E7D32", '
        'penwidth=2.0, '
        'fontcolor="#1B5E20", '
        'fontsize=12, '
        'label="BETTER OUTCOMES\\n\\n'
        'Early treatment\\n'
        'Higher survival rates\\n'
        'Improved quality of life\\n'
        'Reduced healthcare costs"'
        '];',
    ]

    # ======================================================
    # TEMPLATE MODULES
    # ======================================================

    modules = [
        (
            "module_blood_biomarkers",
            "Blood Tests & Biomarkers",
            "Detect cancer using biomarkers in body fluids",
            "#2E7D32",
            "E1",
        ),
        (
            "module_mammography",
            "Mammography for Breast Cancer",
            "Breast imaging used for early signs and screening",
            "#1565C0",
            "E2",
        ),
        (
            "module_prostate",
            "Prostate Cancer Detection",
            "Screening and detection for prostate cancer",
            "#512DA8",
            "E3",
        ),
        (
            "module_colorectal",
            "Colorectal Cancer Screening",
            "Recommended screening methods for colorectal cancer",
            "#EF6C00",
            "E4",
        ),
        (
            "module_diagnostics",
            "General Diagnostic Tests",
            "Tests used to confirm diagnosis and determine extent",
            "#00838F",
            "E5",
        ),
    ]

    # ------------------------------------------------------
    # Four upper modules
    # ------------------------------------------------------

    for key, title, description, color, evidence_id in modules:

        if key == "module_diagnostics":
            continue

        actual_title = get_node_label(key, title)

        lines.append(
            f'{node_id(key)} ['
            f'shape=box, '
            f'style="rounded,filled", '
            f'fillcolor="white", '
            f'color="{color}", '
            f'penwidth=2.0, '
            f'fontcolor="{color}", '
            f'label="{q(actual_title)} [{evidence_id}]\\n'
            f'{q(description)}"'
            f'];'
        )

    # ======================================================
    # SUBGROUPS
    # ======================================================

    subgroup_data = {
        "module_blood_biomarkers": [
            (
                "sample_types",
                "Sample Types",
                ["Blood", "Urine", "Saliva"],
            ),
            (
                "key_features",
                "Key Features",
                [
                    "Detects biomarkers",
                    "Rapid testing potential",
                    "Non-invasive testing potential",
                ],
            ),
            (
                "benefits",
                "Benefits",
                [
                    "Accessible",
                    "Efficient",
                    "Early detection",
                ],
            ),
        ],

        "module_mammography": [
            (
                "method",
                "Method",
                [
                    "Mammography (2-D)",
                    "3-D mammography / tomosynthesis",
                ],
            ),
            (
                "detects",
                "Detects",
                [
                    "Microcalcifications",
                    "Small tumors",
                    "Early signs",
                ],
            ),
            (
                "benefits",
                "Benefits",
                [
                    "Higher detection rate",
                    "Better for dense breast tissue",
                ],
            ),
        ],

        "module_prostate": [
            (
                "who",
                "Who",
                [
                    "Men over 50 / higher risk",
                    "Family history",
                    "Genetic risk",
                ],
            ),
            (
                "screening_methods",
                "Screening Methods",
                [
                    "PSA blood test",
                    "Digital rectal exam",
                    "MRI / imaging",
                ],
            ),
            (
                "benefits",
                "Benefits",
                [
                    "Detects early",
                    "Supports treatment planning",
                    "Monitors progression",
                ],
            ),
        ],

        "module_colorectal": [
            (
                "screening_methods",
                "Screening Methods",
                [
                    "Colonoscopy",
                    "Blood tests (FIT)",
                    "DNA stool tests",
                    "CT colonography",
                ],
            ),
            (
                "who_when",
                "Who & When",
                [
                    "Age / risk-based screening",
                    "Higher risk: earlier and more frequent",
                ],
            ),
            (
                "benefits",
                "Benefits",
                [
                    "Detects polyps & early cancer",
                    "Supports prevention",
                ],
            ),
        ],

        "module_diagnostics": [
            (
                "imaging_tests",
                "Imaging Tests",
                [
                    "Ultrasound",
                    "X-rays",
                    "CT scan",
                    "MRI",
                    "PET scan",
                ],
            ),
            (
                "laboratory_tests",
                "Laboratory Tests",
                [
                    "Blood tests",
                    "Urine tests",
                    "Tumor markers",
                ],
            ),
            (
                "tissue_sampling",
                "Tissue Sampling",
                [
                    "Biopsy",
                    "Fine needle aspiration",
                    "Endoscopic biopsy",
                ],
            ),
            (
                "purpose",
                "Purpose",
                [
                    "Confirm diagnosis",
                    "Determine cancer type",
                    "Assess stage",
                    "Guide treatment",
                ],
            ),
            (
                "outcome",
                "Outcome",
                [
                    "Accurate diagnosis",
                    "Treatment planning",
                    "Monitor response",
                ],
            ),
        ],
    }

    module_colors = {
        "module_blood_biomarkers": "#2E7D32",
        "module_mammography": "#1565C0",
        "module_prostate": "#512DA8",
        "module_colorectal": "#EF6C00",
        "module_diagnostics": "#00838F",
    }

    # ------------------------------------------------------
    # Create subgroup nodes
    # ------------------------------------------------------

    for module_key, subgroups in subgroup_data.items():

        color = module_colors[module_key]

        for subgroup_key, title, items in subgroups:

            full_key = f"{module_key}__{subgroup_key}"

            actual_title = get_node_label(
                full_key,
                title,
            )

            item_text = "\\n".join(
                f"- {item}"
                for item in items
            )

            lines.append(
                f'{node_id(full_key)} ['
                f'shape=box, '
                f'style="rounded,filled", '
                f'fillcolor="#FAFCFE", '
                f'color="{color}", '
                f'penwidth=1.2, '
                f'fontcolor="{color}", '
                f'fontsize=9, '
                f'label="{q(actual_title)}\\n'
                f'{q(item_text)}"'
                f'];'
            )

    # ======================================================
    # MODULE → SUBGROUP
    # ======================================================

    for module_key, subgroups in subgroup_data.items():

        for subgroup_key, _, _ in subgroups:

            full_key = f"{module_key}__{subgroup_key}"

            lines.append(
                f'{node_id(module_key)} -> '
                f'{node_id(full_key)} '
                f'[color="{module_colors[module_key]}", '
                f'penwidth=1.0, '
                f'arrowsize=0.5];'
            )

    # ======================================================
    # MODULE → CENTRAL NODE
    # ======================================================

    for module_key, _, _, color, _ in modules:

        if module_key == "module_diagnostics":
            continue

        lines.append(
            f'{node_id(module_key)} -> early_detection '
            f'[label="achieved through", '
            f'color="{color}", '
            f'fontcolor="{color}"];'
        )

    # ======================================================
    # CENTRAL → DIAGNOSTICS
    # ======================================================

    lines.append(
        f'{node_id("module_diagnostics")} '
        f'[shape=box, '
        f'style="rounded,filled", '
        f'fillcolor="white", '
        f'color="#00838F", '
        f'penwidth=2.0, '
        f'fontcolor="#00838F", '
        f'label="General Diagnostic Tests [E5]\\n'
        f'Tests used to confirm diagnosis and determine extent"];'
    )

    lines.append(
        'early_detection -> '
        f'{node_id("module_diagnostics")} '
        '[label="often followed by", '
        'color="#512DA8", '
        'fontcolor="#512DA8", '
        'penwidth=1.5];'
    )

    # ======================================================
    # DIAGNOSTICS → OUTCOME
    # ======================================================

    lines.append(
        f'{node_id("module_diagnostics")} -> '
        'better_outcomes '
        '[label="leads to", '
        'color="#2E7D32", '
        'fontcolor="#2E7D32", '
        'penwidth=2.0];'
    )

    # ======================================================
    # EVIDENCE SOURCES
    # ======================================================

    if sources:

        source_lines = []

        for source in sources:

            if not isinstance(source, dict):
                continue

            sid = source.get("id", "")
            title = source.get("title", "")

            if sid and title:
                source_lines.append(
                    f"[{sid}] {title}"
                )

        if source_lines:

            lines.append(
                'evidence_sources ['
                'shape=box, '
                'style="rounded,filled", '
                'fillcolor="white", '
                'color="#999999", '
                'fontcolor="#333333", '
                'fontsize=8, '
                f'label="{q("EVIDENCE SOURCES")}\\n'
                f'{q(chr(10).join(source_lines))}"'
                '];'
            )

            lines.append(
                'better_outcomes -> evidence_sources '
                '[style=invis];'
            )

    lines.append("}")

    return "\n".join(lines)