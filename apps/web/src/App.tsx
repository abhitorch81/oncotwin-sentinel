import { useEffect, useMemo, useRef, useState } from 'react'
import { Activity, AudioLines, CircleHelp, Cloud, Database, FlaskConical, ScanSearch } from 'lucide-react'
import { AgentFlightRecorder } from './components/AgentFlightRecorder'
import { ApprovalMembrane } from './components/ApprovalMembrane'
import { CandidateComparison } from './components/CandidateComparison'
import { CommandCapsule } from './components/CommandCapsule'
import { EvidenceReceipt } from './components/EvidenceReceipt'
import { TwinScene } from './components/TwinScene'
import { approveMission, getMemoryProof, getMission, requestMissionApproval, startMission, streamAdkEvents } from './lib/api'
import { demoMission } from './lib/demo'
import type { AdkTraceEvent, AdkTraceStatus, AgentEvent, AgentName, CandidateId, MemoryProof, Mission } from './types'
import './styles.css'
import './styles/memory-evidence.css'
import './styles/mission-theatre.css'

const ACTIVE_MISSION_KEY = 'oncotwin.activeMissionId'

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
  const closeStream = useRef<(() => void) | null>(null)
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
  const selectedResult = mission?.receipt.results.find(result => result.candidate.id === selectedCandidateId)

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
    if (missionId) getMission(missionId).then(saved => {
      if (!active) return
      setMission(saved); setVisible(saved.events.length); setAdkStatus('disabled'); setFallback(false); setRestored(true)
    }).catch(() => window.localStorage.removeItem(ACTIVE_MISSION_KEY))
    return () => { active = false }
  }, [])

  const run = async (prompt: string) => {
    closeStream.current?.()
    setRunning(true); setVisible(0); setAdkEvents([]); setAdkStatus('queued'); setRestored(false); setApprovalError(null); setSelectedCandidateId(null)
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
    finally { setRunning(false) }
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

  return <main>
    <header className="topbar">
      <div className="brand"><div className="brand-mark"><Activity size={19} /></div><div><strong>ONCOTWIN <i>SENTINEL</i></strong><small>LIVING EVIDENCE · SYNTHETIC RESEARCH ONLY</small></div></div>
      <nav><span><Cloud size={13} /> CLOUD RUN TARGET</span><span className={`memory-state ${memoryProof?.healthy ? '' : 'degraded'}`}><Database size={13} /> {memoryProof?.persistent ? 'FIRESTORE LIVE' : 'MEMORY CHECK'}</span><span><AudioLines size={13} /> LIVE VOICE NEXT</span></nav>
      <button aria-label="Help"><CircleHelp size={18} /></button>
    </header>

    <div className="truth-boundary"><FlaskConical size={13} /> Synthetic research simulation — not medical advice, diagnosis, or treatment.</div>
    <section className="stage">
      <div className="viewport">
        <TwinScene onCloneSelect={() => run('Investigate the resistant red clone.')}
          onCandidateSelect={setSelectedCandidateId} selectedCandidateId={selectedCandidateId}
          sceneAction={sceneAction} scenePatch={scenePatch} />
        <div className="scene-heading"><small>NANO SAFETY MISSION / 01</small><h1>Resistant clone<br/><span>under investigation.</span></h1></div>
        <div className="clone-callout"><span /><div><small>SELECTED ANOMALY</small><strong>R7 · RESISTANT CLONE</strong><em>+31% persistence signal</em></div></div>
        <div className="scene-key"><span className="cyan">A · ACCEPTABLE</span><span className="red">B · REJECTED</span><span className="green">C · PREFERRED</span></div>
        {activeArtifact && <div className={`scene-artifact artifact-${activeArtifact.kind}`}>
          <small>ACTIVE WORK PRODUCT</small><strong>{activeArtifact.title}</strong>
          <span>{activeArtifact.detail}</span>
        </div>}
        {scenePatch && <div className={`scene-camera-cue cue-${scenePatch.emphasis}`}>
          <i /><span>CAMERA LOCK</span><strong>{scenePatch.camera_target.replaceAll('_', ' ')}</strong>
        </div>}
        {selectedResult && <div className={`candidate-inspector ${selectedResult.decision}`}>
          <button type="button" aria-label="Close candidate inspection" onClick={() => setSelectedCandidateId(null)}>×</button>
          <small>SELECTED SYNTHETIC CANDIDATE · {selectedResult.candidate.id}</small>
          <h3>{selectedResult.candidate.name}<em>{selectedResult.decision}</em></h3>
          <div className="inspector-parameters">
            <span><i>SIZE</i><b>{selectedResult.candidate.particle_size_nm} nm</b></span>
            <span><i>CHARGE</i><b>{selectedResult.candidate.surface_charge_mv} mV</b></span>
            <span><i>LIGAND</i><b>{Math.round(selectedResult.candidate.ligand_affinity * 100)}%</b></span>
            <span><i>STEALTH</i><b>{Math.round(selectedResult.candidate.stealth_score * 100)}%</b></span>
            <span><i>TUMOUR</i><b>{Math.round(selectedResult.tumour_payload_release * 100)}%</b></span>
            <span><i>LIVER</i><b>{Math.round(selectedResult.liver_accumulation * 100)}%</b></span>
          </div>
          <p>{selectedResult.reason}</p>
        </div>}
        {!mission && <button className="investigate" onClick={() => run(demoMission.prompt)}><ScanSearch size={18} /> BEGIN NANO SAFETY MISSION</button>}
        {mission && presentationComplete && <CandidateComparison results={mission.receipt.results}
          selectedId={selectedCandidateId} onSelect={setSelectedCandidateId} />}
      </div>
      <div className="right-rail">
        <AgentFlightRecorder events={displayEvents} visible={displayVisible} approved={approved} traceStatus={fallback ? 'fallback' : adkStatus} receiptHash={mission?.receipt?.receipt_sha256} />
        {mission && presentationComplete && <EvidenceReceipt mission={mission} proof={memoryProof} restored={restored} fallback={fallback} />}
        {mission && presentationComplete && <ApprovalMembrane approved={approved} onApprove={approve} busy={approvalBusy} auditAvailable={!fallback && Boolean(memoryProof?.persistent && memoryProof?.healthy)} error={approvalError} />}
      </div>
    </section>

    <CommandCapsule running={running} onRun={run} />
    <footer><span>{fallback ? 'DEMO FALLBACK ACTIVE' : `ADK ${adkStatus.toUpperCase()}`}</span><span>{memoryProof?.persistent ? `FIRESTORE · ${memoryProof.mission_count} MISSIONS` : 'MEMORY VERIFYING'}</span><span>POLICY nano-safety-v1</span><span>60 FPS TARGET</span></footer>
  </main>
}
