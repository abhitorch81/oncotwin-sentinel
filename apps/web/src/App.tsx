import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Activity, AudioLines, CircleHelp, Cloud, Database, FlaskConical, ScanSearch } from 'lucide-react'
import { AgentFlightRecorder } from './components/AgentFlightRecorder'
import { ApprovalMembrane } from './components/ApprovalMembrane'
import { CandidateComparison } from './components/CandidateComparison'
import { CommandCapsule } from './components/CommandCapsule'
import { EvidenceReceipt } from './components/EvidenceReceipt'
import { SimulationScrubber } from './components/SimulationScrubber'
import { TwinScene } from './components/TwinScene'
import type { RenderQuality } from './components/TwinScene'
import { approveMission, askMissionQuestion, getAdkTrace, getMemoryProof, getMission, persistRerunPreview, requestMissionApproval, startMission, streamAdkEvents } from './lib/api'
import { demoMission } from './lib/demo'
import { buildFallbackTimeline } from './lib/timeline'
import { useGeminiLiveVoice } from './hooks/useGeminiLiveVoice'
import type { VoiceNavigation } from './hooks/useGeminiLiveVoice'
import type { AdkTraceEvent, AdkTraceStatus, AgentEvent, AgentName, BoundedRerunPreview, CandidateId, ContextualExplanation, MemoryProof, Mission } from './types'
import './styles.css'
import './styles/memory-evidence.css'
import './styles/mission-theatre.css'

const ACTIVE_MISSION_KEY = 'oncotwin.activeMissionId'
const APPROVAL_INTENT = /\b(approve|authorize|grant approval|confirm approval)\b/i
const STOP_INTENT = /^\s*(?:please\s+)?(?:stop(?:\s+(?:speaking|talking|now|please))?|be quiet|cancel(?:\s+speech)?|silence)\s*[.!?]?\s*$/i

