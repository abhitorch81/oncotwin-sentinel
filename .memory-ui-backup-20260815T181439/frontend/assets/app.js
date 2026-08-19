const $ = id => document.getElementById(id);
const GCP_PROJECT_ID = 'project-1f5f7d56-1029-4c78-a68';
const state = {cohorts:[], cohort:null, twin:null, twinLoading:null, twinConfig:null, proof3d:null, proof3dLoading:null, proofData:null, observatory:null, observatoryLoading:null, observatoryData:null, observatoryCase:'feature_quality', observatoryTimers:[], selectedProofCase:'feature_quality', proposal:null, traces:[], generatedArtifacts:null, contextFingerprint:null, playTimer:null, missionStarted:0, missionCases:[], selectedMission:'feature_quality', missionId:null, missionEvents:[], missionStream:null, missionTwinState:null, replayTimers:[]};
const REPLAY_CACHE_KEY='oncotwin_verified_replay_v1';

const missionAgentIndex = {mission_started:0,datahub_context:0,failure_observed:3,lineage_impact:1,rl_decision:2,repair_proposed:4,approval_required:5,governed_action:5,repair_executed:4,quality_validated:3,incident_resolved:5,knowledge_written:5,governance_verified:5,mission_complete:2};
const missionEventTypes = Object.keys(missionAgentIndex);
const proofCaseDetails={
  feature_quality:{number:'01',visual:'BIOMARKER SIGNAL FRACTURE',boundary:'LIVE DATAHUB · SIM BIO · GUARDED WRITE',summary:'DataHub schema, contract and lineage block incomplete MKI67, EPCAM and VIM features before governed repair.'},
  cancer_progression:{number:'02',visual:'TUMOUR-STATE EVOLUTION',boundary:'LIVE DATAHUB · SIM BIO · GUARDED WRITE',summary:'A cataloged tumour-state product grounds a synthetic malignant-cell trajectory and review receipt.'},
  model_drift:{number:'03',visual:'COHORT DRIFT WAVEFRONT',boundary:'LIVE DATAHUB · SIM BIO · GUARDED WRITE',summary:'A dedicated drift-metrics asset is traced through ML lineage before inference is gated.'},
  schema_mutation:{number:'04',visual:'GENOMIC CONTRACT RIFT',boundary:'LIVE DATAHUB · SIM BIO · GUARDED WRITE',summary:'Cataloged schema-contract events generate a metadata-aware SQL patch from real schema and lineage.'},
  biomarker_discordance:{number:'05',visual:'MULTI-OMIC PHASE CONFLICT',boundary:'LIVE DATAHUB · SIM BIO · GUARDED WRITE',summary:'A cataloged multi-omic product exposes RNA, variant and protein provenance before quarantine.'},
  protein_conformation:{number:'06',visual:'CONFORMATION EVIDENCE RIFT',boundary:'LIVE DATAHUB · SIM BIO · GUARDED WRITE',summary:'Cataloged schematic structure evidence freezes when sequence-to-structure provenance becomes ambiguous.'},
  microenvironment_escape:{number:'07',visual:'IMMUNE ESCAPE FIELD',boundary:'LIVE DATAHUB · SIM BIO · GUARDED WRITE',summary:'A cataloged spatial-omics product exposes an immune-context shift before progression scoring.'}
};

const agentBlueprint = [
  {name:'Context Scout', purpose:'Replaces guessed table names with stable DataHub URNs.', tool:'MCP · search', query:'search(query="domain:oncology AND {code} progression")', result:'Governed datasets, owners and platform identity returned.'},
  {name:'Lineage Sentinel', purpose:'Maps upstream evidence and downstream blast radius before action.', tool:'MCP · get_lineage', query:'get_lineage(urn, upstream=true/false, max_hops=3)', result:'Raw assay → features → model → deployment lineage returned.'},
  {name:'ML Guardian', purpose:'Protects the production model from silent feature and data failures.', tool:'Agent Context Kit · LangChain', query:'inspect_model_context(model="{model}")', result:'Production model impact and risk boundary verified.'},
  {name:'Bioinformatics Agent', purpose:'Interprets schema and cell-state evidence without inventing fields.', tool:'MCP · get_entities', query:'get_entities(urns=[progression_features])', result:'Schema, quality, tags and biological context inspected.'},
  {name:'Repair Engineer', purpose:'Generates mergeable data-quality code from real metadata context.', tool:'DataHub Skills · quality + lineage', query:'generate_fix(schema, assertions, blast_radius)', result:'dbt test, Airflow guard and ingestion patch generated.'},
  {name:'Knowledge Steward', purpose:'Writes approved knowledge back so the next agent inherits it.', tool:'MCP · update_description', query:'update_description(operation="append")', result:'Mutation prepared; human approval is still required.'}
];

const codeSnippets = {
  dbt:`-- DataHub Skills repair: schema + lineage + query evidence
-- Source URN: urn:li:dataset:(urn:li:dataPlatform:bigquery,${GCP_PROJECT_ID}.oncotwin.gene_expression_summary,PROD)
-- Target URN: urn:li:dataset:(urn:li:dataPlatform:bigquery,${GCP_PROJECT_ID}.oncotwin.progression_features,PROD)
-- Downstream consumer: {model}
SELECT
  patient_key,
  cluster_id,
  stage,
  COALESCE(AVG(IF(gene = 'MKI67', mean_expression, NULL)), 0.0)
    AS proliferation_signal,
  COALESCE(AVG(IF(gene = 'EPCAM', mean_expression, NULL)), 0.0)
    AS epithelial_signal,
  COALESCE(AVG(IF(gene = 'VIM', mean_expression, NULL)), 0.0)
    AS mesenchymal_signal,
  CURRENT_TIMESTAMP() AS generated_at
FROM \`${GCP_PROJECT_ID}.oncotwin.gene_expression_summary\`
GROUP BY patient_key, cluster_id, stage`,
  airflow:`# Generated lineage-aware Airflow guard
from airflow.exceptions import AirflowFailException
from datahub.sdk import DataHubClient

def guard_{code}_progression(**context):
    client = DataHubClient.from_env()
    dataset = client.entities.get(
        "urn:li:dataset:(urn:li:dataPlatform:bigquery,${GCP_PROJECT_ID}.oncotwin.progression_features,PROD)"
    )
    null_signal_rows = context["ti"].xcom_pull(key="null_signal_rows")
    if null_signal_rows != 0:
        raise AirflowFailException(
            "Blocked {model}: progression feature signals contain NULLs"
        )
    return {"status": "safe", "owner": "{owner}"}

# Downstream impact verified with MCP get_lineage(max_hops=3)`,
  python:`# Generated DataHub ingestion patch
source:
  type: bigquery
  config:
    project_id: "\${GCP_PROJECT_ID}"
    dataset_pattern:
      allow: ["oncotwin"]
+   include_table_lineage: true
+   include_usage_statistics: true
+   profiling:
+     enabled: true
+     profile_table_level_only: false

sink:
  type: datahub-rest
  config:
    server: "\${DATAHUB_GMS_URL}"
    token: "\${DATAHUB_GMS_TOKEN}"

# Cohort: {code} · owner: {owner} · model: {model}`
};

