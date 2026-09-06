"""
Complete End-to-End Execution Script for PS26189: AI-Powered Criminal Network Analysis Pipeline
Phases 1-4: Ingestion, Resolution, Graph Construction, Analytics, Pattern Detection, Explainable Risk Scoring & Alerts.

Usage:
    python run_pipeline.py [--input path/to/sample.json] [--output-dir output/] [--use-llm]
"""

import argparse
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fir_intelligence.phase1_extraction.entity_store import EntityStore
from fir_intelligence.phase1_extraction.extractors import extract_all_mentions
from fir_intelligence.phase1_extraction.ingestion import (
    load_firs_from_csv,
    load_firs_from_json,
)
from fir_intelligence.phase1_extraction.llm_client import NemotronClient
from fir_intelligence.phase1_extraction.resolution import EntityResolver

from fir_intelligence.phase2_graph.graph_builder import GraphBuilder
from fir_intelligence.phase2_graph.llm_relationship_extractor import extract_llm_relationships
from fir_intelligence.phase2_graph.relationship_rules import (
    extract_cooccurrence_relationships,
    extract_structured_field_relationships,
)
from fir_intelligence.phase2_graph.visualization import (
    render_analytics_graph_debug,
    render_graph_debug,
)

from fir_intelligence.phase3_analytics.analyzer import GraphAnalyzer
from fir_intelligence.phase3_analytics.models import Phase3Config

from fir_intelligence.phase4_scoring.alert_generator import AlertGenerator
from fir_intelligence.phase4_scoring.models import ScoringConfig


