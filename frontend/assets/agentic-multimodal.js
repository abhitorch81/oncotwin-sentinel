const $=id=>document.getElementById(id);
const center=$('agenticCommandCenter');
let voiceEnabled=true,inputModality='text',recognition=null,capabilities=null;
let liveSocket=null,liveConnectPromise=null,mediaStream=null,captureContext=null,captureNode=null,captureSource=null;
let playbackContext=null,playbackAt=0,speechFrames=0,liveListening=false;
const playbackSources=new Set();

function escapeHtml(value=''){return String(value).replace(/[&<>'"]/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]))}
function activeCase(){return document.querySelector('.mission-case.active')?.dataset.case||'feature_quality'}
function activeCohort(){return document.querySelector('.cohort-item.active')?.dataset.code||'LUAD'}
function activeView(){return document.querySelector('.tab.active')?.dataset.view||'mission'}
function commandContext(){return{current_view:activeView(),case_id:activeCase(),cohort:activeCohort()}}
function socketUrl(){return`${location.protocol==='https:'?'wss':'ws'}://${location.host}/api/agentic/live`}

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

function renderCommandResult(data,{nativeAudio=false,latency=null}={}){
  $('agenticLane').textContent=data.lane==='local_fast'?(nativeAudio?'GEMINI → SAFE ROUTER':'LOCAL FAST LANE'):'GOVERNED INVESTIGATION';
  $('agenticIntent').textContent=`${data.intent.replaceAll('_',' ').toUpperCase()} · ${Math.round(data.confidence*100)}%`;
  $('agenticResponse').textContent=data.spoken_response;
  if(latency!==null)$('agenticLatency').textContent=`${latency} MS · ${data.modality.toUpperCase()}`;
  center.classList.toggle('approval-boundary',data.safety.human_confirmation_required);
  renderEvidence(data.evidence);dispatchActions(data.ui_actions);
  if(!nativeAudio)speak(data.spoken_response);
}

async function submitCommand(utterance,modality=inputModality){
  const text=utterance.trim();if(!text)return;
  const started=performance.now();$('agenticSend').disabled=true;$('agenticIntent').textContent='ROUTING · SAFE COMMAND CONTRACT';$('agenticResponse').textContent='Grounding the interaction…';
  try{
    const response=await fetch('/api/agentic/commands',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({utterance:text,modality,...commandContext()})});
    const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:`${response.status} ${response.statusText}`);
    renderCommandResult(data,{latency:Math.round(performance.now()-started)});
  }catch(error){$('agenticIntent').textContent='STOPPED SAFELY';$('agenticResponse').textContent=`No action was executed: ${error.message}`;$('agenticLatency').textContent='SAFE FAILURE';renderEvidence([])}
  finally{$('agenticSend').disabled=false;inputModality='text'}
}

function setupRecognition(){
  const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SpeechRecognition)return;
  recognition=new SpeechRecognition();recognition.lang='en-US';recognition.interimResults=true;recognition.continuous=false;
  recognition.onstart=()=>{$('agenticMic').classList.add('listening');$('agenticInput').placeholder='Fallback listening… speak naturally';$('agenticIntent').textContent='BROWSER VOICE FALLBACK · LISTENING'};
  recognition.onresult=event=>{const transcript=Array.from(event.results).map(result=>result[0].transcript).join('');$('agenticInput').value=transcript;if(event.results[event.results.length-1].isFinal){inputModality='voice';submitCommand(transcript,'voice')}};
  recognition.onerror=event=>{$('agenticResponse').textContent=`Voice input stopped safely: ${event.error}. You can type the same command.`};
  recognition.onend=()=>{$('agenticMic').classList.remove('listening');$('agenticInput').placeholder='Ask the twin to focus, explain, compare or investigate…'};
}

function startFallbackRecognition(){
  if(!recognition){$('agenticResponse').textContent='Gemini Live is unavailable and this browser has no speech-recognition fallback. Type the command instead.';return}
  recognition.start();
}

function bytesToBase64(buffer){
  const bytes=new Uint8Array(buffer);let binary='';
  for(let offset=0;offset<bytes.length;offset+=0x8000)binary+=String.fromCharCode(...bytes.subarray(offset,offset+0x8000));
  return btoa(binary);
}

