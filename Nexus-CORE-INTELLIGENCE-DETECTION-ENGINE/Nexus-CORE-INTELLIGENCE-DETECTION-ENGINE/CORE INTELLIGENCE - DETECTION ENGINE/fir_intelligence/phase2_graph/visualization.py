"""
Lightweight debug visualization module for rendering NetworkX graphs using matplotlib and pyvis.
Supports coloring by entity type (Phase 2) or community ID / PageRank sizing (Phase 3).
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union
import networkx as nx
import matplotlib.pyplot as plt


NODE_COLOR_MAP = {
    "Person": "skyblue",
    "Phone": "lightgreen",
    "Location": "salmon",
    "Organization": "mediumpurple",
    "Account": "gold",
    "Transaction": "lightcoral",
    "Device": "lightgray",
    "Email": "turquoise",
    "IP": "khaki",
    "CaseRef": "plum",
    "Event": "orange",
}

COMMUNITY_COLORS = [
    "skyblue", "lightgreen", "salmon", "gold", "mediumpurple",
    "turquoise", "lightcoral", "plum", "khaki", "lightgray"
]


def render_graph_debug(
    graph: nx.MultiDiGraph,
    output_png: Union[str, Path],
    output_html: Optional[Union[str, Path]] = None,
) -> None:
    """
    Renders static PNG visualization using matplotlib and optionally interactive HTML visualization using pyvis.
    Colored by Entity type.
    """
    png_path = Path(output_png)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    if graph.number_of_nodes() == 0:
        print("Warning: Graph is empty, skipping visualization.")
        return

    fig, ax = plt.subplots(figsize=(14, 10))
    pos = nx.spring_layout(graph, seed=42, k=0.5)

    node_colors = []
    labels = {}
    for n, data in graph.nodes(data=True):
        ent_type = data.get("type", "Unknown")
        node_colors.append(NODE_COLOR_MAP.get(ent_type, "lightgray"))
        labels[n] = f"{data.get('display_value', n)}\n({ent_type})"

    nx.draw_networkx_nodes(graph, pos, node_color=node_colors, node_size=800, alpha=0.9, ax=ax)
    nx.draw_networkx_edges(graph, pos, arrowstyle="->", arrowsize=15, edge_color="gray", alpha=0.6, ax=ax)
    nx.draw_networkx_labels(graph, pos, labels=labels, font_size=8, font_family="sans-serif", ax=ax)

    ax.set_title("PS26189 Criminal Network Graph (Phase 2 Sanity Check)", fontsize=14, fontweight="bold")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(png_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"[OK] Rendered debug graph image: {png_path}")

    if output_html:
        html_path = Path(output_html)
        try:
            from pyvis.network import Network
            net = Network(height="750px", width="100%", directed=True, notebook=False)
            
            for n, data in graph.nodes(data=True):
                ent_type = data.get("type", "Unknown")
                color = NODE_COLOR_MAP.get(ent_type, "gray")
                label = data.get("display_value", n)
                title = f"ID: {n}<br>Type: {ent_type}<br>Canonical: {data.get('canonical_value', '')}<br>FIRs: {data.get('source_FIR_ids', '')}"
                net.add_node(n, label=label, title=title, color=color)

            for u, v, k, data in graph.edges(data=True, keys=True):
                rel_type = data.get("relation_type", "link")
                weight = data.get("weight", 1.0)
                evidence = data.get("evidence", "")
                net.add_edge(u, v, title=f"Type: {rel_type}<br>Weight: {weight}<br>Evidence: {evidence}", label=rel_type)

            net.write_html(str(html_path))
            print(f"[OK] Rendered interactive HTML graph: {html_path}")
        except Exception as e:
            print(f"Warning: Failed to render pyvis interactive HTML graph: {e}")


def render_analytics_graph_debug(
    graph: nx.MultiDiGraph,
    analysis_result: Any,
    output_png: Union[str, Path],
) -> None:
    """
    Renders static PNG visualization with nodes sized by PageRank and colored by Louvain Community ID.
    """
    png_path = Path(output_png)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    if graph.number_of_nodes() == 0:
        return

    fig, ax = plt.subplots(figsize=(14, 10))
    pos = nx.spring_layout(graph, seed=42, k=0.5)

    node_colors = []
    node_sizes = []
    labels = {}

    metrics_map = analysis_result.entity_metrics

    for n, data in graph.nodes(data=True):
        m = metrics_map.get(n)
        if m:
            comm_id = m.community_id
            pr = m.centrality.pagerank
            flags = ",".join(m.pattern_flags) if m.pattern_flags else ""
        else:
            comm_id = 0
            pr = 0.01
            flags = ""

        color = COMMUNITY_COLORS[(comm_id - 1) % len(COMMUNITY_COLORS)] if comm_id > 0 else "lightgray"
        node_colors.append(color)

        # Sizing proportional to PageRank
        size = max(500, int(pr * 15000))
        node_sizes.append(size)

        lbl = f"{data.get('display_value', n)}\n[Comm:{comm_id}]"
        if flags:
            lbl += f"\n! {flags}"
        labels[n] = lbl

    nx.draw_networkx_nodes(graph, pos, node_color=node_colors, node_size=node_sizes, alpha=0.9, ax=ax)
    nx.draw_networkx_edges(graph, pos, arrowstyle="->", arrowsize=15, edge_color="gray", alpha=0.5, ax=ax)
    nx.draw_networkx_labels(graph, pos, labels=labels, font_size=7, font_family="sans-serif", ax=ax)

    ax.set_title("PS26189 Network Analytics (Node Size = PageRank, Color = Community)", fontsize=13, fontweight="bold")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(png_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"[OK] Rendered analytics debug graph image: {png_path}")
