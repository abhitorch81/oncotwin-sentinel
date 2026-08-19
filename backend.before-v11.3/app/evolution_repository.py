"""CockroachDB-backed mutation evolution graph and tandem-agent council."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from .config import get_settings
from .database import get_engine


def _rows(connection: Any, statement: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(text(statement), parameters).mappings().all()]


def _number(value: Any) -> float:
    return float(value if value is not None else 0)


def _receipt(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def evolution_graph(synthetic_code: str) -> dict[str, Any] | None:
    settings = get_settings()
    parameters = {"tenant_id": settings.memory_tenant_id, "synthetic_code": synthetic_code.upper()}
    with get_engine().connect() as connection:
        patient = connection.execute(text(
            "SELECT tenant_id, patient_id, synthetic_code, cancer_type, cancer_stage, metadata "
            "FROM patients WHERE tenant_id=CAST(:tenant_id AS UUID) AND synthetic_code=:synthetic_code"
        ), parameters).mappings().first()
        if patient is None:
            return None
        scope = {"tenant_id": str(patient["tenant_id"]), "patient_id": str(patient["patient_id"])}
        clones = _rows(connection, "SELECT clone_id, clone_label, generation, prevalence, fitness, risk_score, mutations, first_seen, last_seen, evidence FROM evolution_clones WHERE tenant_id=CAST(:tenant_id AS UUID) AND patient_id=CAST(:patient_id AS UUID) ORDER BY generation, prevalence DESC", scope)
        edges = _rows(connection, "SELECT parent_clone_id, child_clone_id, mechanism, transition_probability, evidence, created_at FROM evolution_edges WHERE tenant_id=CAST(:tenant_id AS UUID) AND patient_id=CAST(:patient_id AS UUID) ORDER BY created_at", scope)
        events = _rows(connection, "SELECT mutation_event_id, clone_id, gene, alteration, event_time, variant_allele_fraction, evidence_strength, source_name, evidence_hash FROM mutation_events WHERE tenant_id=CAST(:tenant_id AS UUID) AND patient_id=CAST(:patient_id AS UUID) ORDER BY event_time", scope)
        insights = _rows(connection, "SELECT insight_id, snapshot_id, agent_name, insight_type, conclusion, confidence, evidence_refs, status, created_at FROM evolution_agent_insights WHERE tenant_id=CAST(:tenant_id AS UUID) AND patient_id=CAST(:patient_id AS UUID) ORDER BY created_at DESC LIMIT 20", scope)
        memories = _rows(connection, "SELECT memory_id, title, confidence, source_agent, created_at FROM agent_memories WHERE tenant_id=CAST(:tenant_id AS UUID) AND patient_id=CAST(:patient_id AS UUID) ORDER BY created_at DESC LIMIT 5", scope)

    for clone in clones:
        clone["prevalence"]=_number(clone["prevalence"]); clone["fitness"]=_number(clone["fitness"]); clone["risk_score"]=_number(clone["risk_score"])
    for edge in edges: edge["transition_probability"]=_number(edge["transition_probability"])
    for event in events:
        event["variant_allele_fraction"]=_number(event["variant_allele_fraction"]); event["evidence_strength"]=_number(event["evidence_strength"])
    for insight in insights: insight["confidence"]=_number(insight["confidence"])
    receipt_payload={"patient_id":str(patient["patient_id"]),"clones":[str(x["clone_id"]) for x in clones],"edges":[[str(x["parent_clone_id"]),str(x["child_clone_id"])] for x in edges],"events":[x["evidence_hash"] for x in events]}
    receipt=hashlib.sha256(json.dumps(receipt_payload,sort_keys=True).encode()).hexdigest()
    generations=sorted({int(x["generation"]) for x in clones})
    return {"source":"cockroachdb-evolution-graph","synthetic":True,"research_only":True,"clinical_action_allowed":False,"patient":dict(patient),"clones":clones,"edges":edges,"mutation_events":events,"prior_agent_insights":insights,"persistent_memories":memories,"timeline":{"generations":generations,"latest_generation":max(generations,default=0)},"graph_receipt":{"sha256":receipt,"clone_count":len(clones),"edge_count":len(edges),"mutation_count":len(events)}}


def _project(graph: dict[str, Any], horizon: int) -> list[dict[str, Any]]:
    projected=[]
    for clone in graph["clones"]:
        prevalence=_number(clone["prevalence"]); fitness=_number(clone["fitness"]); risk=_number(clone["risk_score"])
        trajectory=[]
        for step in range(1,horizon+1):
            growth=(fitness-.5)*.17 + risk*.025
            prevalence=max(0,min(.95,prevalence*(1+growth)))
            trajectory.append({"generation":int(clone["generation"])+step,"prevalence":round(prevalence,4),"uncertainty":round(.07+step*.035,4)})
        projected.append({"clone_id":str(clone["clone_id"]),"clone_label":clone["clone_label"],"trajectory":trajectory})
    return projected


def run_evolution_council(synthetic_code: str, horizon: int = 4) -> dict[str, Any] | None:
    graph=evolution_graph(synthetic_code)
    if graph is None: return None
    clones=graph["clones"]
    if not clones: return {**graph,"council":[],"projection":[],"decision":"NO_EVOLUTION_DATA"}
    dominant=max(clones,key=lambda x:x["prevalence"]); emerging=max(clones,key=lambda x:x["fitness"]*x["risk_score"])
    weak=[x for x in graph["mutation_events"] if x["evidence_strength"]<.7]
    mutation_names=[f"{m['gene']} {m['alteration']}" for m in graph["mutation_events"]]
    memory_titles=[m["title"] for m in graph["persistent_memories"]]
    decision="HOLD_RESEARCH_CLAIM" if emerging["risk_score"]>=.8 or weak else "MONITOR_WITH_REVIEW"
    council=[
      {"agent":"Genomic Cartographer","role":"maps acquired alterations","finding":f"Mapped {len(clones)} clones and {len(graph['edges'])} supported evolutionary transitions; observed {', '.join(mutation_names)}.","confidence":.94,"handoff_to":"Clonal Evolution Forecaster"},
      {"agent":"Clonal Evolution Forecaster","role":"simulates competitive fitness","finding":f"{emerging['clone_label']} has the highest fitness-risk product; projection uncertainty expands with horizon.","confidence":.88,"handoff_to":"Evidence Challenger"},
      {"agent":"Evidence Challenger","role":"attacks unsupported conclusions","finding":f"Flagged {len(weak)} low-strength mutation event(s); inferred branches cannot be promoted to fact.","confidence":.91,"handoff_to":"Memory Sentinel"},
      {"agent":"Memory Sentinel","role":"recalls prior CockroachDB episodes","finding":f"Rehydrated {len(memory_titles)} persistent memories" + (f", including {memory_titles[0]}." if memory_titles else "; no prior memory may be assumed."),"confidence":.95 if memory_titles else .5,"handoff_to":"Safety Governor"},
      {"agent":"Safety Governor","role":"enforces research boundary","finding":f"Decision: {decision}. Human review is mandatory; no clinical action is generated.","confidence":.99,"handoff_to":"Human Reviewer"},
    ]
    projection=_project(graph,horizon)
    graph_receipt=graph["graph_receipt"]["sha256"]
    snapshot_id=str(uuid.uuid5(uuid.NAMESPACE_URL,f"oncotwin:{synthetic_code}:{graph_receipt}"))
    scope={"tenant_id":str(graph["patient"]["tenant_id"]),"patient_id":str(graph["patient"]["patient_id"]),"snapshot_id":snapshot_id,"receipt":graph_receipt,"generation":graph["timeline"]["latest_generation"],"dominant":str(dominant["clone_id"]),"decision":decision,"projection":json.dumps(projection),"council":json.dumps(council)}
    with get_engine().begin() as connection:
        connection.execute(text("INSERT INTO evolution_snapshots (tenant_id,patient_id,snapshot_id,graph_receipt,generation,dominant_clone_id,decision,projection,agent_council,human_review_required) VALUES (CAST(:tenant_id AS UUID),CAST(:patient_id AS UUID),CAST(:snapshot_id AS UUID),:receipt,:generation,CAST(:dominant AS UUID),:decision,CAST(:projection AS JSONB),CAST(:council AS JSONB),true) ON CONFLICT (tenant_id,patient_id,graph_receipt) DO NOTHING"),scope)
        for index,insight in enumerate(council):
            insight_id=str(uuid.uuid5(uuid.NAMESPACE_URL,f"{snapshot_id}:{insight['agent']}"))
            connection.execute(text("INSERT INTO evolution_agent_insights (tenant_id,patient_id,insight_id,snapshot_id,agent_name,insight_type,conclusion,confidence,evidence_refs,status) VALUES (CAST(:tenant_id AS UUID),CAST(:patient_id AS UUID),CAST(:insight_id AS UUID),CAST(:snapshot_id AS UUID),:agent,:kind,:conclusion,:confidence,CAST(:refs AS JSONB),'HUMAN_REVIEW_REQUIRED') ON CONFLICT DO NOTHING"),{**scope,"insight_id":insight_id,"agent":insight["agent"],"kind":insight["role"],"conclusion":insight["finding"],"confidence":insight["confidence"],"refs":json.dumps({"graph_receipt":graph_receipt,"sequence":index+1})})
    decision_receipt=hashlib.sha256(json.dumps({"graph_receipt":graph_receipt,"snapshot_id":snapshot_id,"decision":decision,"council":council,"projection":projection},sort_keys=True).encode()).hexdigest()
    return {"ok":True,"source":"cockroachdb-evolution-council","synthetic":True,"research_only":True,"clinical_action_allowed":False,"snapshot_id":snapshot_id,"graph_receipt":graph_receipt,"decision_receipt":decision_receipt,"decision":decision,"human_review_required":True,"dominant_clone":{"clone_id":str(dominant["clone_id"]),"clone_label":dominant["clone_label"],"prevalence":dominant["prevalence"]},"emerging_clone":{"clone_id":str(emerging["clone_id"]),"clone_label":emerging["clone_label"],"risk_score":emerging["risk_score"]},"council":council,"projection":projection,"horizon":horizon}


def evolution_memory_replay(synthetic_code: str) -> dict[str, Any] | None:
    """Rehydrate immutable observations, forecasts and the latest prediction delta."""
    graph = evolution_graph(synthetic_code)
    if graph is None:
        return None
    scope = {
        "tenant_id": str(graph["patient"]["tenant_id"]),
        "patient_id": str(graph["patient"]["patient_id"]),
    }
    with get_engine().connect() as connection:
        frames = _rows(connection, "SELECT frame_id, generation, observed_at, clone_distribution, evidence_refs, frame_receipt, source_name, created_at FROM evolution_memory_frames WHERE tenant_id=CAST(:tenant_id AS UUID) AND patient_id=CAST(:patient_id AS UUID) ORDER BY generation, observed_at", scope)
        paths = _rows(connection, "SELECT path_id, base_frame_id, scenario, pressure_mode, horizon, probability, trajectories, agent_votes, memory_refs, path_receipt, created_at FROM evolution_path_hypotheses WHERE tenant_id=CAST(:tenant_id AS UUID) AND patient_id=CAST(:patient_id AS UUID) ORDER BY created_at DESC LIMIT 12", scope)
        reconciliations = _rows(connection, "SELECT reconciliation_id, path_id, observed_frame_id, divergence_score, surprises, status, receipt, created_at FROM evolution_memory_reconciliations WHERE tenant_id=CAST(:tenant_id AS UUID) AND patient_id=CAST(:patient_id AS UUID) ORDER BY created_at DESC LIMIT 12", scope)
        snapshots = connection.execute(text("SELECT count(*) FROM evolution_snapshots WHERE tenant_id=CAST(:tenant_id AS UUID) AND patient_id=CAST(:patient_id AS UUID)"), scope).scalar_one()
    for path in paths:
        path["probability"] = _number(path["probability"])
    for item in reconciliations:
        item["divergence_score"] = _number(item["divergence_score"])
    deltas: list[dict[str, Any]] = []
    if len(frames) > 1:
        previous = frames[-2]["clone_distribution"]
        latest = frames[-1]["clone_distribution"]
        clone_labels = {str(item["clone_id"]): item["clone_label"] for item in graph["clones"]}
        for clone_id in sorted(set(previous) | set(latest)):
            delta = _number(latest.get(clone_id)) - _number(previous.get(clone_id))
            if abs(delta) >= .015:
                deltas.append({"clone_id": clone_id, "clone_label": clone_labels.get(clone_id, "Unknown clone"), "delta": round(delta, 4), "signal": "expanding" if delta > 0 else "contracting"})
        deltas.sort(key=lambda item: abs(item["delta"]), reverse=True)
    return {
        "ok": True,
        "source": "cockroachdb-persistent-evolution-memory",
        "restart_rehydratable": True,
        "synthetic": True,
        "research_only": True,
        "clinical_action_allowed": False,
        "frames": frames,
        "saved_paths": paths,
        "reconciliations": reconciliations,
        "latest_deltas": deltas,
        "memory_utility": {
            "frames_recalled": len(frames),
            "paths_remembered": len(paths),
            "council_snapshots_recalled": int(snapshots),
            "divergence_events": len(reconciliations),
            "temporal_span_days": (frames[-1]["observed_at"] - frames[0]["observed_at"]).days if len(frames) > 1 else 0,
            "utility": "History changes path probabilities and exposes forecast-versus-observation drift.",
        },
        "replay_receipt": _receipt({"frames": [item["frame_receipt"] for item in frames], "paths": [item["path_receipt"] for item in paths]}),
    }


def _scenario_projection(graph: dict[str, Any], horizon: int, scenario: str, pressure_mode: str) -> list[dict[str, Any]]:
    pressure = {"low": .65, "balanced": 1.0, "high": 1.35}[pressure_mode]
    clones = graph["clones"]
    current = {str(item["clone_id"]): _number(item["prevalence"]) for item in clones}
    total = sum(current.values()) or 1
    current = {key: value / total for key, value in current.items()}
    trajectories = {key: [] for key in current}
    for step in range(1, horizon + 1):
        weighted: dict[str, float] = {}
        for clone in clones:
            clone_id = str(clone["clone_id"])
            label = clone["clone_label"].lower()
            evidence = _number((clone.get("evidence") or {}).get("confidence", .5))
            fitness = _number(clone["fitness"])
            risk = _number(clone["risk_score"])
            modifier = 1 + pressure * ((fitness - .55) * .22 + risk * .035)
            if scenario == "resistance_sweep" and ("met" in label or risk >= .85): modifier += .15
            if scenario == "stable_coexistence": modifier = 1 + (modifier - 1) * .28
            if scenario == "plasticity_escape" and ("emt" in label or "bypass" in label): modifier += .18
            if scenario == "evidence_pruning": modifier *= .55 + .45 * evidence
            weighted[clone_id] = max(.001, current[clone_id] * modifier)
        denominator = sum(weighted.values()) or 1
        current = {key: value / denominator for key, value in weighted.items()}
        for clone_id, value in current.items():
            trajectories[clone_id].append({"generation": graph["timeline"]["latest_generation"] + step, "prevalence": round(value, 4), "uncertainty": round(min(.42, .055 + step * .038 + (0 if scenario == "stable_coexistence" else .025)), 4)})
    labels = {str(item["clone_id"]): item["clone_label"] for item in clones}
    return [{"clone_id": clone_id, "clone_label": labels[clone_id], "trajectory": values} for clone_id, values in trajectories.items()]


def run_evolution_memory_paths(synthetic_code: str, horizon: int = 4, pressure_mode: str = "balanced") -> dict[str, Any] | None:
    """Create, vote on and persist competing paths from recalled evolution memory."""
    graph = evolution_graph(synthetic_code)
    if graph is None:
        return None
    replay = evolution_memory_replay(synthetic_code)
    frames = replay["frames"] if replay else []
    if not frames:
        return {"ok": False, "reason": "NO_MEMORY_FRAMES", "paths": []}
    latest = frames[-1]
    memories = graph["persistent_memories"]
    trend = replay["latest_deltas"] if replay else []
    scenarios = [
        ("resistance_sweep", "Resistant clone sweep", "High-fitness resistant clones displace competing populations."),
        ("stable_coexistence", "Stable clonal coexistence", "Several lineages persist without one immediately dominating."),
        ("plasticity_escape", "Cell-state plasticity escape", "Phenotypic state changes outpace mutation-only explanations."),
        ("evidence_pruning", "Evidence-pruned branch", "Weak branches collapse when confidence is applied as a penalty."),
    ]
    raw_scores = []
    for key, _, _ in scenarios:
        score = {"resistance_sweep": .34, "stable_coexistence": .27, "plasticity_escape": .24, "evidence_pruning": .15}[key]
        if pressure_mode == "high" and key == "resistance_sweep": score += .12
        if pressure_mode == "low" and key == "stable_coexistence": score += .10
        if any("MET" in item.get("title", "") for item in memories) and key == "resistance_sweep": score += .08
        if any(item["signal"] == "expanding" and ("EMT" in item["clone_label"] or "bypass" in item["clone_label"].lower()) for item in trend) and key == "plasticity_escape": score += .07
        raw_scores.append(score)
    score_total = sum(raw_scores)
    probabilities = [score / score_total for score in raw_scores]
    base_votes = {
        "Genomic Cartographer": "resistance_sweep",
        "Clonal Evolution Forecaster": "resistance_sweep" if pressure_mode != "low" else "stable_coexistence",
        "Evidence Challenger": "evidence_pruning",
        "Memory Sentinel": "resistance_sweep" if memories else "stable_coexistence",
        "Safety Governor": "evidence_pruning",
    }
    scope = {"tenant_id": str(graph["patient"]["tenant_id"]), "patient_id": str(graph["patient"]["patient_id"])}
    paths = []
    for (scenario, label, hypothesis), probability in zip(scenarios, probabilities):
        trajectories = _scenario_projection(graph, horizon, scenario, pressure_mode)
        votes = [{"agent": agent, "supports": vote == scenario, "preferred_path": vote, "reason": "Vote is grounded in recalled frames, clone evidence and the research safety policy."} for agent, vote in base_votes.items()]
        memory_refs = {"base_frame_receipt": latest["frame_receipt"], "graph_receipt": graph["graph_receipt"]["sha256"], "memory_ids": [str(item["memory_id"]) for item in memories], "observed_delta": trend[:4]}
        receipt_payload = {"scenario": scenario, "pressure_mode": pressure_mode, "horizon": horizon, "trajectories": trajectories, "memory_refs": memory_refs}
        path_receipt = _receipt(receipt_payload)
        path_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"oncotwin:path:{path_receipt}"))
        path = {"path_id": path_id, "scenario": scenario, "label": label, "hypothesis": hypothesis, "probability": round(probability, 4), "trajectories": trajectories, "agent_votes": votes, "supporting_votes": sum(item["supports"] for item in votes), "memory_refs": memory_refs, "path_receipt": path_receipt}
        paths.append(path)
        with get_engine().begin() as connection:
            connection.execute(text("INSERT INTO evolution_path_hypotheses (tenant_id,patient_id,path_id,base_frame_id,scenario,pressure_mode,horizon,probability,trajectories,agent_votes,memory_refs,path_receipt) VALUES (CAST(:tenant_id AS UUID),CAST(:patient_id AS UUID),CAST(:path_id AS UUID),CAST(:frame_id AS UUID),:scenario,:pressure_mode,:horizon,:probability,CAST(:trajectories AS JSONB),CAST(:votes AS JSONB),CAST(:memory_refs AS JSONB),:path_receipt) ON CONFLICT (tenant_id,patient_id,path_receipt) DO NOTHING"), {**scope, "path_id": path_id, "frame_id": str(latest["frame_id"]), "scenario": scenario, "pressure_mode": pressure_mode, "horizon": horizon, "probability": probability, "trajectories": json.dumps(trajectories), "votes": json.dumps(votes), "memory_refs": json.dumps(memory_refs), "path_receipt": path_receipt})
    paths.sort(key=lambda item: item["probability"], reverse=True)
    run_receipt = _receipt({"at": datetime.now(timezone.utc).date().isoformat(), "base_frame": latest["frame_receipt"], "paths": [item["path_receipt"] for item in paths]})
    return {"ok": True, "source": "cockroachdb-memory-conditioned-paths", "synthetic": True, "research_only": True, "clinical_action_allowed": False, "human_review_required": True, "pressure_mode": pressure_mode, "horizon": horizon, "base_frame": latest, "memory_utility": replay["memory_utility"], "paths": paths, "recommended_research_path": paths[0]["scenario"], "decision": "COMPARE_PATHS_WITH_HUMAN_REVIEW", "run_receipt": run_receipt}
