import { useEffect, useMemo, useRef, useState } from 'react'
import { Activity, AudioLines, CircleHelp, Cloud, Database, FlaskConical, ScanSearch } from 'lucide-react'
import { AgentFlightRecorder } from './components/AgentFlightRecorder'
import { ApprovalMembrane } from './components/ApprovalMembrane'
import { CandidateComparison } from './components/CandidateComparison'
import { CommandCapsule } from './components/CommandCapsule'
import { TwinScene } from './components/TwinScene'
import { approveMission, startMission, streamAdkEvents } from './lib/api'
import { demoMission } from './lib/demo'
import type { AdkTraceEvent, AdkTraceStatus, AgentEvent, AgentName, Mission } from './types'
import './styles.css'

export default function App() {
  const [mission, setMission] = useState<Mission | null>(null)
  const [visible, setVisible] = useState(0)
  const [running, setRunning] = useState(false)
  const [approved, setApproved] = useState(false)
  const [fallback, setFallback] = useState(false)
  const [adkStatus, setAdkStatus] = useState<AdkTraceStatus>('disabled')
  const [adkEvents, setAdkEvents] = useState<AdkTraceEvent[]>([])
  const closeStream = useRef<(() => void) | null>(null)

  const useDeterministicTrace = fallback || adkStatus === 'fallback' || adkStatus === 'disabled'
  const liveAgentEvents = useMemo<AgentEvent[]>(() => adkEvents
    .filter(event => event.visible_agent)
    .map(event => {
      const agent = event.visible_agent as AgentName
      const status = event.phase === 'complete'
        ? agent === 'Safety Steward' ? 'blocked' : 'complete'
        : 'working'
      const summary = event.phase === 'tool_call'
        ? `Called bounded tool: ${event.tool_names.join(', ').replaceAll('_', ' ')}.`
        : event.phase === 'complete'
          ? agent === 'Safety Steward' ? 'Policy complete. Autonomy paused for human approval.' : 'Output validated and handed to the next agent.'
          : 'Gemini is processing this governed workflow node.'
      return { sequence: event.sequence, agent, status, summary, evidence_ids: [],
        scene_action: event.scene_action || undefined, tool_names: event.tool_names }
    }), [adkEvents])
  const displayEvents = useDeterministicTrace ? mission?.events || [] : liveAgentEvents
  const displayVisible = useDeterministicTrace ? visible : displayEvents.length
  const presentationComplete = Boolean(mission) && (
    adkStatus === 'succeeded' || (useDeterministicTrace && visible >= (mission?.events.length || 0))
  )
  const sceneAction = [...displayEvents].reverse().find(event => event.scene_action)?.scene_action

  useEffect(() => {
    if (!mission || !useDeterministicTrace || visible >= mission.events.length) return
    const timer = window.setTimeout(() => setVisible(v => v + 1), visible === 0 ? 250 : 700)
    return () => window.clearTimeout(timer)
  }, [mission, visible, useDeterministicTrace])

  useEffect(() => () => closeStream.current?.(), [])

  const run = async (prompt: string) => {
    closeStream.current?.()
    setRunning(true); setApproved(false); setVisible(0); setAdkEvents([]); setAdkStatus('queued')
    try {
      const created = await startMission(prompt)
      setMission(created); setFallback(false)
      closeStream.current = streamAdkEvents(
        created.id,
        event => setAdkEvents(current => current.some(item => item.sequence === event.sequence) ? current : [...current, event]),
        setAdkStatus,
        () => setAdkStatus('fallback'),
      )
    }
    catch { setMission({ ...demoMission, prompt }); setFallback(true); setAdkStatus('fallback') }
    finally { setRunning(false) }
  }
  const approve = async () => {
    if (!mission) return
    if (!fallback) await approveMission(mission.id)
    setApproved(true)
  }

  return <main>
    <header className="topbar">
      <div className="brand"><div className="brand-mark"><Activity size={19} /></div><div><strong>ONCOTWIN <i>SENTINEL</i></strong><small>LIVING EVIDENCE · SYNTHETIC RESEARCH ONLY</small></div></div>
      <nav><span><Cloud size={13} /> CLOUD RUN TARGET</span><span><Database size={13} /> MEMORY CONTRACT</span><span><AudioLines size={13} /> LIVE VOICE NEXT</span></nav>
      <button aria-label="Help"><CircleHelp size={18} /></button>
    </header>

    <div className="truth-boundary"><FlaskConical size={13} /> Synthetic research simulation — not medical advice, diagnosis, or treatment.</div>
    <section className="stage">
      <div className="viewport">
        <TwinScene onCloneSelect={() => run('Investigate the resistant red clone.')} sceneAction={sceneAction} />
        <div className="scene-heading"><small>NANO SAFETY MISSION / 01</small><h1>Resistant clone<br/><span>under investigation.</span></h1></div>
        <div className="clone-callout"><span /><div><small>SELECTED ANOMALY</small><strong>R7 · RESISTANT CLONE</strong><em>+31% persistence signal</em></div></div>
        <div className="scene-key"><span className="cyan">A · ACCEPTABLE</span><span className="red">B · REJECTED</span><span className="green">C · PREFERRED</span></div>
        {!mission && <button className="investigate" onClick={() => run(demoMission.prompt)}><ScanSearch size={18} /> BEGIN NANO SAFETY MISSION</button>}
        {mission && presentationComplete && <CandidateComparison results={mission.receipt.results} />}
      </div>
      <div className="right-rail">
        <AgentFlightRecorder events={displayEvents} visible={displayVisible} approved={approved} traceStatus={fallback ? 'fallback' : adkStatus} />
        {mission && presentationComplete && <ApprovalMembrane approved={approved} onApprove={approve} />}
      </div>
    </section>

    <CommandCapsule running={running} onRun={run} />
    <footer><span>{fallback ? 'DEMO FALLBACK ACTIVE' : `ADK ${adkStatus.toUpperCase()}`}</span><span>DETERMINISTIC SIM v1</span><span>POLICY nano-safety-v1</span><span>60 FPS TARGET</span></footer>
  </main>
}