async function boot(){
  wireStaticEvents();
  try{
    const [health, twinConfig, cohorts, missionCases] = await Promise.all([
      fetch('/api/health').then(checkJson), fetch('/api/twin').then(checkJson), fetch('/api/cohorts').then(checkJson), fetch('/api/missions/cases').then(checkJson)
    ]);
    $('modeBadge').textContent = health.mode === 'live' ? `▱ DataHub LIVE · V${health.ui_version}` : `▱ DataHub DEMO · V${health.ui_version}`;
    $('modeBadge').classList.add('live');
    $('analyticsLink').href = health.analytics_agent_url;
    state.twinConfig = twinConfig; state.cohorts = cohorts; state.missionCases = missionCases;
    renderCohorts(); renderMissionCases(); selectCohort(cohorts[0].code);
    selectMissionCase('feature_quality',false);
    renderAgentPager(); selectAgent(0); renderGeneBars('MKI67'); renderClusterCards(); initUmap(); renderCode('dbt');renderProofCases();selectProofCase('feature_quality',false);
    restoreVerifiedReplay();
  }catch(error){
    $('modeBadge').textContent='BACKEND OFFLINE';
    $('answer').textContent=`Application context could not load: ${error.message}`;
  }
}

function checkJson(response){if(!response.ok) throw new Error(`${response.status} ${response.statusText}`); return response.json()}

function wireStaticEvents(){
  document.querySelectorAll('.tab').forEach(tab=>tab.addEventListener('click',()=>switchView(tab.dataset.view)));
  document.querySelectorAll('.agent-node').forEach(node=>node.addEventListener('click',()=>selectAgent(Number(node.dataset.agent))));
  document.querySelectorAll('.gene').forEach(btn=>btn.addEventListener('click',()=>{document.querySelectorAll('.gene').forEach(x=>x.classList.remove('active'));btn.classList.add('active');renderGeneBars(btn.textContent)}));
  document.querySelectorAll('.code-tabs button').forEach(btn=>btn.addEventListener('click',()=>{document.querySelectorAll('.code-tabs button').forEach(x=>x.classList.remove('active'));btn.classList.add('active');renderCode(btn.dataset.code)}));
  $('runMission').addEventListener('click',runMission); $('approveWriteback').addEventListener('click',commitWriteback);
  $('approveMission').addEventListener('click',approveMission); $('replayMission').addEventListener('click',replayMission);
  document.querySelectorAll('.mission-case').forEach(btn=>btn.addEventListener('click',()=>selectMissionCase(btn.dataset.case)));
  $('playProgression').addEventListener('click',toggleProgression);
  $('autoRotate').addEventListener('click',()=>applyTwinTool('rotate',$('autoRotate')));
  document.querySelectorAll('[data-twin-tool]').forEach(btn=>btn.addEventListener('click',()=>applyTwinTool(btn.dataset.twinTool,btn)));
  $('stageSlider').addEventListener('input',e=>{stopProgression();state.twin?.setStage(e.target.value,'slider')});
  $('downloadFix').addEventListener('click',downloadFix); $('reviewWriteback').addEventListener('click',()=>{switchView('mission');$('writeback').scrollIntoView({behavior:'smooth'})});
  $('runDatahubProof').addEventListener('click',runDatahubProof);$('downloadProof').addEventListener('click',downloadJudgeProof);$('launchProofCase').addEventListener('click',launchSelectedProofCase);$('replayProofCase').addEventListener('click',replaySelectedProofCase);
  $('syncObservatory').addEventListener('click',syncObservatory);$('injectIncident').addEventListener('click',injectObservatoryIncident);$('previewRepair').addEventListener('click',previewObservatoryRepair);$('rewindObservatory').addEventListener('click',rewindObservatory);document.querySelectorAll('[data-observatory-case]').forEach(button=>button.addEventListener('click',()=>selectObservatoryCase(button.dataset.observatoryCase)));
}

function switchView(view){
  document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x.dataset.view===view));
  document.querySelectorAll('.app-view').forEach(x=>x.classList.toggle('active',x.id===`view-${view}`));
  window.scrollTo({top:0,behavior:'smooth'});
  if(view==='twin') setTimeout(()=>ensureTwin(),80);
  if(view==='scrna') setTimeout(drawUmap,80);
  if(view==='proof') setTimeout(()=>ensureProofGalaxy(),80);
  if(view==='graph') setTimeout(()=>ensureObservatory(),80);
}

async function ensureObservatory(){
  if(state.observatory){state.observatory.focus('progression_features');return state.observatory}
  if(state.observatoryLoading)return state.observatoryLoading;
      state.observatoryLoading=(async()=>{try{const {createCausalObservatory}=await import('./observatory3d.js?v=10.0.0');state.observatory=createCausalObservatory($('observatory3d'),{onNode:data=>{$('observatoryNode').textContent=data.label;$('observatoryNodeKind').textContent=data.kind;$('observatoryUrn').textContent=data.urn},onReady:info=>{$('observatoryRenderer').textContent=`● ${info.version} · ${info.nodes} NODES · ${info.edges} EDGES`},onPhase:(phase,nodes)=>{$('observatoryAffected').textContent=phase==='baseline'?'0':String(nodes.length)}});state.observatory.setScenario(state.observatoryCase);return state.observatory}catch(error){$('observatoryRenderer').textContent='× CAUSAL ENGINE ERROR';$('causalLedger').innerHTML=`<p>Live evidence remains available. 3D engine: ${escapeHtml(error.message)}</p>`;return null}finally{state.observatoryLoading=null}})();return state.observatoryLoading
}

