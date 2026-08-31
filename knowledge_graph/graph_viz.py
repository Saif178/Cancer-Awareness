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
    """Render a clean fixed-layout diagram closely matching the supplied template."""
    nodes=template_graph.get("nodes",{})
    sources={s["id"]:s for s in template_graph.get("sources",[])}

    def he(s):
        return escape(str(s), quote=True)

    positions={
        "module_blood_biomarkers": (-520,230),
        "module_mammography": (520,230),
        "module_prostate": (-520,10),
        "module_colorectal": (520,10),
        "module_diagnostics": (0,-230),
    }
    subgroup_xy={
        "module_blood_biomarkers__sample_types": (-650,145),
        "module_blood_biomarkers__key_features": (-520,145),
        "module_blood_biomarkers__benefits": (-390,145),
        "module_mammography__method": (390,145),
        "module_mammography__detects": (520,145),
        "module_mammography__benefits": (650,145),
        "module_prostate__who": (-650,-80),
        "module_prostate__screening_methods": (-520,-80),
        "module_prostate__benefits": (-390,-80),
        "module_colorectal__screening_methods": (390,-80),
        "module_colorectal__who_when": (520,-80),
        "module_colorectal__benefits": (650,-80),
        "module_diagnostics__imaging_tests": (-400,-330),
        "module_diagnostics__laboratory_tests": (-200,-330),
        "module_diagnostics__tissue_sampling": (0,-330),
        "module_diagnostics__purpose": (200,-330),
        "module_diagnostics__outcome": (400,-330),
    }
    descriptions={
        "module_blood_biomarkers":"Detect cancer using biomarkers in body fluids",
        "module_mammography":"Breast imaging used for early signs and screening",
        "module_prostate":"Screening and detection for prostate cancer",
        "module_colorectal":"Recommended screening methods for colorectal cancer",
        "module_diagnostics":"Tests used to confirm diagnosis and determine extent",
    }
    subgroup_items={
        "module_blood_biomarkers__sample_types":["Blood","Urine","Saliva"],
        "module_blood_biomarkers__key_features":["Detects biomarkers","Rapid testing potential","Non-invasive testing potential"],
        "module_blood_biomarkers__benefits":["Accessible","Efficient","Early detection"],
        "module_mammography__method":["Mammography (2-D)","3-D mammography / tomosynthesis"],
        "module_mammography__detects":["Microcalcifications","Small tumors","Early signs"],
        "module_mammography__benefits":["Higher detection rate","Better for dense breast tissue"],
        "module_prostate__who":["Men over 50 / higher risk","Family history","Genetic risk"],
        "module_prostate__screening_methods":["PSA blood test","Digital rectal exam","MRI / imaging"],
        "module_prostate__benefits":["Detects early","Supports treatment planning","Monitors progression"],
        "module_colorectal__screening_methods":["Colonoscopy","Blood tests (FIT)","DNA stool tests","CT colonography"],
        "module_colorectal__who_when":["Age / risk-based screening","Higher risk: earlier and more frequent"],
        "module_colorectal__benefits":["Detects polyps & early cancer","Supports prevention"],
        "module_diagnostics__imaging_tests":["Ultrasound","X-rays","CT scan","MRI","PET scan"],
        "module_diagnostics__laboratory_tests":["Blood tests","Urine tests","Tumor markers"],
        "module_diagnostics__tissue_sampling":["Biopsy","Fine needle aspiration","Endoscopic biopsy"],
        "module_diagnostics__purpose":["Confirm diagnosis","Determine cancer type","Assess stage","Guide treatment"],
        "module_diagnostics__outcome":["Accurate diagnosis","Treatment planning","Monitor response"],
    }
    module_source={
        "module_blood_biomarkers":"E1","module_mammography":"E2",
        "module_prostate":"E3","module_colorectal":"E4","module_diagnostics":"E5"
    }

    lines=[
        "digraph CancerAwarenessTemplate {",
        'graph [layout=neato, overlap=false, splines=true, bgcolor="white", pad=0.35, outputorder=edgesfirst, '
        'label="CANCER EARLY DETECTION KNOWLEDGE GRAPH\\nFrom Screening to Better Outcomes", '
        'labelloc=t, labeljust=c, fontsize=18, fontname="Arial"];',
        'node [fontname="Arial", fontsize=10, margin="0.10,0.06", pin=true];',
        'edge [fontname="Arial", fontsize=8, arrowsize=0.65, penwidth=1.3];'
    ]

    lines.append(
        'n_early_detection_of_cancer [pos="0,0!", shape=ellipse, width=2.6, height=1.5, '
        'style="filled", fillcolor="#F4EEFF", color="#512DA8", penwidth=2.2, fontcolor="#2F1B69", '
        'label=< <B>Early Detection</B><BR/><B>of Cancer</B><BR/><BR/>'
        'Improves treatment outcomes, survival<BR/>rates and quality of life >];'
    )
    lines.append(
        'n_better_outcomes [pos="720,-230!", shape=box, width=2.35, '
        'style="rounded,filled", fillcolor="#EEF8EE", color="#2E7D32", penwidth=1.8, '
        'fontcolor="#1B5E20", label=< <B>BETTER OUTCOMES</B><BR/><BR/>'
        '• Early treatment<BR/>• Higher survival rates<BR/>• Improved quality of life<BR/>'
        '• Reduced healthcare costs >];'
    )

    for mid,(x,y) in positions.items():
        n=nodes.get(mid,{})
        col=COLOR_HEX.get(n.get("color"),"#666666")
        eid=module_source.get(mid)
        title=n.get("label","")
        if eid: title += f" [{eid}]"
        desc=descriptions.get(mid,"")
        lines.append(
            f'n_{_node_id(mid)[2:]} [pos="{x},{y}!", shape=box, width=3.15, height=0.72, '
            f'style="rounded,filled", fillcolor="#FFFFFF", color="{col}", penwidth=2.0, fontcolor="{col}", '
            f'label=< <B>{he(title)}</B><BR/><FONT POINT-SIZE="9">{he(desc)}</FONT> >];'
        )

    for sid,(x,y) in subgroup_xy.items():
        n=nodes.get(sid,{})
        col=COLOR_HEX.get(n.get("color"),"#777777")
        label=n.get("label","")
        items=subgroup_items.get(sid, [])
        body="<BR/>".join("• "+he(i) for i in items)
        lines.append(
            f'n_{_node_id(sid)[2:]} [pos="{x},{y}!", shape=box, width=1.95, height=0.88, '
            f'style="rounded,filled", fillcolor="#FAFCFE", color="{col}", penwidth=1.15, fontcolor="{col}", '
            f'label=< <B>{he(label)}</B><BR/>{body} >];'
        )

    # Connect each module to its three/five template subgroups.
    for mid in positions:
        col=COLOR_HEX.get(nodes.get(mid,{}).get("color"),"#666666")
        for sid in subgroup_xy:
            if sid.startswith(mid+"__"):
                lines.append(
                    f'n_{_node_id(mid)[2:]} -> n_{_node_id(sid)[2:]} '
                    f'[color="{col}", penwidth=1.0, arrowsize=0.5];'
                )

    # Main template relationships.
    for mid in ("module_blood_biomarkers","module_mammography","module_prostate","module_colorectal"):
        col=COLOR_HEX.get(nodes.get(mid,{}).get("color"),"#555555")
        lines.append(
            f'n_{_node_id(mid)[2:]} -> n_early_detection_of_cancer '
            f'[label="achieved through", color="{col}", fontcolor="{col}"];'
        )
    lines.append(
        'n_early_detection_of_cancer -> n_module_diagnostics '
        '[label="often followed by", color="#512DA8", fontcolor="#512DA8"];'
    )
    lines.append(
        'n_module_diagnostics -> n_better_outcomes '
        '[label="leads to", color="#2E7D32", fontcolor="#2E7D32", penwidth=1.8];'
    )

    # Evidence footer, matching the source strip in the supplied template.
    source_text=[]
    for eid in ("E1","E2","E3","E4","E5","E6"):
        if eid in sources:
            source_text.append(f"<B>[{he(eid)}]</B> {he(sources[eid]['title'])}")
    if source_text:
        footer="<BR/>".join(source_text)
        lines.append(
            'evidence_sources [pos="0,-480!", shape=box, width=11.5, height=0.95, '
            'style="rounded,filled", fillcolor="#FFFFFF", color="#999999", penwidth=1.0, '
            'fontcolor="#333333", fontsize=8, '
            f'label=< <B>EVIDENCE SOURCES</B><BR/>{footer} >];'
        )

    lines.append("}")
    return "\n".join(lines)
