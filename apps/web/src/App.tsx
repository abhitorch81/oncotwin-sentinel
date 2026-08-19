import { useEffect, useState } from 'react'
import { Activity, AudioLines, CircleHelp, Cloud, Database, FlaskConical, ScanSearch } from 'lucide-react'
import { AgentFlightRecorder } from './components/AgentFlightRecorder'
import { ApprovalMembrane } from './components/ApprovalMembrane'
import { CandidateComparison } from './components/CandidateComparison'
import { CommandCapsule } from './components/CommandCapsule'
import { TwinScene } from './components/TwinScene'
import { approveMission, startMission } from './lib/api'
import { demoMission } from './lib/demo'
import type { Mission } from './types'
import './styles.css'

export default function App() {
  const [mission, setMission] = useState<Mission | null>(null)
  const [visible, setVisible] = useState(0)
  const [running, setRunning] = useState(false)
  const [approved, setApproved] = useState(false)
  const [fallback, setFallback] = useState(false)

  useEffect(() => {
    if (!mission || visible >= mission.events.length) return
    const timer = window.setTimeout(() => setVisible(v => v + 1), visible === 0 ? 250 : 700)
    return () => window.clearTimeout(timer)
  }, [mission, visible])

  const run = async (prompt: string) => {
    setRunning(true); setApproved(false); setVisible(0)
    try { setMission(await startMission(prompt)); setFallback(false) }
    catch { setMission({ ...demoMission, prompt }); setFallback(true) }
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
        <TwinScene onCloneSelect={() => run('Investigate the resistant red clone.')} />
        <div className="scene-heading"><small>NANO SAFETY MISSION / 01</small><h1>Resistant clone<br/><span>under investigation.</span></h1></div>
        <div className="clone-callout"><span /><div><small>SELECTED ANOMALY</small><strong>R7 · RESISTANT CLONE</strong><em>+31% persistence signal</em></div></div>
        <div className="scene-key"><span className="cyan">A · ACCEPTABLE</span><span className="red">B · REJECTED</span><span className="green">C · PREFERRED</span></div>
        {!mission && <button className="investigate" onClick={() => run(demoMission.prompt)}><ScanSearch size={18} /> BEGIN NANO SAFETY MISSION</button>}
        {mission && visible >= mission.events.length && <CandidateComparison results={mission.receipt.results} />}
      </div>
      <AgentFlightRecorder events={mission?.events || []} visible={visible} />
    </section>

    {mission && visible >= mission.events.length && <ApprovalMembrane approved={approved} onApprove={approve} />}
    <CommandCapsule running={running} onRun={run} />
    <footer><span>{fallback ? 'DEMO FALLBACK ACTIVE' : 'API READY'}</span><span>DETERMINISTIC SIM v1</span><span>POLICY nano-safety-v1</span><span>60 FPS TARGET</span></footer>
  </main>
}