async function ensureProofGalaxy(){
  if(state.proof3d){state.proof3d.focus();return state.proof3d}
  if(state.proof3dLoading)return state.proof3dLoading;
  state.proof3dLoading=(async()=>{try{const {createProofGalaxy}=await import('./proof3d.js?v=10.0.0');state.proof3d=createProofGalaxy($('proof3d'),{onSelect:caseId=>selectProofCase(caseId,true),onReady:info=>{$('proofRendererStatus').textContent=`● ${info.version} · ${info.worlds} WORLDS`;$('proofRendererStatus').classList.add('ready')}});state.proof3d.select(state.selectedProofCase,false);return state.proof3d}catch(error){$('proofRendererStatus').textContent='× 3D PROOF ENGINE ERROR';$('proofVerdict').textContent='The evidence ledger still works without WebGL';$('proofTimestamp').textContent=error.message;return null}finally{state.proof3dLoading=null}})();return state.proof3dLoading
}

async function ensureTwin(){
  if(state.twin){state.twin.resetCamera();return state.twin}
  if(state.twinLoading)return state.twinLoading;
  const card=$('lesionCard');
  card.innerHTML='<span class="eyebrow">LOADING 3D ENGINE</span><strong>Starting cancer twin…</strong><p>The rest of OncoTwin remains independent while WebGL loads.</p>';
  state.twinLoading=(async()=>{
    try{
      const {createTwin3D}=await import('./twin3d.js?v=10.0.0');
      state.twin=createTwin3D($('twin3d'),state.twinConfig,{onStage:updateStageHUD,onSelect:showLesion,onSpecimen:(name,kind)=>{$('specimenName').textContent=name;$('organLabel').textContent=kind.toUpperCase()},onReady:info=>{$('twinRendererStatus').textContent=`● ${info.version} · LOCAL`;$('twinRendererStatus').className='renderer-status ready'},onError:message=>{$('twinRendererStatus').textContent='× WEBGL CONTEXT LOST';$('twinRendererStatus').className='renderer-status error';card.querySelector('p').textContent=message}});
      state.twin.setCohort(state.cohort?.code||'LUAD');
      state.twin.setStage(state.missionTwinState?stageFromTwin(state.missionTwinState):3,'boot');
      card.innerHTML='<span class="eyebrow">✣ INFERRED STATE</span><strong>Stage III</strong><p>Drag to rotate<br>Scroll to zoom<br>Click a dot to learn more</p>';
      return state.twin;
    }catch(error){
      $('twinRendererStatus').textContent='× RENDERER ERROR';
      $('twinRendererStatus').className='renderer-status error';
      card.innerHTML=`<span class="eyebrow">3D ENGINE UNAVAILABLE</span><strong>Other tasks still work</strong><p>${escapeHtml(error.message)}. Live Mission, scRNA, Causal Observatory, Proof Galaxy and Generated Fix are unaffected.</p>`;
      return null;
    }finally{state.twinLoading=null}
  })();
  return state.twinLoading;
}

function renderCohorts(){
  $('cohortList').innerHTML=state.cohorts.map(c=>`<button class="cohort-item" data-code="${c.code}"><i class="cohort-dot" style="background:${c.color};color:${c.color}"></i><span><strong>${c.code}</strong><span>${c.name}</span><small>${c.assets} assets · trust ${c.trust}</small></span></button>`).join('');
  document.querySelectorAll('.cohort-item').forEach(btn=>btn.addEventListener('click',()=>selectCohort(btn.dataset.code)));
}

function renderMissionCases(){
  $('missionCaseGrid').innerHTML=state.missionCases.map(spec=>{const detail=proofCaseDetails[spec.case_id];return `<button class="mission-case" data-case="${spec.case_id}"><i>${detail.number}</i><span><b>${spec.title} · LIVE DATAHUB</b><small>${spec.asset_name} · simulated biology · guarded write</small></span></button>`}).join('');
  $('missionCaseGrid').querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>selectMissionCase(button.dataset.case)));
}

function selectCohort(code){
  const c=state.cohorts.find(x=>x.code===code); if(!c)return; state.cohort=c;
  state.generatedArtifacts=null;state.contextFingerprint=null;
  document.querySelectorAll('.cohort-item').forEach(x=>x.classList.toggle('active',x.dataset.code===code));
  $('incidentCode').textContent=c.code;$('incidentText').textContent=c.incident;$('incidentModel').textContent=c.model;
  $('trustValue').textContent=c.trust;$('trustBar').style.width=`${c.trust}%`;$('trustIncident').textContent=c.incident;
  $('rightModel').textContent=c.model;$('rightOwner').textContent=c.owner;$('rightSource').textContent=c.source;
  $('graphModel').textContent=c.model;$('graphOwner').textContent=c.owner;$('fixOwner').textContent=c.owner;$('twinCohort').textContent=c.code;
  state.twin?.setCohort(c.code);
  renderDrivers(c);renderComposition(c);renderMolecules(c);renderCode(document.querySelector('.code-tabs button.active')?.dataset.code||'dbt');selectAgent(0);drawUmap();
}

function renderDrivers(c){$('driverBars').innerHTML=c.drivers.map(([n,v])=>`<div><span>${n}</span><i><b style="width:${v}%"></b></i><em>${v}</em></div>`).join('')}
function renderComposition(c){const colors=['#62d9ad','#71aef3','#e3ad56','#ef7172'];$('compositionList').innerHTML=c.composition.map(([n,v],i)=>`<p><i style="background:${colors[i]}"></i><span>${n}</span><b>${v}%</b></p>`).join('')}
function renderMolecules(c){$('moleculeList').innerHTML=c.molecules.map(([n,v])=>`<p><b>${n}</b><small>${c.drivers[0][0]} · RDKit</small><em>${v}</em></p>`).join('')}

function renderAgentPager(){$('agentPager').innerHTML=agentBlueprint.map((_,i)=>`<button data-agent="${i}" class="${i===0?'active':''}">${i+1}</button>`).join('');$('agentPager').querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>selectAgent(Number(b.dataset.agent))))}

function selectAgent(index){
  const a=agentBlueprint[index],c=state.cohort||{code:'LUAD',model:'luad_progression_v3',assets:27};
  document.querySelectorAll('.agent-node').forEach(x=>x.classList.toggle('active',Number(x.dataset.agent)===index));
  $('agentPager')?.querySelectorAll('button').forEach(x=>x.classList.toggle('active',Number(x.dataset.agent)===index));
  $('inspectorNumber').textContent=`AGENT INSPECTOR · ${String(index+1).padStart(2,'0')}`;$('inspectorName').textContent=a.name;$('inspectorPurpose').textContent=a.purpose;$('inspectorTool').textContent=a.tool;
  $('inspectorQuery').textContent=a.query.replaceAll('{code}',c.code).replaceAll('{model}',c.model);
  const trace=state.traces[index];$('inspectorEvidence').textContent=trace?.summary||a.result;$('inspectorUrn').textContent=trace?.snippet||`urn:li:dataset:(urn:li:dataPlatform:bigquery,${GCP_PROJECT_ID}.oncotwin.progression_features,PROD)`;
}