export default function App() {
  const [mission, setMission] = useState<Mission | null>(null)
  const [visible, setVisible] = useState(0)
  const [running, setRunning] = useState(false)
  const [fallback, setFallback] = useState(false)
  const [memoryProof, setMemoryProof] = useState<MemoryProof | null>(null)
  const [restored, setRestored] = useState(false)
  const [approvalBusy, setApprovalBusy] = useState(false)
  const [approvalError, setApprovalError] = useState<string | null>(null)
  const [adkStatus, setAdkStatus] = useState<AdkTraceStatus>('disabled')
  const [adkEvents, setAdkEvents] = useState<AdkTraceEvent[]>([])
  const [selectedCandidateId, setSelectedCandidateId] = useState<CandidateId | null>(null)
  const [renderQuality, setRenderQuality] = useState<RenderQuality>('balanced')
  const [reducedMotion, setReducedMotion] = useState(false)
  const [simulationHour, setSimulationHour] = useState(24)
  const [explanation, setExplanation] = useState<ContextualExplanation | null>(null)
  const [rerun, setRerun] = useState<BoundedRerunPreview | null>(null)
  const [persistBusy, setPersistBusy] = useState(false)
  const [voiceAuthorityMessage, setVoiceAuthorityMessage] = useState('')
  const [voiceNarrationRevision, setVoiceNarrationRevision] = useState(0)
  const [timelinePlaying, setTimelinePlaying] = useState(false)
  const closeStream = useRef<(() => void) | null>(null)
  const runLock = useRef(false)
  const askLock = useRef(false)
  const approved = mission?.state === 'approved'

  const useDeterministicTrace = fallback || adkStatus === 'fallback' || adkStatus === 'disabled'
  const liveAgentEvents = useMemo<AgentEvent[]>(() => adkEvents
    .filter(event => event.visible_agent)
    .map(event => {
      const agent = event.visible_agent as AgentName
      const status = event.phase === 'complete'
        ? agent === 'Safety Steward' ? 'blocked' : 'complete'
        : 'working'
      const fallbackSummary = event.phase === 'tool_call'
        ? `Called bounded tool: ${event.tool_names.join(', ').replaceAll('_', ' ')}.`
        : event.phase === 'complete'
          ? agent === 'Safety Steward' ? 'Policy complete. Autonomy paused for human approval.' : 'Output validated and handed to the next agent.'
          : 'Gemini is processing this governed workflow node.'
      return { sequence: event.sequence, agent, status, summary: event.summary || fallbackSummary,
        evidence_ids: event.artifact?.evidence_ids || [],
        scene_action: event.scene_patch?.action || event.scene_action || undefined,
        tool_names: event.tool_names, artifact: event.artifact, scene_patch: event.scene_patch }
    }), [adkEvents])
  const displayEvents = useDeterministicTrace ? mission?.events || [] : liveAgentEvents
  const displayVisible = useDeterministicTrace ? visible : displayEvents.length
  const presentationComplete = Boolean(mission) && (
    adkStatus === 'succeeded' || (useDeterministicTrace && visible >= (mission?.events.length || 0))
  )
  const visibleSceneEvents = displayEvents.slice(0, displayVisible)
  const activeSceneEvent = [...visibleSceneEvents].reverse().find(event => event.scene_patch || event.scene_action)
  const sceneAction = activeSceneEvent?.scene_patch?.action || activeSceneEvent?.scene_action
  const scenePatch = activeSceneEvent?.scene_patch || undefined
  const activeArtifact = [...visibleSceneEvents].reverse().find(event => event.artifact)?.artifact
  const activeResults = rerun?.results || mission?.receipt.results || []
  const selectedResult = activeResults.find(result => result.candidate.id === selectedCandidateId)
  const timeline = useMemo(() => {
    if (!mission) return []
    if (rerun) return rerun.timeline
    return mission.receipt.timeline?.length ? mission.receipt.timeline : buildFallbackTimeline(mission.receipt.results)
  }, [mission, rerun])
  const simulationFrames = useMemo(() => timeline.filter(frame => frame.hour === simulationHour), [simulationHour, timeline])
  const selectedFrame = simulationFrames.find(frame => frame.candidate_id === selectedCandidateId)
  const effectiveScenePatch = rerun?.scene_patch || explanation?.scene_patch || scenePatch
  const updatePerformance = useCallback((quality: RenderQuality, reduced: boolean) => {
    setRenderQuality(quality)
    setReducedMotion(reduced)
  }, [])
  const selectCandidate = useCallback((candidateId: CandidateId | null) => {
    setSelectedCandidateId(candidateId)
    setExplanation(null)
    setRerun(null)
  }, [])
  const changeSimulationHour = useCallback((hour: number) => {
    setSimulationHour(hour)
    setExplanation(null)
  }, [])

  useEffect(() => {
    if (!timelinePlaying) return
    const timer = window.setInterval(() => {
      setSimulationHour(hour => {
        if (hour >= 24) { setTimelinePlaying(false); return 24 }
        return hour + 1
      })
    }, 450)
    return () => window.clearInterval(timer)
  }, [timelinePlaying])

  useEffect(() => {
    if (!mission || !useDeterministicTrace || visible >= mission.events.length) return
    const timer = window.setTimeout(() => setVisible(v => v + 1), visible === 0 ? 250 : 1600)
    return () => window.clearTimeout(timer)
  }, [mission, visible, useDeterministicTrace])

  useEffect(() => () => closeStream.current?.(), [])

  useEffect(() => {
    let active = true
    getMemoryProof().then(proof => active && setMemoryProof(proof)).catch(() => undefined)
    const missionId = window.localStorage.getItem(ACTIVE_MISSION_KEY)
    if (missionId) getMission(missionId).then(async saved => {
      if (!active) return
      setMission(saved); setVisible(saved.events.length); setFallback(false); setRestored(true)
      try {
        const trace = await getAdkTrace(missionId)
        if (!active) return
        setAdkEvents(trace.events)
        setAdkStatus(trace.status)
      } catch {
        if (active) setAdkStatus('disabled')
      }
    }).catch(() => window.localStorage.removeItem(ACTIVE_MISSION_KEY))
    return () => { active = false }
  }, [])

  const run = async (prompt: string) => {
    if (runLock.current) return
    runLock.current = true
    closeStream.current?.()
    setRunning(true); setVisible(0); setAdkEvents([]); setAdkStatus('queued'); setRestored(false); setApprovalError(null); setSelectedCandidateId(null); setSimulationHour(24); setExplanation(null); setRerun(null)
    try {
      const created = await startMission(prompt)
      setMission(created); setFallback(false); window.localStorage.setItem(ACTIVE_MISSION_KEY, created.id)
      getMemoryProof().then(setMemoryProof).catch(() => undefined)
      closeStream.current = streamAdkEvents(
        created.id,
        event => setAdkEvents(current => current.some(item => item.sequence === event.sequence) ? current : [...current, event]),
        setAdkStatus,
        () => setAdkStatus('fallback'),
      )
    }
    catch { setMission({ ...demoMission, prompt }); setFallback(true); setAdkStatus('fallback'); window.localStorage.removeItem(ACTIVE_MISSION_KEY) }
    finally { runLock.current = false; setRunning(false) }
  }
  const ask = async (question: string, channel: 'text' | 'voice' = 'text') => {
    if (!mission || askLock.current) return
    askLock.current = true
    setRunning(true); setApprovalError(null)
    try {
      const response = await askMissionQuestion(mission.id, question, selectedCandidateId, simulationHour, channel)
      if (response.kind === 'bounded_rerun') {
        setRerun(response)
        setExplanation(null)
      } else {
        setExplanation(response)
        setRerun(null)
      }
      setSelectedCandidateId(response.candidate_id)
      setSimulationHour(response.focus_hour)
      if (channel === 'voice') setVoiceNarrationRevision(revision => revision + 1)
    } catch (error) {
      setApprovalError(error instanceof Error ? error.message : 'Contextual explanation unavailable')
    } finally { askLock.current = false; setRunning(false) }
  }
  const approve = async () => {
    if (!mission) return
    if (fallback) { setApprovalError('Demo fallback cannot claim an auditable approval. Restore the API connection first.'); return }
    setApprovalBusy(true); setApprovalError(null)
    try {
      await requestMissionApproval(mission.id)
      await approveMission(mission.id)
      const saved = await getMission(mission.id)
      setMission(saved)
      setMemoryProof(await getMemoryProof())
    } catch (error) {
      setApprovalError(error instanceof Error ? error.message : 'Approval could not be recorded')
    } finally { setApprovalBusy(false) }
  }
  const persistRerun = async () => {
    if (!mission || !rerun || persistBusy) return
    if (fallback) { setApprovalError('Demo fallback cannot persist an auditable child receipt. Restore the API connection first.'); return }
    setPersistBusy(true); setApprovalError(null)
    try {
      const response = await persistRerunPreview(mission.id, rerun)
      const child = response.child_mission
      closeStream.current?.()
      setMission(child); setRerun(null); setExplanation(null); setVisible(0); setAdkEvents([]); setAdkStatus('disabled')
      setSelectedCandidateId(null); setSimulationHour(24); setRestored(false)
      window.localStorage.setItem(ACTIVE_MISSION_KEY, child.id)
      setMemoryProof(await getMemoryProof())
    } catch (error) {
      setApprovalError(error instanceof Error ? error.message : 'Child mission could not be persisted')
    } finally { setPersistBusy(false) }
  }
  const voiceNarration = explanation?.spoken_text || rerun?.spoken_text || activeSceneEvent?.summary || ''
  const governedNarration = voiceAuthorityMessage || voiceNarration
  const handleVoiceNavigation = useCallback((navigation: VoiceNavigation) => {
    const ids = activeResults.map(result => result.candidate.id as CandidateId)
    const current = selectedCandidateId ? ids.indexOf(selectedCandidateId) : -1
    const announce = (message: string) => {
      setVoiceAuthorityMessage(message)
      setVoiceNarrationRevision(revision => revision + 1)
    }
    if (navigation.action === 'next_candidate' && ids.length) {
      const target = ids[(current + 1 + ids.length) % ids.length]
      selectCandidate(target)
      announce(`Candidate ${target} selected.`)
    } else if (navigation.action === 'previous_candidate' && ids.length) {
      const target = ids[(current - 1 + ids.length) % ids.length]
      selectCandidate(target)
      announce(`Candidate ${target} selected.`)
    } else if (navigation.action === 'select_candidate' && navigation.candidate_id) {
      selectCandidate(navigation.candidate_id)
      announce(`Candidate ${navigation.candidate_id} selected.`)
    } else if (navigation.action === 'next_hour') {
      const hour = Math.min(24, simulationHour + 1)
      changeSimulationHour(hour)
      announce(`Simulation moved to T plus ${hour} hours.`)
    } else if (navigation.action === 'previous_hour') {
      const hour = Math.max(0, simulationHour - 1)
      changeSimulationHour(hour)
      announce(`Simulation moved to T plus ${hour} hours.`)
    } else if (navigation.action === 'set_hour' && typeof navigation.hour === 'number') {
      changeSimulationHour(navigation.hour)
      announce(`Simulation moved to T plus ${navigation.hour} hours.`)
    } else if (navigation.action === 'play_timeline') {
      if (simulationHour >= 24) changeSimulationHour(0)
      setTimelinePlaying(true)
      announce('Simulation timeline playing.')
    } else if (navigation.action === 'pause_timeline') {
      setTimelinePlaying(false)
      announce('Simulation timeline paused.')
    } else if (navigation.action === 'show_approval_boundary') {
      setTimelinePlaying(false)
      setSimulationHour(24)
      setSelectedCandidateId(null)
      announce('Human authority boundary. Voice and agents cannot approve this mission.')
    }
  }, [activeResults, changeSimulationHour, selectCandidate, selectedCandidateId, simulationHour])
  const routeVoiceCommand = (command: string) => {
    if (APPROVAL_INTENT.test(command)) {
      const refusal = 'I cannot approve this research mission. Voice and agents have no approval authority. Use the explicit human review and approval control.'
      setVoiceAuthorityMessage(refusal)
      setVoiceNarrationRevision(revision => revision + 1)
      setApprovalError('Voice approval blocked. Explicit human UI confirmation is required.')
      return
    }
    setVoiceAuthorityMessage('')
    if (mission) void ask(command, 'voice')
    else void run(command)
  }
  const voice = useGeminiLiveVoice({
    missionId: mission?.id || null,
    narration: mission ? governedNarration : '',
    narrationRevision: voiceNarrationRevision,
    onNavigation: handleVoiceNavigation,
    onCommand: routeVoiceCommand,
  })
  const submitCommand = (command: string) => {
    if (STOP_INTENT.test(command)) { voice.stopSpeech(); return }
    if (APPROVAL_INTENT.test(command)) { routeVoiceCommand(command); return }
    setVoiceAuthorityMessage('')
    if (mission) void ask(command)
    else void run(command)
  }

  return <main>
    <header className="topbar">
      <div className="brand"><div className="brand-mark"><Activity size={19} /></div><div><strong>ONCOTWIN <i>SENTINEL</i></strong><small>LIVING EVIDENCE · SYNTHETIC RESEARCH ONLY</small></div></div>
      <nav><span><Cloud size={13} /> CLOUD RUN TARGET</span><span className={`memory-state ${memoryProof?.healthy ? '' : 'degraded'}`}><Database size={13} /> {memoryProof?.persistent ? 'FIRESTORE LIVE' : 'MEMORY CHECK'}</span><span className={`voice-state voice-${voice.state}`}><AudioLines size={13} /> GEMINI 3.5 LIVE INPUT · ADK 3.5 · {voice.state.toUpperCase()}</span></nav>
      <button aria-label="Help"><CircleHelp size={18} /></button>
    </header>

    <div className="truth-boundary"><FlaskConical size={13} /> Synthetic research simulation — not medical advice, diagnosis, or treatment.</div>
    <section className="stage">
      <div className="viewport">
        <TwinScene onCloneSelect={() => run('Investigate the resistant red clone.')}
          onCandidateSelect={selectCandidate} selectedCandidateId={selectedCandidateId}
          sceneAction={rerun?.scene_patch.action || explanation?.scene_patch.action || sceneAction}
          scenePatch={rerun?.scene_patch || explanation?.scene_patch || scenePatch} onPerformanceChange={updatePerformance}
          simulationHour={simulationHour} simulationFrames={simulationFrames} candidateResults={activeResults} />
        <div className="scene-heading"><small>NANO SAFETY MISSION / 01</small><h1>Resistant clone<br/><span>under investigation.</span></h1></div>
        <div className="clone-callout"><span /><div><small>SELECTED ANOMALY</small><strong>R7 · RESISTANT CLONE</strong><em>+31% persistence signal</em></div></div>
        <div className="scene-key"><span className="cyan">A · ACCEPTABLE</span><span className="red">B · REJECTED</span><span className="green">C · PREFERRED</span></div>
        {rerun ? <div className={`scene-artifact contextual-explanation rerun-preview rerun-${rerun.after.decision}`}>
          <button type="button" className="explanation-close" aria-label="Close bounded rerun preview" onClick={() => setRerun(null)}>×</button>
          <small>TWIN SIMULATOR · BOUNDED PREVIEW</small><strong>{rerun.candidate_id} · {rerun.change.previous_value} → {rerun.change.requested_value} NM</strong>
          <span>{rerun.summary}</span>
          <div className="explanation-metrics">
            <i className="neutral"><em>OLD LIVER</em><b>{Math.round(rerun.before.liver_accumulation * 100)}%</b></i>
            <i className="warning"><em>NEW LIVER</em><b>{Math.round(rerun.after.liver_accumulation * 100)}%</b></i>
            <i className="good"><em>NEW TUMOUR</em><b>{Math.round(rerun.after.tumour_payload_release * 100)}%</b></i>
          </div>
          <code>PREVIEW ONLY · NOT STORED · {rerun.preview_sha256.slice(0, 12)}</code>
          <button type="button" className="persist-rerun" disabled={persistBusy} onClick={persistRerun}>
            {persistBusy ? 'PERSISTING CHILD RECEIPT…' : 'PERSIST AS CHILD RUN · HUMAN ACTION'}
          </button>
        </div> : explanation ? <div className={`scene-artifact contextual-explanation explanation-${explanation.decision}`}>
          <button type="button" className="explanation-close" aria-label="Close Safety Steward explanation" onClick={() => setExplanation(null)}>×</button>
          <small>SAFETY STEWARD · VOICE-READY</small><strong>{explanation.candidate_id} · {explanation.decision}</strong>
          <span>{explanation.explanation}</span>
          <div className="explanation-metrics">{explanation.metrics.map(metric => <i className={metric.tone} key={metric.label}>
            <em>{metric.label}</em><b>{metric.value}{metric.unit || ''}</b></i>)}</div>
          <code>{explanation.evidence_ids.join(' · ')} · {explanation.source_receipt_sha256_prefix}</code>
        </div> : mission?.lineage ? <div className="scene-artifact persisted-child-artifact">
          <small>CHILD RECEIPT · HUMAN-PERSISTED</small>
          <strong>{mission.lineage.candidate_id} bounded rerun stored</strong>
          <span>Parent evidence remains immutable. This child requires its own human approval.</span>
          <code>{mission.lineage.parent_mission_id} → {mission.id}</code>
        </div> : activeArtifact && <div className={`scene-artifact artifact-${activeArtifact.kind}`}>
          <small>ACTIVE WORK PRODUCT</small><strong>{activeArtifact.title}</strong>
          <span>{activeArtifact.detail}</span>
        </div>}
        {effectiveScenePatch && <div className={`scene-camera-cue cue-${effectiveScenePatch.emphasis}`}>
          <i /><span>CAMERA LOCK</span><strong>{effectiveScenePatch.camera_target.replaceAll('_', ' ')}</strong>
        </div>}
        {selectedResult && !explanation && !rerun && <div className={`candidate-inspector ${selectedResult.decision}`}>
          <button type="button" className="inspector-close" aria-label="Close candidate inspection" onClick={() => selectCandidate(null)}>×</button>
          <small>SELECTED SYNTHETIC CANDIDATE · {selectedResult.candidate.id}</small>
          <h3>{selectedResult.candidate.name}<em>{selectedResult.decision}</em></h3>
          <div className="inspector-parameters">
            <span><i>SIZE</i><b>{selectedResult.candidate.particle_size_nm} nm</b></span>
            <span><i>CHARGE</i><b>{selectedResult.candidate.surface_charge_mv} mV</b></span>
            <span><i>LIGAND</i><b>{Math.round(selectedResult.candidate.ligand_affinity * 100)}%</b></span>
            <span><i>STEALTH</i><b>{Math.round(selectedResult.candidate.stealth_score * 100)}%</b></span>
            <span><i>TUMOUR · {simulationHour}H</i><b>{Math.round((selectedFrame?.tumour_payload_release ?? selectedResult.tumour_payload_release) * 100)}%</b></span>
            <span><i>LIVER · {simulationHour}H</i><b>{Math.round((selectedFrame?.liver_accumulation ?? selectedResult.liver_accumulation) * 100)}%</b></span>
          </div>
          <p>{selectedResult.reason}</p>
          <button type="button" className="explain-candidate" onClick={() => ask(`Why was candidate ${selectedResult.candidate.id} ${selectedResult.decision}?`)}>
            ASK SAFETY STEWARD WHY
          </button>
          {selectedResult.candidate.id === 'B' && <button type="button" className="rerun-candidate" onClick={() => ask('Reduce candidate B to 70 nm and rerun')}>
            PREVIEW B AT 70 NM
          </button>}
        </div>}
        {!mission && <button className="investigate" onClick={() => run(demoMission.prompt)}><ScanSearch size={18} /> BEGIN NANO SAFETY MISSION</button>}
        {mission && presentationComplete && <SimulationScrubber hour={simulationHour} timeline={timeline} onChange={changeSimulationHour} />}
        {mission && presentationComplete && <CandidateComparison results={activeResults}
          selectedId={selectedCandidateId} onSelect={selectCandidate} frames={simulationFrames} hour={simulationHour} />}
      </div>
      <div className="right-rail">
        <AgentFlightRecorder events={displayEvents} visible={displayVisible} approved={approved} traceStatus={fallback ? 'fallback' : adkStatus} receiptHash={mission?.receipt?.receipt_sha256} />
        {mission && presentationComplete && <EvidenceReceipt mission={mission} proof={memoryProof} restored={restored} fallback={fallback} />}
        {mission && presentationComplete && <ApprovalMembrane approved={approved} onApprove={approve} busy={approvalBusy} auditAvailable={!fallback && Boolean(memoryProof?.persistent && memoryProof?.healthy)} error={approvalError} />}
      </div>
    </section>

    <CommandCapsule running={running} onRun={submitCommand} contextual={Boolean(mission)}
      suggestion={mission ? selectedCandidateId ? `Why was candidate ${selectedCandidateId} ${selectedResult?.decision || 'classified'}?` : 'Why was candidate B rejected?' : undefined}
      voiceState={voice.state} voiceTranscript={voice.inputTranscript} agentTranscript={voice.outputTranscript}
      voiceError={voice.errorDetail}
      onVoiceToggle={voice.state === 'speaking' ? voice.stopSpeech : voice.toggle} />
    <footer><span>{fallback ? 'DEMO FALLBACK ACTIVE' : mission?.lineage ? 'BOUNDED CHILD · LOCAL TRACE' : `ADK ${adkStatus.toUpperCase()}`}</span><span>{memoryProof?.persistent ? `FIRESTORE · ${memoryProof.mission_count} MISSIONS` : 'MEMORY VERIFYING'}</span><span>VOICE {voice.state.toUpperCase()} · NO AUTHORITY</span><span>POLICY nano-safety-v1</span><span>3D {renderQuality.toUpperCase()}{reducedMotion ? ' · REDUCED MOTION' : ' · ADAPTIVE'}</span></footer>
  </main>
}
