const $=id=>document.getElementById(id);
const center=$('agenticCommandCenter');
let voiceEnabled=true;
let inputModality='text';
let recognition=null;

function escapeHtml(value=''){return String(value).replace(/[&<>'"]/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]))}
function activeCase(){return document.querySelector('.mission-case.active')?.dataset.case||'feature_quality'}
function activeCohort(){return document.querySelector('.cohort-item.active')?.dataset.code||'LUAD'}
function activeView(){return document.querySelector('.tab.active')?.dataset.view||'mission'}

function speak(text){
  if(!voiceEnabled||!('speechSynthesis'in window))return;
  speechSynthesis.cancel();const utterance=new SpeechSynthesisUtterance(text);utterance.rate=.91;utterance.pitch=.98;utterance.volume=.92;speechSynthesis.speak(utterance);
}

function renderEvidence(items=[]){
  const box=$('agenticEvidence');box.hidden=!items.length;
  box.innerHTML=items.map(item=>`<article><span>${item.verified?'✓':'○'}</span><div><small>${escapeHtml(item.label)}</small><b>${escapeHtml(item.value)}</b>${item.source?`<em>${escapeHtml(item.source)}</em>`:''}</div></article>`).join('');
}

function dispatchActions(actions=[]){
  actions.forEach((action,index)=>setTimeout(()=>window.dispatchEvent(new CustomEvent('oncotwin:agentic-action',{detail:action})),index*70));
}

async function submitCommand(utterance,modality=inputModality){
  const text=utterance.trim();if(!text)return;
  const started=performance.now();$('agenticSend').disabled=true;$('agenticIntent').textContent='ROUTING · SAFE COMMAND CONTRACT';$('agenticResponse').textContent='Grounding the interaction…';
  try{
    const response=await fetch('/api/agentic/commands',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({utterance:text,modality,current_view:activeView(),case_id:activeCase(),cohort:activeCohort()})});
    const data=await response.json();if(!response.ok)throw new Error(data.detail||`${response.status} ${response.statusText}`);
    const elapsed=Math.round(performance.now()-started);$('agenticLane').textContent=data.lane==='local_fast'?'LOCAL FAST LANE':'GOVERNED INVESTIGATION';$('agenticIntent').textContent=`${data.intent.replaceAll('_',' ').toUpperCase()} · ${Math.round(data.confidence*100)}%`;$('agenticResponse').textContent=data.spoken_response;$('agenticLatency').textContent=`${elapsed} MS · ${modality.toUpperCase()}`;
    center.classList.toggle('approval-boundary',data.safety.human_confirmation_required);renderEvidence(data.evidence);dispatchActions(data.ui_actions);speak(data.spoken_response);
  }catch(error){$('agenticIntent').textContent='STOPPED SAFELY';$('agenticResponse').textContent=`No action was executed: ${error.message}`;$('agenticLatency').textContent='SAFE FAILURE';renderEvidence([])}
  finally{$('agenticSend').disabled=false;inputModality='text'}
}

function setupRecognition(){
  const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SpeechRecognition){$('agenticMic').classList.add('unsupported');$('agenticMic').title='Browser speech recognition is unavailable; type the command instead.';return}
  recognition=new SpeechRecognition();recognition.lang='en-US';recognition.interimResults=true;recognition.continuous=false;
  recognition.onstart=()=>{$('agenticMic').classList.add('listening');$('agenticInput').placeholder='Listening… speak naturally';$('agenticIntent').textContent='VOICE INPUT · LISTENING'};
  recognition.onresult=event=>{const transcript=Array.from(event.results).map(result=>result[0].transcript).join('');$('agenticInput').value=transcript;if(event.results[event.results.length-1].isFinal){inputModality='voice';submitCommand(transcript,'voice')}};
  recognition.onerror=event=>{$('agenticResponse').textContent=`Voice input stopped safely: ${event.error}. You can type the same command.`};
  recognition.onend=()=>{$('agenticMic').classList.remove('listening');$('agenticInput').placeholder='Ask the twin to focus, explain, compare or investigate…'};
}

$('agenticForm').addEventListener('submit',event=>{event.preventDefault();submitCommand($('agenticInput').value)});
$('agenticMic').addEventListener('click',()=>{if(!recognition)return;$('agenticMic').classList.contains('listening')?recognition.stop():recognition.start()});
$('agenticSpeak').addEventListener('click',()=>{voiceEnabled=!voiceEnabled;$('agenticSpeak').textContent=voiceEnabled?'VOICE ON':'VOICE OFF';if(!voiceEnabled&&'speechSynthesis'in window)speechSynthesis.cancel()});
$('agenticCollapse').addEventListener('click',()=>{center.classList.toggle('collapsed');$('agenticCollapse').textContent=center.classList.contains('collapsed')?'+':'—'});
document.querySelectorAll('[data-agentic-prompt]').forEach(button=>button.addEventListener('click',()=>{$('agenticInput').value=button.dataset.agenticPrompt;submitCommand(button.dataset.agenticPrompt,'text')}));
setupRecognition();
fetch('/api/agentic/capabilities').then(response=>response.ok?response.json():null).then(data=>{if(data)$('agenticIntent').textContent='READY · SAFE COMMAND CONTRACT'}).catch(()=>{});