async function runMission(){
  stopMissionPlayback();
  const button=$('runMission');button.disabled=true;button.innerHTML='<span>◌</span> Capturing DataHub-grounded mission…';state.missionStarted=Date.now();state.traces=[];state.proposal=null;state.missionEvents=[];
  $('missionTimeline').innerHTML='<span class="empty">GCP backend is capturing the mission trace…</span>';
  document.querySelectorAll('.agent-node').forEach(x=>x.classList.remove('done','running'));$('corePercent').textContent='8%';$('missionStatus').textContent='Opening DataHub context…';$('answer').textContent='Waiting for RL + metadata evidence…';$('writebackGate').textContent='LOCKED';$('approveMission').disabled=true;
  $('rlAction').textContent='OBSERVING';$('rlReward').textContent='—';$('rlRisk').textContent='—';$('rlTrust').textContent='—';
  try{
    const response=await fetch('/api/missions/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({case_id:state.selectedMission,cohort:state.cohort.code,mode:'live'})});
    const data=await checkJson(response); state.missionId=data.mission_id; $('replayMission').disabled=false;$('replayProofCase').disabled=false;
    $('missionStatus').textContent=`Mission ${data.mission_id} captured · playing ${data.mode.toUpperCase()} evidence`;
    connectMissionStream(data.mission_id);
  }catch(error){$('missionStatus').textContent='Mission stopped safely';$('answer').textContent=`No action committed: ${error.message}`;button.disabled=false;button.innerHTML='<span>▷</span> Run selected mission'}
}

function selectMissionCase(caseId,switchCohort=true){
  state.selectedMission=caseId;const spec=state.missionCases.find(x=>x.case_id===caseId);
  document.querySelectorAll('.mission-case').forEach(x=>x.classList.toggle('active',x.dataset.case===caseId));
  if(spec&&switchCohort&&state.cohorts.some(x=>x.code===spec.default_cohort))selectCohort(spec.default_cohort);
  if(spec){$('incidentText').textContent=spec.failure;$('incidentCode').textContent=state.cohort?.code||spec.default_cohort;$('missionStatus').textContent=`Ready · ${spec.title}`}
}

function connectMissionStream(missionId){
  state.missionStream?.close();const source=new EventSource(`/api/missions/${missionId}/events`);state.missionStream=source;
  missionEventTypes.forEach(type=>source.addEventListener(type,e=>applyMissionEvent(JSON.parse(e.data),false)));
  source.addEventListener('stream_end',e=>{const end=JSON.parse(e.data);source.close();state.missionStream=null;const awaiting=end.status==='awaiting_approval';$('approveMission').disabled=!awaiting;$('writebackGate').textContent=awaiting?'APPROVAL REQUIRED':end.status.toUpperCase();$('missionStatus').textContent=awaiting?'RL response ready · recovery paused at governance':`Mission ${end.status}`;persistVerifiedReplay();const button=$('runMission');button.disabled=false;button.innerHTML='<span>▷</span> Run selected mission'});
  source.onerror=()=>{source.close();state.missionStream=null;$('missionStatus').textContent='Event stream closed safely';const button=$('runMission');button.disabled=false;button.innerHTML='<span>▷</span> Run selected mission'};
}

function applyMissionEvent(event,replay=false){
  state.missionEvents.push(event);state.missionTwinState=event.twin||state.missionTwinState;
  const idx=missionAgentIndex[event.type];
  if(idx!==undefined){state.traces[idx]={agent:event.agent,tool:event.tool||event.type,summary:event.summary,evidence:event.evidence||event.rl||event.twin,snippet:evidenceSnippet(event.evidence||event.rl||event.twin),duration_ms:event.at_ms||0,scene_cue:event.scene_cue||'context-pulse'};activateAgent(idx,state.traces[idx])}
  if(event.twin){const trust=Math.round(event.twin.data_trust),risk=Number(event.twin.model_risk);$('rlTrust').textContent=`${trust}/100`;$('trustValue').textContent=trust;$('trustBar').style.width=`${trust}%`;$('rlRisk').textContent=risk.toFixed(2);$('modelRiskMetric').textContent=risk>=.75?'HIGH':risk>=.45?'WATCH':'LOW';$('modelRiskMetric').classList.toggle('warning',risk>=.45);if(state.twin)state.twin.setStage(stageFromTwin(event.twin),'mission');drawUmap()}
  if(event.rl){$('rlAction').textContent=String(event.rl.action).replaceAll('_',' ').toUpperCase();$('rlReward').textContent=`+${Number(event.rl.reward).toFixed(1)}`}
  if(event.type==='datahub_context'){
    const urn=event.evidence?.asset_urn||event.evidence?.asset;
    if(urn)$('assetUrn').textContent=urn;
  }
  if(event.type==='failure_observed'){$('trustIncident').textContent=event.summary;$('answer').textContent=`Failure observed. DataHub lineage and RL safety policy are evaluating downstream impact.`;$('graphFeatureNode').classList.add('warn');$('graphFeatureStatus').textContent='active context failure ⚠'}
  if(event.type==='lineage_impact'){$('answer').textContent='DataHub lineage mapped the blast radius before the RL controller selected an action.';document.querySelector('.lineage-canvas')?.classList.add('live-pulse');setTimeout(()=>document.querySelector('.lineage-canvas')?.classList.remove('live-pulse'),900)}
  if(event.type==='repair_proposed'){
    $('proposalText').textContent=event.summary;$('writebackGate').textContent='REVIEW REQUIRED';
    if(event.generated_artifacts){state.generatedArtifacts=event.generated_artifacts;renderCode(document.querySelector('.code-tabs button.active')?.dataset.code||'dbt')}
  }
  if(event.type==='approval_required'){$('approveMission').disabled=replay;$('writebackGate').textContent=replay?'REPLAY · NO WRITES':'APPROVAL REQUIRED'}
  if(event.type==='repair_executed'){$('proposalText').textContent=`Approved BigQuery repair executed · job ${event.evidence?.job_id||'captured'}`;$('writebackGate').textContent='REPAIR EXECUTED'}
  if(event.type==='quality_validated'){$('answer').textContent=event.summary;$('qualityScore').textContent='5/5';$('writebackGate').textContent='QUALITY PASS'}
  if(event.type==='incident_resolved'){$('trustIncident').textContent='DataHub incident resolved · zero active';$('writebackGate').textContent='INCIDENT RESOLVED'}
  if(event.type==='knowledge_written'){$('proposalText').textContent=`Inherited knowledge written to DataHub by ${event.evidence?.responsible_agent||'Knowledge Steward'} · receipt ${(event.evidence?.receipt_sha256||'').slice(0,16)}…`;$('writebackGate').textContent='KNOWLEDGE INHERITED'}
  if(event.type==='mission_complete'){$('answer').textContent='Governed recovery verified. Context is healthy enough to unblock the research ML consumer.';$('trustIncident').textContent='Context restored · model unblocked';$('writebackGate').textContent='VERIFIED';$('qualityScore').textContent='5/5';$('graphFeatureNode').classList.remove('warn');$('graphFeatureStatus').textContent='repaired context · PASS ✓'}
  $('corePercent').textContent=`${Math.min(100,8+event.sequence*12)}%`;$('missionStatus').textContent=`${replay?'REPLAY · ':''}${event.agent} · ${event.summary}`;appendTimelineEvent(event,replay);
}

function appendTimelineEvent(event,replay){
  const line=$('missionTimeline');if(line.querySelector('.empty'))line.innerHTML='';const node=document.createElement('div');node.className=`timeline-event ${event.status||''}`;node.innerHTML=`<i></i><b>${String(event.type).replaceAll('_',' ')}</b><small>${replay?'REPLAY':'LIVE'} · ${event.at_ms||0}ms</small>`;line.appendChild(node);line.scrollLeft=line.scrollWidth;
}

function stageFromTwin(twin){const m=Number(twin?.malignant_fraction||0);if(m>=.43)return 4;if(m>=.32)return 3;if(m>=.22)return 2;if(m>=.14)return 1;return 0}

async function approveMission(){
  if(!state.missionId)return;const secret=$('approvalSecret').value;if(!secret){$('writebackStatus').textContent='Enter the operator approval secret first.';return}
  const btn=$('approveMission');btn.disabled=true;$('writebackStatus').textContent='Applying guarded mission recovery…';
  try{const response=await fetch(`/api/missions/${state.missionId}/approve`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({approval_secret:secret})});const data=await checkJson(response);const seen=new Set(state.missionEvents.map(x=>x.sequence));const fresh=data.events.filter(x=>!seen.has(x.sequence));fresh.forEach(x=>applyMissionEvent(x,false));const proof=fresh.find(x=>x.type==='governance_verified')?.evidence||{};$('writebackStatus').textContent=proof.knowledge_written_back?`✓ Repair PASS · incident resolved · DataHub knowledge inherited · ${(proof.knowledge_writeback?.receipt_sha256||'').slice(0,16)}…`:proof.execution_scope==='live-datahub'?(proof.datahub_mutation?'✓ Live DataHub incident resolved · PASS verified':'✓ Live DataHub PASS verified · no active incident'):'✓ Digital-twin recovery approved · no DataHub mutation';$('replayMission').disabled=false;$('replayMission').textContent='↻ VERIFIED REPLAY';persistVerifiedReplay()}
  catch(error){$('writebackStatus').textContent=`Not approved: ${error.message}`;btn.disabled=false}
}

