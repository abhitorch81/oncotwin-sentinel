import { ArrowRight, CheckCircle2, CircleDot, ShieldAlert } from 'lucide-react'
import type { AgentEvent, Mission } from '../types'

export function MissionBrief() {
  return <section className="mission-brief" aria-label="Mission brief">
    <span><small>PROBLEM</small><b>R7 resistance persists</b></span>
    <ArrowRight size={12} />
    <span><small>OBJECTIVE</small><b>Safer nano delivery</b></span>
    <ArrowRight size={12} />
    <span><small>GUARDRAIL</small><b>≤45% liver at T+18H</b></span>
    <ArrowRight size={12} />
    <span className="authority"><small>AUTHORITY</small><b>Human decision only</b></span>
  </section>
}

export function DecisionChain({ mission, events, visible, activeSequence, onReplay }: {
  mission: Mission
  events: AgentEvent[]
  visible: number
  activeSequence?: number
  onReplay: (event: AgentEvent) => void
}) {
  const shown = events.slice(0, visible)
  const agentOrder = ['Evidence Scout', 'Nano Designer', 'Twin Simulator', 'Safety Steward'] as const
  const handoffs = agentOrder.map(agent => [...shown].reverse().find(event => event.agent === agent))
  const preferred = mission.receipt.results.find(result => result.candidate.id === mission.receipt.preferred_candidate_id)
  const breach = mission.receipt.results.find(result => mission.receipt.rejected_candidate_ids.includes(result.candidate.id))
  const prior = mission.receipt.prior_memory_used?.length || 0
  const frames = mission.receipt.timeline?.length || 0
  return <section className="decision-board glass" aria-label="Auditable decision chain">
    <div className="panel-kicker"><span>DECISION CHAIN</span><span>RECEIPT-DERIVED</span></div>
    <h3>How the fleet reached candidate {mission.receipt.preferred_candidate_id}</h3>
    <div className="handoff-ribbon">
      {agentOrder.map((agent, index) => {
        const event = handoffs[index]
        return <div className="handoff-step" key={agent}>
          <button type="button" disabled={!event} className={event?.sequence === activeSequence ? 'active' : ''} onClick={() => event && onReplay(event)}>
            <i>{event ? <CheckCircle2 size={12} /> : <CircleDot size={12} />}</i>
            <span><small>{String(index + 1).padStart(2, '0')}</small><b>{agent}</b></span>
          </button>
          {index < agentOrder.length - 1 ? <ArrowRight size={12} /> : null}
        </div>
      })}
    </div>
    <div className="decision-evidence">
      <button type="button" disabled={!shown[0]} onClick={() => shown[0] && onReplay(shown[0])}><small>1 · SIGNAL</small><b>+31% persistence</b><span>R7 isolated</span></button>
      <button type="button" disabled={!shown[1]} onClick={() => shown[1] && onReplay(shown[1])}><small>2 · OPTIONS</small><b>{mission.receipt.results.length} candidates</b><span>bounded designs</span></button>
      <button type="button" disabled={!shown[2]} onClick={() => shown[2] && onReplay(shown[2])}><small>3 · SIMULATION</small><b>{frames || 75} frames</b><span>0–24 hour twin</span></button>
      <button type="button" disabled={!shown[3]} onClick={() => shown[3] && onReplay(shown[3])}><small>4 · POLICY</small><b>{breach?.candidate.id || 'B'} quarantined</b><span>liver ceiling breached</span></button>
    </div>
    <div className="mission-impact">
      <div><ShieldAlert size={15} /><span><small>RISK REMOVED</small><b>{mission.receipt.rejected_candidate_ids.length} unsafe path quarantined</b></span></div>
      <div><CheckCircle2 size={15} /><span><small>RECOMMENDATION</small><b>{preferred?.candidate.name || `Candidate ${mission.receipt.preferred_candidate_id}`} · human review</b></span></div>
      <footer><span>{prior} prior receipts used</span><span>0 autonomous approvals</span></footer>
    </div>
  </section>
}