function base64ToInt16(encoded){
  const binary=atob(encoded),bytes=new Uint8Array(binary.length);
  for(let i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);
  return new Int16Array(bytes.buffer);
}

function stopPlayback(){
  playbackSources.forEach(source=>{try{source.stop()}catch(_error){}});playbackSources.clear();
  if(playbackContext)playbackAt=playbackContext.currentTime;
}

async function playPcm(encoded,sampleRate=24000){
  if(!voiceEnabled)return;
  playbackContext=playbackContext||new AudioContext({sampleRate});
  if(playbackContext.state==='suspended')await playbackContext.resume();
  const pcm=base64ToInt16(encoded),audio=playbackContext.createBuffer(1,pcm.length,sampleRate),channel=audio.getChannelData(0);
  for(let i=0;i<pcm.length;i++)channel[i]=pcm[i]/(pcm[i]<0?0x8000:0x7fff);
  const source=playbackContext.createBufferSource();source.buffer=audio;source.connect(playbackContext.destination);
  const start=Math.max(playbackContext.currentTime+.025,playbackAt);source.start(start);playbackAt=start+audio.duration;playbackSources.add(source);source.onended=()=>playbackSources.delete(source);
}

function setLiveBadge(status){
  const badge=$('agenticLiveBadge');badge.classList.remove('planned','ready','error');
  if(status==='ready'){badge.textContent='GEMINI LIVE · READY';badge.classList.add('ready')}
  else if(status==='configuration_required'){badge.textContent='GEMINI LIVE · CONFIGURE';badge.classList.add('error')}
  else{badge.textContent='GEMINI LIVE · FALLBACK';badge.classList.add('planned')}
}

function handleLiveMessage(message){
  if(message.type==='connected'){
    setLiveBadge('ready');$('agenticLane').textContent='GEMINI LIVE · CONNECTED';$('agenticIntent').textContent=`NATIVE AUDIO · ${message.voice.toUpperCase()}`;$('agenticResponse').textContent='Listening through Gemini Live. Speak naturally; you can interrupt the response.';return;
  }
  if(message.type==='audio'){playPcm(message.data,message.sample_rate||24000);$('agenticIntent').textContent='GEMINI LIVE · SPEAKING';return}
  if(message.type==='input_transcript'){$('agenticInput').value=message.text;$('agenticIntent').textContent='GEMINI LIVE · TRANSCRIBING';return}
  if(message.type==='output_transcript'){$('agenticResponse').textContent=message.text;return}
  if(message.type==='command_result'){renderCommandResult(message.command,{nativeAudio:true});return}
  if(message.type==='interrupted'){stopPlayback();$('agenticIntent').textContent='BARGE-IN · LISTENING';return}
  if(message.type==='turn_complete'){$('agenticLatency').textContent='LIVE TURN COMPLETE';return}
  if(message.type==='reconnect_required'){$('agenticResponse').textContent='Gemini rotated the live session. Tap the microphone to reconnect safely.';stopLiveCapture(false);return}
  if(message.type==='unavailable'){setLiveBadge(message.reason==='configuration_required'?'configuration_required':'disabled');$('agenticResponse').textContent='Gemini Live is unavailable. The deterministic browser voice fallback remains active.';return}
  if(message.type==='error'){$('agenticResponse').textContent=`Live audio stopped safely (${message.code}). The command router remains available.`}
}

function connectLive(){
  if(liveSocket?.readyState===WebSocket.OPEN)return Promise.resolve(liveSocket);
  if(liveConnectPromise)return liveConnectPromise;
  liveConnectPromise=new Promise((resolve,reject)=>{
    const socket=new WebSocket(socketUrl());let settled=false;liveSocket=socket;
    socket.onopen=()=>socket.send(JSON.stringify({type:'context',context:commandContext()}));
    socket.onmessage=event=>{let message;try{message=JSON.parse(event.data)}catch{return}handleLiveMessage(message);if(message.type==='connected'&&!settled){settled=true;resolve(socket)}if(message.type==='unavailable'&&!settled){settled=true;reject(new Error(message.reason))}};
    socket.onerror=()=>{if(!settled){settled=true;reject(new Error('websocket_connection_failed'))}};
    socket.onclose=()=>{if(!settled){settled=true;reject(new Error('websocket_closed_before_ready'))}liveSocket=null;liveConnectPromise=null;center.classList.remove('gemini-live');if(liveListening)stopLiveCapture(false)};
  }).finally(()=>{liveConnectPromise=null});
  return liveConnectPromise;
}