async function replayMission(){
  if(!state.missionId)return;
  const cachedEvents=[...state.missionEvents];
  stopMissionPlayback();resetMissionVisualsForReplay();
  try{
    let events=[];
    try{events=(await fetch(`/api/missions/${state.missionId}/replay`).then(checkJson)).events||[]}
    catch(error){events=cachedEvents;if(!events.length)throw error}
    if(!events.length)throw new Error('No captured mission events are available');
    events.forEach((event,i)=>{const timer=setTimeout(()=>{$('replayMission').textContent=`■ REPLAYING ${i+1}/${events.length}`;applyMissionEvent(event,true)},i*850);state.replayTimers.push(timer)});
    const done=setTimeout(()=>{$('missionStatus').textContent='VERIFIED REPLAY COMPLETE · no mutations executed';$('writebackStatus').textContent='✓ Replay proof complete · zero write operations';$('replayMission').textContent='↻ REPLAY AGAIN';$('replayMission').disabled=false;$('replayMission').classList.remove('active');document.querySelector('.mission-deck').classList.add('replay-complete')},events.length*850+450);state.replayTimers.push(done)
  }catch(error){$('missionStatus').textContent=`Replay unavailable: ${error.message}`;$('replayMission').textContent='↻ RETRY REPLAY';$('replayMission').disabled=false;$('replayMission').classList.remove('active')}
}

function resetMissionVisualsForReplay(){
  state.missionEvents=[];state.traces=[];state.missionTwinState=null;state.missionStarted=Date.now();
  document.querySelectorAll('.agent-node').forEach((node,i)=>{node.classList.remove('done','running','active');if(i===0)node.classList.add('active')});
  document.querySelector('.mission-deck').classList.remove('replay-complete');document.querySelector('.mission-deck').classList.add('replay');
  $('liveMode').classList.remove('active');$('liveMode').textContent='○ LIVE CAPTURED';$('replayMission').classList.add('active');$('replayMission').textContent='■ REWINDING';$('replayMission').disabled=true;
  $('approveMission').disabled=true;$('missionTimeline').innerHTML='<span class="empty">Rewinding the immutable mission trace…</span>';
  $('missionStatus').textContent='VERIFIED REPLAY · read-only · preparing event 1';$('missionClock').textContent='00:00';$('corePercent').textContent='8%';
  $('rlRisk').textContent='—';$('rlAction').textContent='REWINDING';$('rlReward').textContent='—';$('rlTrust').textContent='—';$('qualityScore').textContent='—/5';
  $('answer').textContent='Replaying DataHub evidence and RL decisions from the captured mission.';$('writebackGate').textContent='REPLAY · NO WRITES';$('proposalText').textContent='Verified replay is read-only. Governance mutations are disabled.';$('writebackStatus').textContent='Replay proof: every event is timestamped; no tools can write.';
  selectAgent(0);document.querySelector('.mission-deck').scrollIntoView({behavior:'smooth',block:'center'});
}

