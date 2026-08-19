const byId=id=>document.getElementById(id);
const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
let initialized=false;

async function json(response){const data=await response.json().catch(()=>({}));if(!response.ok)throw new Error(data?.detail?.message||data?.detail||`${response.status} ${response.statusText}`);return data}
function state(id,ok,ready='READY'){const node=byId(id);node.textContent=ok?ready:'MISSING';node.classList.toggle('ops-good',Boolean(ok));node.classList.toggle('ops-bad',!ok)}

async function loadCapabilities(){
  try{
    const data=await fetch('/api/cockroach/ops/capabilities',{cache:'no-store'}).then(json);
    state('opsMcpState',data.mcp.connected,data.mcp.connected?'CONNECTED':'MISSING');
    byId('opsMcpDetail').textContent=data.mcp.connected?`${data.mcp.transport} · ${data.mcp.tools.length} read tools`:data.mcp.reason||'not configured';
    state('opsCcloudState',data.ccloud.authenticated,data.ccloud.authenticated?'VERIFIED':data.ccloud.installed?'LOGIN NEEDED':'MISSING');
    byId('opsCcloudDetail').textContent=data.ccloud.authenticated?`${data.ccloud.cluster_count} cluster(s) visible`:data.ccloud.reason||'not authenticated';
    state('opsSkillState',data.agent_skill.installed,data.agent_skill.installed?'LOADED':'MISSING');
    byId('opsSkillDetail').textContent=data.agent_skill.installed?`${data.agent_skill.name} · ${data.agent_skill.sha256.slice(0,10)}…`:data.agent_skill.install_command;
    state('opsVectorState',data.distributed_vector_index.used);
  }catch(error){byId('opsVerdict').textContent='SETUP REQUIRED';byId('opsLedger').innerHTML=`<p>${esc(error.message)}</p>`}
}

function renderProof(data){
  byId('opsVerdict').textContent=data.status;byId('opsVerdict').className=data.status==='PASS'?'ops-good':'ops-warn';
  const rows=(data.mcp_evidence||[]).map((item,index)=>`<article class="ops-tool ${item.ok?'pass':'fail'}"><i>${String(index+1).padStart(2,'0')}</i><div><small>MCP TOOL</small><strong>${esc(item.tool)}</strong><span>${item.ok?'typed result captured':esc(item.message||'tool failed')}</span></div><b>${Number(item.duration_ms||0).toFixed(1)} ms</b></article>`);
  rows.push(`<article class="ops-tool ${data.ccloud.authenticated?'pass':'fail'}"><i>06</i><div><small>CCLOUD CLI</small><strong>cluster list</strong><span>${data.ccloud.authenticated?`${data.ccloud.cluster_count} authenticated cluster(s); credentials redacted`:esc(data.ccloud.reason||'not verified')}</span></div><b>${data.ccloud.authenticated?'VERIFIED':'PARTIAL'}</b></article>`);
  rows.push(`<article class="ops-tool ${data.agent_skill.installed?'pass':'fail'}"><i>07</i><div><small>OFFICIAL AGENT SKILL</small><strong>${esc(data.agent_skill.name)}</strong><span>${esc(data.skill_application?.selected_branch||'health review')} · ${esc((data.agent_skill.sha256||'').slice(0,16))}…</span></div><b>APPLIED</b></article>`);
  byId('opsLedger').innerHTML=rows.join('');byId('opsReceipt').textContent=`sha256:${data.receipt_sha256}`;
}

async function loadRuns(){
  try{const data=await fetch('/api/cockroach/ops/runs?limit=8',{cache:'no-store'}).then(json);byId('opsRunCount').textContent=`${data.count} RUN${data.count===1?'':'S'}`;byId('opsRuns').innerHTML=data.runs.length?data.runs.map(run=>`<article><span class="${run.status==='PASS'?'ops-good':'ops-warn'}">${esc(run.status)}</span><b>${new Date(run.captured_at).toLocaleString()}</b><small>MCP ${esc(run.mcp_transport)} · ccloud ${run.ccloud_verified?'verified':'partial'} · read-only ${run.read_only_verified?'verified':'failed'}</small><code>${esc(run.receipt_sha256.slice(0,22))}…</code></article>`).join(''):'<p>No persisted operations receipts yet.</p>'}catch(error){byId('opsRuns').innerHTML=`<p>${esc(error.message)}</p>`}
}

async function runProof(){
  const button=byId('runOpsProof');button.disabled=true;button.textContent='◌ Agent is inspecting the live cluster…';byId('opsVerdict').textContent='RUNNING';
  try{const data=await fetch('/api/cockroach/ops/proof',{method:'POST'}).then(json);renderProof(data);await loadRuns();await loadCapabilities()}catch(error){byId('opsVerdict').textContent='SAFE FAILURE';byId('opsLedger').innerHTML=`<article class="ops-tool fail"><i>!</i><div><small>PROOF STOPPED</small><strong>Evidence boundary preserved</strong><span>${esc(error.message)}</span></div><b>NO CLAIM</b></article>`}
  finally{button.disabled=false;button.textContent='◎ Run live CockroachDB proof'}
}

export async function initCockroachOps(){if(!initialized){initialized=true;byId('runOpsProof')?.addEventListener('click',runProof)}await Promise.all([loadCapabilities(),loadRuns()])}