def run_pipeline(
    input_path: Path,
    output_dir: Path,
    use_llm: bool = False,
    nvidia_api_key: str = "",
) -> Dict:
    print("==========================================================================")
    print("=== PS26189: AI-Powered Criminal Network Analysis System (Phases 1-4) ===")
    print("==========================================================================")
    print(f"Loading FIR records from: {input_path}")

    # Initialize Nemotron Client if LLM mode requested
    llm_client = None
    if use_llm:
        api_key = nvidia_api_key or os.getenv("NVIDIA_API_KEY", "")
        llm_client = NemotronClient(api_key=api_key)
        if llm_client.is_available():
            print("[OK] Nemotron LLM Client Initialized successfully.")
        else:
            print("[!] Warning: --use-llm requested but NVIDIA_API_KEY is missing/invalid. Falling back to deterministic mode.")
            use_llm = False

    mode_str = "Nemotron-Augmented (LLM + Regex + RapidFuzz)" if use_llm else "Deterministic Baseline (Regex + RapidFuzz)"
    print(f"Execution Mode: {mode_str}")

    # --- PHASE 1: Ingestion, Extraction & Resolution ---
    print("\n[Phase 1] FIR Extraction & Entity Resolution...")
    if input_path.suffix.lower() == ".csv":
        firs = load_firs_from_csv(input_path)
    else:
        firs = load_firs_from_json(input_path)

    print(f"  - Loaded {len(firs)} FIR record(s).")

    all_mentions = []
    for fir in firs:
        mentions = extract_all_mentions(fir, use_llm=use_llm, llm_client=llm_client)
        all_mentions.extend(mentions)

    llm_count = sum(1 for m in all_mentions if "llm" in m.field_source)
    print(f"  - Extracted {len(all_mentions)} total entity mentions across all FIRs ({llm_count} via Nemotron NER).")

    resolver = EntityResolver(
        fuzzy_merge_threshold=0.82,
        candidate_merge_threshold=0.70,
        use_llm=use_llm,
        llm_client=llm_client,
    )
    entities, candidate_merges, merge_history = resolver.resolve_mentions(all_mentions)

    store = EntityStore(
        entities=entities,
        candidate_merges=candidate_merges,
        merge_history=merge_history,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "deduplicated_entities.json"
    csv_path = output_dir / "entities_summary.csv"

    store.export_json(json_path)
    store.export_csv(csv_path)
    print(f"  - Phase 1 Complete: {len(entities)} unique entities exported to {json_path}")

    # --- PHASE 2: Relationship Mining & Graph Construction ---
    print("\n[Phase 2] Relationship Mining & Graph Construction...")
    struct_rels = extract_structured_field_relationships(store)
    cooccur_rels = extract_cooccurrence_relationships(store)
    print(f"  - Extracted {len(struct_rels)} structured-field relationships.")
    print(f"  - Extracted {len(cooccur_rels)} co-occurrence relationships.")

    llm_rels = []
    if use_llm and llm_client:
        llm_rels = extract_llm_relationships(firs, store, llm_client)
        print(f"  - Inferred {len(llm_rels)} narrative relationships via Nemotron.")

    all_relationships = struct_rels + cooccur_rels + llm_rels

    builder = GraphBuilder()
    nx_graph = builder.build_from_entity_store(store, all_relationships)

    graph_json_path = output_dir / "network_graph.json"
    graph_graphml_path = output_dir / "network_graph.graphml"

    builder.export_json(nx_graph, graph_json_path)
    builder.export_graphml(nx_graph, graph_graphml_path)

    png_path = output_dir / "network_graph.png"
    html_path = output_dir / "network_graph.html"
    render_graph_debug(nx_graph, output_png=png_path, output_html=html_path)
    print(f"  - Phase 2 Complete: Graph constructed with {nx_graph.number_of_nodes()} nodes and {nx_graph.number_of_edges()} edges.")

    # --- PHASE 3: Graph Analytics & Pattern Detection ---
    print("\n[Phase 3] Graph Analytics & Pattern Detection...")
    analyzer = GraphAnalyzer(Phase3Config())
    analysis_result = analyzer.run_full_analysis(nx_graph)

    analysis_json_path = output_dir / "graph_analysis.json"
    analyzer.export_json(analysis_result, analysis_json_path)

    analytics_png_path = output_dir / "network_graph_analytics.png"
    render_analytics_graph_debug(nx_graph, analysis_result, analytics_png_path)
    print(f"  - Phase 3 Complete: Analyzed {len(analysis_result.communities)} communities and detected {len(analysis_result.patterns)} pattern matches.")

    # --- PHASE 4: Explainable Risk Scoring & Alerts ---
    print("\n[Phase 4] Explainable Risk Scoring & Alert Generation...")
    alert_gen = AlertGenerator(ScoringConfig(min_alert_tier="MEDIUM"))
    alerts_payload = alert_gen.generate_alerts(
        analysis_result,
        entity_store=store,
        use_llm=use_llm,
        llm_client=llm_client,
    )

    alerts_json_path = output_dir / "alerts.json"
    alert_gen.export_json(alerts_payload, alerts_json_path)
    print(f"  - Phase 4 Complete: Exported final alerts to {alerts_json_path}")

    # --- FINAL EXECUTIVE DEMO SUMMARY ---
    print("\n==========================================================================")
    print("===                  CRIMINAL NETWORK INTELLIGENCE DEMO                ===")
    print("==========================================================================")

    e_alerts = alerts_payload.get("entity_alerts", [])
    c_alerts = alerts_payload.get("cluster_alerts", [])

    print(f"\n[!] HIGH/MEDIUM RISK ALERTS GENERATED: {len(e_alerts)} Entity Alerts, {len(c_alerts)} Cluster Alerts")

    print("\n--- TOP SUSPICIOUS ENTITY ALERTS ---")
    for alert in e_alerts[:5]:
        ent_obj = store.get_entity_by_id(alert["target_id"])
        disp_name = ent_obj.display_value if ent_obj else alert["target_id"]
        print(f"\n  [!] Risk Score: {alert['risk_score']}/100 -- {alert['risk_tier']} RISK | Target: {disp_name} ({alert['target_id']})")
        print("      Reasons:")
        for r in alert["reasons"]:
            print(f"        - {r}")
        print("      Contributing Factors Breakdown:")
        for cf in alert["contributing_factors"]:
            print(f"        - {cf['factor_name']:<25}: +{cf['points_contributed']} pts ({cf['description']})")

    if c_alerts:
        print("\n--- SUSPICIOUS CLUSTER ALERTS ---")
        for ca in c_alerts:
            print(f"\n  [!] Cluster Alert: {ca['target_id']} | Risk Score: {ca['risk_score']}/100 -- {ca['risk_tier']}")
            print("      Reasons:")
            for r in ca["reasons"]:
                print(f"        - {r}")

    print("\n==========================================================================")
    print("=== Pipeline Completed Successfully. All Phase 1-4 Artifacts Exported. ===")
    print("==========================================================================")

    return alerts_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PS26189 Criminal Network Analysis Pipeline")
    default_input = Path(__file__).parent / "tests" / "fixtures" / "sample_firs.json"
    default_output = Path(__file__).parent / "output"

    env_use_llm = os.getenv("USE_LLM_EXTRACTION", "False").lower() in ("true", "1", "yes")

    parser.add_argument("--input", type=Path, default=default_input, help="Path to input FIR JSON or CSV file")
    parser.add_argument("--output-dir", type=Path, default=default_output, help="Path to output directory")
    parser.add_argument("--use-llm", action="store_true", default=env_use_llm, help="Enable Nemotron LLM narrative extraction, merge reasoning & reason polishing")

    args = parser.parse_args()
    run_pipeline(
        args.input,
        args.output_dir,
        use_llm=args.use_llm,
    )