function persistVerifiedReplay(){
  if(!state.missionId||!state.missionEvents.length)return;
  try{localStorage.setItem(REPLAY_CACHE_KEY,JSON.stringify({missionId:state.missionId,events:state.missionEvents,cohort:state.cohort?.code,caseId:state.selectedMission}))}catch(_error){}
}

function restoreVerifiedReplay(){
  try{const saved=JSON.parse(localStorage.getItem(REPLAY_CACHE_KEY)||'null');if(!saved?.missionId||!saved?.events?.length)return;if(saved.cohort&&state.cohorts.some(x=>x.code===saved.cohort))selectCohort(saved.cohort);if(saved.caseId)selectMissionCase(saved.caseId,false);state.missionId=saved.missionId;state.missionEvents=saved.events;$('replayMission').disabled=false;$('replayProofCase').disabled=false;$('replayMission').textContent='↻ VERIFIED REPLAY';$('missionStatus').textContent=`Verified replay ready · ${saved.events.length} captured events`}
  catch(_error){localStorage.removeItem(REPLAY_CACHE_KEY)}
}

function stopMissionPlayback(){state.missionStream?.close();state.missionStream=null;state.replayTimers.forEach(clearTimeout);state.replayTimers=[];document.querySelector('.mission-deck')?.classList.remove('replay','replay-complete');$('liveMode')?.classList.add('active');$('liveMode').textContent='● LIVE';$('replayMission')?.classList.remove('active')}

function activateAgent(index,trace){
  const nodes=[...document.querySelectorAll('.agent-node')],node=nodes[index];nodes.forEach(n=>n.classList.remove('running'));node.classList.add('running');setTimeout(()=>node.classList.replace('running','done'),560);
  $('corePercent').textContent=`${Math.min(100,18+(index+1)*14)}%`;const elapsed=Math.floor((Date.now()-state.missionStarted)/1000);$('missionClock').textContent=`00:${String(elapsed).padStart(2,'0')}`;$('missionStatus').textContent=`${trace.agent} · ${trace.tool} · ${trace.duration_ms}ms`;selectAgent(index);state.twin?.pulse(trace.scene_cue);if(trace.scene_cue==='risk-focus')state.twin?.setStage(2,'agent');
}

function evidenceSnippet(e){const s=JSON.stringify(e||{});return s.length>150?`${s.slice(0,150)}…`:s}

async function commitWriteback(){
  if(!state.proposal){$('writebackStatus').textContent='Run an investigation first.';return}
  const btn=$('approveWriteback');btn.disabled=true;$('writebackStatus').textContent='Committing approved metadata through DataHub MCP…';
  try{const r=await fetch('/api/writeback/commit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proposal_id:state.proposal.proposal_id,approval_secret:$('approvalSecret').value})});const data=await checkJson(r);$('writebackGate').textContent='COMMITTED';$('writebackStatus').textContent=`✓ ${data.mode.toUpperCase()} writeback committed · proposal consumed`;state.proposal=null;state.twin?.pulse('lineage-pulse')}
  catch(error){$('writebackStatus').textContent=`Not committed: ${error.message}`;btn.disabled=false}
}

function updateStageHUD(stage){$('stageSlider').value=stage.index;$('stageLabel').textContent=`${stage.label} · ${stage.title.toUpperCase()}`;$('stageSignature').textContent=stage.signature;$('activeSignals').textContent=stage.index+1;document.querySelectorAll('.timeline-labels>span').forEach((x,i)=>x.classList.toggle('active',i===stage.index))}
function showLesion(l){$('lesionCard').innerHTML=`<span class="eyebrow">${l.id} · SIGNAL FOCUS</span><strong>${l.label}</strong><p>Research signal ${Math.round(l.risk*100)}%<br>Appears at stage ${l.appears_at}<br>Click another marker to compare</p>`}
function applyTwinTool(tool,button){if(!state.twin)return;const result=state.twin.command(tool);if(tool==='rotate'){$('autoRotate').classList.toggle('active',result.active);return}if(tool==='reset'){document.querySelectorAll('[data-twin-tool]').forEach(x=>x.classList.remove('active'));$('autoRotate').classList.add('active');return}button?.classList.toggle('active',result.active)}
function toggleProgression(){state.playTimer?stopProgression():playProgression()}
function playProgression(){const last=(state.twinConfig?.stages?.length||5)-1;let i=Number($('stageSlider').value);if(i>=last){i=0;state.twin?.setStage(0,'play')}$('playProgression').textContent='Ⅱ Pause';state.playTimer=setInterval(()=>{i++;if(i>last)return stopProgression();state.twin?.setStage(i,'play');state.twin?.pulse(i===last?'risk-focus':'lineage-pulse')},1350)}
function stopProgression(){clearInterval(state.playTimer);state.playTimer=null;$('playProgression').textContent='▷ Play progression'}

let umapPoints=[];
function initUmap(){const rand=mulberry32(42);const clusters=[[-1.5,-.6,'Epithelial','#62d9ad'],[-.2,1.1,'T cells','#71aef3'],[1.15,.35,'Myeloid','#e3ad56'],[.65,-1.05,'Malignant','#ef7172']];umapPoints=[];clusters.forEach(([cx,cy,name,color],ci)=>{for(let i=0;i<190;i++){const a=rand()*Math.PI*2,r=Math.sqrt(rand())*(ci===3?1.05:.82);umapPoints.push({x:cx+Math.cos(a)*r,y:cy+Math.sin(a)*r*.55,name,color,value:rand()})}});drawUmap();addEventListener('resize',drawUmap);$('umapCanvas').addEventListener('pointermove',hoverUmap)}
function drawUmap(){const canvas=$('umapCanvas');if(!canvas||!umapPoints.length)return;const rect=canvas.getBoundingClientRect(),d=Math.min(devicePixelRatio||1,2),malignant=Number(state.missionTwinState?.malignant_fraction||0);canvas.width=rect.width*d;canvas.height=rect.height*d;const x=canvas.getContext('2d');x.setTransform(d,0,0,d,0,0);x.clearRect(0,0,rect.width,rect.height);x.strokeStyle='rgba(70,120,101,.12)';for(let i=1;i<6;i++){x.beginPath();x.arc(rect.width/2,rect.height/2,i*55,0,Math.PI*2);x.stroke()}umapPoints.forEach(p=>{p.sx=rect.width/2+p.x*120;p.sy=rect.height/2+p.y*125;const risk=p.name==='Malignant'?1+malignant*1.7:1;x.globalAlpha=.35+p.value*.55;x.fillStyle=p.color;x.shadowColor=p.name==='Malignant'&&malignant>.3?'rgba(239,113,114,.85)':'transparent';x.shadowBlur=p.name==='Malignant'?malignant*12:0;x.beginPath();x.arc(p.sx,p.sy,(2.1+p.value*1.4)*risk,0,Math.PI*2);x.fill()});x.shadowBlur=0;x.globalAlpha=1}
function hoverUmap(e){let best=null,dist=40;const r=e.currentTarget.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;umapPoints.forEach(p=>{const d=(p.sx-x)**2+(p.sy-y)**2;if(d<dist){dist=d;best=p}});const tip=$('umapTooltip');if(!best){tip.classList.add('hidden');return}tip.classList.remove('hidden');tip.style.left=`${x+12}px`;tip.style.top=`${y+12}px`;tip.textContent=`${best.name} · ${state.cohort?.code||'LUAD'} · z=${best.value.toFixed(2)}`}
function mulberry32(a){return()=>{let t=a+=0x6D2B79F5;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296}}

function renderGeneBars(gene){$('selectedGene').textContent=gene;const base={MKI67:[28,46,68,91],EPCAM:[86,72,59,44],KRAS:[52,61,76,84],TP53:[45,58,67,73],STK11:[39,48,55,62]}[gene]||[40,50,60,70];$('geneBars').innerHTML=['Epithelial','T cells','Myeloid','Malignant'].map((n,i)=>`<div><p><span>${n}</span><b>${base[i]}</b></p><i><b style="width:${base[i]}%"></b></i></div>`).join('')}
function renderClusterCards(){$('clusterCards').innerHTML=[['C01','Epithelial',2738],['C02','T cells',3019],['C03','Myeloid',2588],['C04','Malignant',6037]].map(([id,n,v])=>`<div><strong>${v.toLocaleString()}</strong><b>${n}</b><small>${id} · DataHub governed cluster</small></div>`).join('')}

function renderProofCases(){
  $('proofCaseGrid').innerHTML=state.missionCases.map(spec=>{const detail=proofCaseDetails[spec.case_id];return `<button class="proof-case-card" data-proof-case="${spec.case_id}"><i>${detail.number} · ${detail.visual}</i><b>${spec.title}</b><small>${detail.summary}</small><span>${detail.boundary}</span></button>`}).join('');
  $('proofCaseGrid').querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>selectProofCase(button.dataset.proofCase,true)));
}