async function startLiveCapture(){
  try{
    const socket=await connectLive();
    mediaStream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false});
    captureContext=new AudioContext();await captureContext.audioWorklet.addModule('/assets/pcm-capture-worklet.js?v=12.1.0');
    captureSource=captureContext.createMediaStreamSource(mediaStream);captureNode=new AudioWorkletNode(captureContext,'oncotwin-pcm16-capture',{processorOptions:{targetSampleRate:16000}});
    const silent=captureContext.createGain();silent.gain.value=0;captureSource.connect(captureNode);captureNode.connect(silent).connect(captureContext.destination);
    captureNode.port.onmessage=event=>{if(event.data.type!=='audio'||socket.readyState!==WebSocket.OPEN)return;const rms=Number(event.data.rms||0);speechFrames=rms>.025?speechFrames+1:0;if(speechFrames===3&&playbackSources.size)stopPlayback();socket.send(JSON.stringify({type:'audio',data:bytesToBase64(event.data.buffer)}))};
    liveListening=true;center.classList.add('gemini-live');$('agenticMic').classList.add('listening','live');$('agenticIntent').textContent='GEMINI LIVE · LISTENING';$('agenticMic').title='Stop Gemini Live microphone';
  }catch(error){stopLiveCapture(false);$('agenticResponse').textContent=`Gemini Live could not start (${error.message}). Switching to the deterministic browser fallback.`;startFallbackRecognition()}
}

async function stopLiveCapture(sendEnd=true){
  liveListening=false;$('agenticMic').classList.remove('listening','live');center.classList.remove('gemini-live');speechFrames=0;
  if(sendEnd&&liveSocket?.readyState===WebSocket.OPEN)liveSocket.send(JSON.stringify({type:'end_turn'}));
  captureNode?.disconnect();captureSource?.disconnect();mediaStream?.getTracks().forEach(track=>track.stop());
  captureNode=null;captureSource=null;mediaStream=null;
  if(captureContext){await captureContext.close().catch(()=>{});captureContext=null}
  $('agenticMic').title='Start voice input';$('agenticIntent').textContent='READY · SAFE COMMAND CONTRACT';
}

async function toggleVoiceInput(){
  if(liveListening){await stopLiveCapture();return}
  const status=capabilities?.lanes?.gemini_live?.status;
  if(status==='ready'&&navigator.mediaDevices&&window.AudioWorkletNode){await startLiveCapture();return}
  startFallbackRecognition();
}

$('agenticForm').addEventListener('submit',event=>{event.preventDefault();submitCommand($('agenticInput').value)});
$('agenticMic').addEventListener('click',toggleVoiceInput);
$('agenticSpeak').addEventListener('click',()=>{voiceEnabled=!voiceEnabled;$('agenticSpeak').textContent=voiceEnabled?'VOICE ON':'VOICE OFF';if(!voiceEnabled){stopPlayback();if('speechSynthesis'in window)speechSynthesis.cancel()}});
$('agenticCollapse').addEventListener('click',()=>{center.classList.toggle('collapsed');$('agenticCollapse').textContent=center.classList.contains('collapsed')?'+':'—'});
document.querySelectorAll('[data-agentic-prompt]').forEach(button=>button.addEventListener('click',()=>{$('agenticInput').value=button.dataset.agenticPrompt;submitCommand(button.dataset.agenticPrompt,'text')}));

setupRecognition();
fetch('/api/agentic/capabilities').then(response=>response.ok?response.json():Promise.reject(new Error('capabilities unavailable'))).then(data=>{capabilities=data;setLiveBadge(data.lanes.gemini_live.status);$('agenticIntent').textContent='READY · SAFE COMMAND CONTRACT'}).catch(()=>{setLiveBadge('disabled')});
addEventListener('beforeunload',()=>{if(liveSocket?.readyState===WebSocket.OPEN)liveSocket.send(JSON.stringify({type:'stop'}));mediaStream?.getTracks().forEach(track=>track.stop())});
