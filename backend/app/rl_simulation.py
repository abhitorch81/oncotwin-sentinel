"""Research-only decision engine for OncoTwin V11.

Actions govern data, evidence and ML workflows. They never recommend treatment.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from random import Random
from typing import Any
from .condition_registry import condition

@dataclass
class TwinState:
    data_trust: int
    model_risk: float
    malignant_fraction: float
    null_rate: float = 0.0
    drift_score: float = 0.0
    schema_compatible: bool = True
    model_blocked: bool = False
    repaired: bool = False
    def public(self) -> dict[str, Any]: return asdict(self)

def _case(title: str, cohort: str, failure: str, safe: str, repair: str, initial: TwinState,
          topic: str, question: str, memory: str, arc: list[str], council: list[list[str]]) -> dict[str, Any]:
    return {"title": title, "cohort": cohort, "challenge": "Agents That Do Real Work", "failure": failure,
            "datahub": ["search", "get_entities", "list_schema_fields", "get_lineage", "get_dataset_queries"],
            "actions": ["continue", "monitor", safe, repair, "request_review"], "initial": initial,
            "safe_action": safe, "repair_action": repair, "state_arc": arc, "topic": topic,
            "decision_question": question, "memory_query": memory, "agent_council": council,
            "evidence_freshness_hours": 6, "research_only": True}

MISSION_CASES: dict[str, dict[str, Any]] = {
 "feature_quality": _case("Trial Data Integrity Crisis","LUAD","Missing biomarker features compromise a trial-derived research model","block_model","repair_features",TwinState(61,.86,.43,null_rate=.18),"Responsible trial AI","Can this evidence safely enter the research model?","missing biomarker evidence and model safety",["complete","integrity breach","audited recovery"],[["Data Sentinel","BLOCK"],["ML Guardian","BLOCK"],["Evidence Steward","ESCALATE"]]),
 "cancer_progression": _case("MET Resistance Evolution","LUAD","A MET-positive resistant population expands during EGFR-targeted therapy","flag_research_review","reconcile_resistance_evidence",TwinState(82,.73,.43,drift_score=.61),"Targeted-therapy resistance","Is the resistance signal strong enough for a research escalation?","emerging MET mediated resistance",["EGFR-sensitive","MET-emergent","review-gated"],[["Bioinformatics Agent","ESCALATE"],["ML Guardian","MONITOR"],["Safety Steward","ESCALATE"]]),
 "model_drift": _case("Digital Pathology Domain Shift","KIRC","Scanner and staining distribution diverge from governed training context","block_model","revalidate_pathology_domain",TwinState(68,.91,.35,drift_score=.77),"Digital pathology assurance","Should inference continue under scanner domain shift?","pathology scanner drift and model reliability",["validated domain","silent shift","revalidation gate"],[["Drift Sentinel","BLOCK"],["Pathology Agent","MONITOR"],["ML Guardian","BLOCK"]]),
 "schema_mutation": _case("Genomic Schema Mutation","COAD","An upstream expression field becomes incompatible with feature SQL","block_consumers","generate_patch",TwinState(54,.88,.35,schema_compatible=False),"Genomic data contracts","Which consumers must stop before a schema-aware patch?","genomic schema contract failure",["compatible","breaking","patched"],[["Schema Sentinel","BLOCK"],["Lineage Agent","BLOCK"],["Repair Engineer","REPAIR"]]),
 "biomarker_discordance": _case("Multi-omic Discordance","PAAD","RNA, variant and protein evidence disagree on biomarker state","quarantine_biomarker","reconcile_evidence",TwinState(58,.84,.30,drift_score=.64),"Multi-omic evidence","Can a discordant biomarker support a research hypothesis?","multi omic biomarker discordance",["concordant","discordant","reconciled"],[["Omics Agent","BLOCK"],["Evidence Steward","ESCALATE"],["ML Guardian","BLOCK"]]),
 "protein_conformation": _case("ADC Payload Resistance","SKCM","Response evidence shifts without governed target and payload provenance","freeze_structure_score","verify_structure_provenance",TwinState(63,.87,.32,drift_score=.72),"Antibody-drug conjugates","Should the ADC resistance score remain visible?","ADC payload resistance and target evidence",["responsive","payload shift","provenance gate"],[["Molecular Agent","MONITOR"],["Evidence Steward","BLOCK"],["Safety Steward","BLOCK"]]),
 "microenvironment_escape": _case("Spatial Immune Escape","GBM","Spatial immune context shifts while the bulk score appears stable","flag_spatial_review","reconcile_spatial_context",TwinState(60,.82,.45,drift_score=.68),"Spatial immuno-oncology","Does the spatial signal overturn the bulk-model conclusion?","spatial immune escape microenvironment",["inflamed","immune-excluded","escape-risk"],[["Spatial Agent","ESCALATE"],["Bioinformatics Agent","ESCALATE"],["ML Guardian","BLOCK"]]),
 "ctdna_mrd_rebound": _case("ctDNA MRD Rebound","COAD","Longitudinal ctDNA rises after an apparent molecular response","hold_escalation","validate_mrd_signal",TwinState(67,.83,.28,drift_score=.66),"Liquid biopsy and MRD","Is the rebound robust across timepoints and assays?","ctDNA MRD rebound longitudinal variant",["undetectable","rebound","orthogonal validation"],[["Liquid Biopsy Agent","ESCALATE"],["Evidence Steward","MONITOR"],["Safety Steward","BLOCK"]]),
 "bispecific_safety": _case("Bispecific Safety Signal","LUAD","A cytokine pattern crosses the governed preclinical safety boundary","activate_safety_gate","reconcile_cytokine_signal",TwinState(64,.89,.31,drift_score=.71),"Bispecific immunotherapy safety","Must this research workflow pause for safety review?","bispecific cytokine safety signal",["baseline","signal detected","safety gate"],[["Safety Agent","BLOCK"],["Immunology Agent","ESCALATE"],["ML Guardian","BLOCK"]]),
 "cart_antigen_escape": _case("CAR-T Antigen Escape","LIHC","A rising clone loses the cataloged target-antigen signal","freeze_response_claim","validate_antigen_escape",TwinState(62,.85,.39,drift_score=.69),"Cell therapy escape","Is antigen loss real enough to invalidate the response claim?","CAR T antigen escape clone",["antigen-positive","mixed escape","claim frozen"],[["Cell Therapy Agent","ESCALATE"],["Omics Agent","MONITOR"],["Evidence Steward","BLOCK"]]),
 "neoantigen_vaccine_drift": _case("Neoantigen Vaccine Drift","SKCM","Dominant clones drift away from the governed neoantigen target set","hold_vaccine_hypothesis","refresh_neoantigen_targets",TwinState(66,.81,.36,drift_score=.74),"Personalized cancer vaccines","Does clonal drift invalidate the target hypothesis?","neoantigen vaccine clonal drift",["targeted","clonal drift","target refresh"],[["Vaccine Agent","ESCALATE"],["Genomics Agent","MONITOR"],["Safety Steward","BLOCK"]]),
 "radiopharmaceutical_mismatch": _case("Radiopharmaceutical Target Mismatch","KIRC","Imaging uptake and tissue target evidence diverge","block_theranostic_claim","reconcile_target_alignment",TwinState(59,.88,.34,drift_score=.76),"Radiopharmaceutical theranostics","Can the theranostic research claim survive target mismatch?","radiopharmaceutical target imaging tissue mismatch",["aligned","discordant","alignment review"],[["Imaging Agent","BLOCK"],["Molecular Agent","ESCALATE"],["Evidence Steward","BLOCK"]]),
}

class SafetyQLearner:
    def __init__(self, case_id: str, seed: int = 81):
        self.case_id=case_id; self.case=MISSION_CASES[case_id]; self.actions=self.case["actions"]
        self.rand=Random(seed+list(MISSION_CASES).index(case_id)); self.q: dict[tuple[tuple[int,int,int,int],str],float]={}
    @staticmethod
    def bucket(s: TwinState)->tuple[int,int,int,int]: return (int(s.data_trust<70),int(s.model_risk>=.75),int(s.null_rate>=.10 or s.drift_score>=.60),int(not s.schema_compatible))
    def reward(self,state: TwinState,action: str)->float:
        unsafe=state.model_risk>=.75 or state.null_rate>=.10 or state.drift_score>=.60 or not state.schema_compatible or state.malignant_fraction>=.35
        if action==self.case["safe_action"]: return 12.0 if unsafe else 3.0
        if action==self.case["repair_action"]: return 8.0 if unsafe else 2.0
        if action=="request_review": return 5.0
        if action=="monitor": return 2.0 if not unsafe else -4.0
        if action=="continue": return -15.0 if unsafe else 4.0
        return 1.0
    def train(self,episodes: int=700)->None:
        state=self.case["initial"]; key=self.bucket(state)
        for episode in range(episodes):
            epsilon=max(.03,.34*(1-episode/episodes)); action=self.rand.choice(self.actions) if self.rand.random()<epsilon else max(self.actions,key=lambda a:self.q.get((key,a),0.0))
            old=self.q.get((key,action),0.0); self.q[(key,action)]=old+.18*(self.reward(state,action)-old)
    def decide(self,state: TwinState)->dict[str,Any]:
        self.train(); key=self.bucket(state); ranked=sorted(((a,round(self.q.get((key,a),0.0),3)) for a in self.actions),key=lambda x:x[1],reverse=True)
        counterfactuals=[{"action":a,"q_value":q,"reward":self.reward(state,a),"outcome":("contains risk" if a==self.case["safe_action"] else "repairs evidence" if a==self.case["repair_action"] else "leaves residual risk"),"recommended":i==0} for i,(a,q) in enumerate(ranked)]
        return {"algorithm":"tabular-q-learning","episodes":700,"state_bucket":key,"action":ranked[0][0],"q_value":ranked[0][1],"reward":self.reward(state,ranked[0][0]),"ranked_actions":ranked,"decision_margin":round(ranked[0][1]-ranked[1][1],3),"counterfactuals":counterfactuals,"agent_council":[{"agent":a,"vote":v} for a,v in self.case["agent_council"]],"decision_question":self.case["decision_question"],"decisive_reason":"Highest safety-adjusted value under the observed evidence state.","research_only":True}

def simulate_transition(case_id: str,state: TwinState,action: str)->TwinState:
    nxt=TwinState(**state.public()); case=MISSION_CASES[case_id]
    if action==case["safe_action"]:
        nxt.model_blocked=True; nxt.model_risk=max(.25,nxt.model_risk-.28); nxt.data_trust=min(100,nxt.data_trust+7)
    elif action==case["repair_action"]:
        nxt.repaired=True; nxt.null_rate=0; nxt.drift_score=min(nxt.drift_score,.18); nxt.schema_compatible=True; nxt.model_risk=max(.18,nxt.model_risk-.48); nxt.data_trust=min(100,nxt.data_trust+24)
    return nxt

def mission_catalog()->list[dict[str,Any]]:
    result=[]
    for case_id,case in MISSION_CASES.items():
        spec=condition(case_id)
        result.append({"case_id":case_id,"title":case["title"],"default_cohort":case["cohort"],"challenge":case["challenge"],"failure":case["failure"],"datahub_tools":["search","get_entities","list_schema_fields","get_lineage_upstream","get_lineage_downstream","get_dataset_queries"],"asset_name":spec["asset_name"],"asset_owner":spec["owner"],"data_contract":spec["contract"],"proof_endpoint":f"/api/datahub/proof?case_id={case_id}","writeback":"human-gated-condition-incident","datahub_native":True,"state_arc":case["state_arc"],"topic":case["topic"],"decision_question":case["decision_question"],"memory_query":case["memory_query"],"agent_council":[{"agent":a,"vote":v} for a,v in case["agent_council"]],"evidence_freshness_hours":case["evidence_freshness_hours"],"research_only":True})
    return result