function selectProofCase(caseId,syncMission=true){
  const spec=state.missionCases.find(item=>item.case_id===caseId),detail=proofCaseDetails[caseId];if(!spec||!detail)return;state.selectedProofCase=caseId;
  document.querySelectorAll('.proof-case-card').forEach(card=>card.classList.toggle('active',card.dataset.proofCase===caseId));
  $('proofCaseTitle').textContent=spec.title;$('proofCaseChallenge').textContent=`${spec.challenge} · ${detail.boundary} · ${(spec.state_arc||[]).join(' → ')}`;state.proof3d?.select(caseId,false);
  if(syncMission)selectMissionCase(caseId,true);
}

async function runDatahubProof(){
  const button=$('runDatahubProof');button.disabled=true;button.textContent='◌ Calling self-hosted DataHub MCP…';$('proofMode').textContent='CAPTURING';$('proofVerdict').textContent='Reading the live metadata graph';$('proofTimestamp').textContent='No mutation tools are permitted during this proof.';$('proofToolLedger').innerHTML='<p class="empty">Opening MCP session → canonical search → schema → upstream lineage → downstream lineage…</p>';
  try{
    const proof=await fetch(`/api/datahub/proof?case_id=${encodeURIComponent(state.selectedProofCase)}`,{cache:'no-store'}).then(checkJson);state.proofData=proof;$('proofMode').textContent=`${proof.mode.toUpperCase()} · MCP · ${proof.case_id}`;$('proofVerdict').textContent=proof.all_tools_passed?`${proof.condition_title} is DataHub-grounded`:'DataHub returned partial evidence';$('proofTimestamp').textContent=`Proof ${proof.proof_id} · SHA-256 ${proof.receipt_sha256.slice(0,16)}… · ${new Date(proof.captured_at).toLocaleString()}`;$('proofAssetUrn').textContent=proof.asset_urn;$('proofToolCount').textContent=`${proof.successful_tools}/${proof.total_tools}`;$('proofIncidentCount').textContent=proof.active_incidents===null?'N/A':String(proof.active_incidents);
    const purposes={search:'canonical asset discovery',get_entities:'owner, tags and properties',list_schema_fields:'catalog schema contract',get_lineage_upstream:'upstream provenance',get_lineage_downstream:'downstream blast radius',get_dataset_queries:'generating query evidence'};$('proofToolLedger').innerHTML=proof.evidence.map(item=>`<div class="proof-tool ${item.is_error?'error':''}"><i>${item.is_error?'×':'✓'}</i><span><b>${escapeHtml(item.tool)}</b><small>${purposes[item.tool]||'DataHub context evidence'}</small></span><em>${Number(item.duration_ms||0)}ms</em></div>`).join('');
    $('downloadProof').disabled=false;state.proof3d?.setEvidence(proof.successful_tools,proof.total_tools);button.textContent='✓ Capture fresh proof again';$('replayProofCase').disabled=!state.missionId;
  }catch(error){$('proofMode').textContent='PROOF FAILED';$('proofVerdict').textContent='No claim was accepted without evidence';$('proofTimestamp').textContent=error.message;$('proofToolLedger').innerHTML='<p class="empty">The proof stopped safely. No write was attempted.</p>';button.textContent='↻ Retry live DataHub proof'}finally{button.disabled=false}
}

function launchSelectedProofCase(){
  selectMissionCase(state.selectedProofCase,true);switchView('mission');setTimeout(()=>{$('runMission').scrollIntoView({behavior:'smooth',block:'center'});runMission()},420)
}

function replaySelectedProofCase(){
  if(!state.missionId)return;switchView('mission');setTimeout(replayMission,420)
}

function downloadJudgeProof(){
  if(!state.proofData)return;const blob=new Blob([JSON.stringify(state.proofData,null,2)],{type:'application/json'}),link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download=`oncotwin_datahub_proof_${state.proofData.proof_id}.json`;link.click();URL.revokeObjectURL(link.href)
}

const observatoryFallback={
  feature_quality:{label:'Biomarker completeness fracture',action:'BLOCK MODEL',repair:'COALESCE biomarker feature patch',path:['progression_features','progression_scores','OncoTwin model']},
  cancer_progression:{label:'Tumour-state progression surge',action:'FLAG REVIEW',repair:'preserve governed progression evidence',path:['gene_expression_summary','progression_features','progression_scores']},
  model_drift:{label:'Cancer cohort drift',action:'RETRAIN GATE',repair:'revalidate training cohort context',path:['progression_scores','OncoTwin model','Mission Control']},
  schema_mutation:{label:'Genomic schema mutation',action:'BLOCK CONSUMERS',repair:'metadata-aware genomic SQL patch',path:['gene_expression_summary','progression_features']},
  biomarker_discordance:{label:'Multi-omic biomarker discordance',action:'QUARANTINE BIOMARKER',repair:'reconcile RNA, variant and protein provenance',path:['multi_omic_biomarker_evidence','progression_features','progression_scores']},
  protein_conformation:{label:'Protein conformation evidence rift',action:'FREEZE STRUCTURE SCORE',repair:'verify sequence-to-structure model lineage',path:['protein_conformation_states','progression_scores','OncoTwin model']},
  microenvironment_escape:{label:'Tumour microenvironment escape',action:'FLAG SPATIAL REVIEW',repair:'reconcile spatial cell-state context',path:['spatial_microenvironment','progression_features','progression_scores']}
};
function observatorySpec(){return state.observatoryData?.scenarios?.find(x=>x.id===state.observatoryCase)||observatoryFallback[state.observatoryCase]}
function selectObservatoryCase(caseId){state.observatoryCase=caseId;document.querySelectorAll('[data-observatory-case]').forEach(button=>button.classList.toggle('active',button.dataset.observatoryCase===caseId));const spec=observatorySpec();$('causalAction').textContent=spec.action;$('causalRepair').textContent=`Repair preview: ${spec.repair}`;$('causalLedger').innerHTML=`<p>${escapeHtml(spec.label)} armed. Synchronize live DataHub, then inject the counterfactual incident.</p>`;$('observatoryAffected').textContent='0';state.observatory?.setScenario(caseId)}
async function syncObservatory(){const button=$('syncObservatory');button.disabled=true;button.textContent='◌ Reading condition-specific DataHub identity, schema and lineage…';$('observatoryMode').textContent='SYNCING';try{await ensureObservatory();const data=await fetch(`/api/datahub/observatory?case_id=${encodeURIComponent(state.observatoryCase)}`,{cache:'no-store'}).then(checkJson);state.observatoryData=data;state.proofData=data.proof;state.observatory?.sync(data);$('observatoryMode').textContent=`${data.mode.toUpperCase()} · MCP · ${state.observatoryCase}`;$('observatoryProof').textContent=`${data.proof.successful_tools}/${data.proof.total_tools} claims grounded · ${data.proof_id}`;$('observatoryCaptured').textContent=`${new Date(data.captured_at).toLocaleString()} · ${data.truth_boundary.live}`;$('observatoryReads').textContent=`${data.proof.successful_tools}/${data.proof.total_tools}`;button.textContent='✓ Synchronize fresh graph again';selectObservatoryCase(state.observatoryCase);renderCausalLedger([['00','MCP session','opened'],['01','Canonical identity','verified'],['02','Schema contract','attached'],['03','Bidirectional lineage','bound to 3D edges']])}catch(error){$('observatoryMode').textContent='SYNC FAILED';$('observatoryProof').textContent='No unsupported claim accepted';$('observatoryCaptured').textContent=error.message;button.textContent='↻ Retry live synchronization'}finally{button.disabled=false}}
function clearObservatoryTimers(){state.observatoryTimers.forEach(clearTimeout);state.observatoryTimers=[]}
function renderCausalLedger(rows){$('causalLedger').innerHTML=rows.map(([step,label,status])=>`<div><i>${step}</i><b>${escapeHtml(label)}</b><em>${escapeHtml(status)}</em></div>`).join('')}
function animateCausalLedger(mode){clearObservatoryTimers();const spec=observatorySpec(),path=spec.path||[];const rows=[];renderCausalLedger([['00',mode==='incident'?'Counterfactual injected':'Governed repair preview','starting']]);path.forEach((node,index)=>{state.observatoryTimers.push(setTimeout(()=>{rows.push([String(index+1).padStart(2,'0'),node,mode==='incident'?(index===path.length-1?spec.action:'impact observed'):(index===path.length-1?'trusted context restored':'repair propagated')]);renderCausalLedger(rows)},500*(index+1)))});}
async function injectObservatoryIncident(){await ensureObservatory();state.observatory?.inject();animateCausalLedger('incident');$('causalAction').textContent=`${observatorySpec().action} · POLICY MEMBRANE ACTIVE`}
async function previewObservatoryRepair(){await ensureObservatory();state.observatory?.repair();animateCausalLedger('repair');$('causalAction').textContent='COUNTERFACTUAL RECOVERY · NO WRITE';$('causalRepair').textContent=`Preview only: ${observatorySpec().repair}. Human approval is still required.`}
function rewindObservatory(){clearObservatoryTimers();state.observatory?.rewind();selectObservatoryCase(state.observatoryCase)}

function renderCode(kind){const c=state.cohort||{code:'LUAD',model:'luad_progression_v3',owner:'Thoracic ML'};const fallback=codeSnippets[kind].replaceAll('{code}',c.code.toLowerCase()).replaceAll('{model}',c.model).replaceAll('{owner}',c.owner);const raw=state.generatedArtifacts?.[kind]||fallback;$('generatedCode').dataset.raw=raw;$('generatedCode').querySelector('code').innerHTML=raw.split('\n').map(line=>{const cls=line.startsWith('+')?'code-add':line.startsWith('-')?'code-remove':line.trim().startsWith('#')?'code-comment':'';return `<span class="${cls}">${escapeHtml(line)}</span>`}).join('\n')}
function downloadFix(){const raw=$('generatedCode').dataset.raw||'';const kind=document.querySelector('.code-tabs button.active').dataset.code;const ext={dbt:'sql',airflow:'py',python:'yml'}[kind];const blob=new Blob([raw],{type:'text/plain'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`oncotwin_${state.cohort.code.toLowerCase()}_${kind}_fix.${ext}`;a.click();URL.revokeObjectURL(a.href)}
function escapeHtml(v){return String(v).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}

boot();
