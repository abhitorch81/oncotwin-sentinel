import { motion } from 'framer-motion'
import { Binoculars, Dna, ShieldCheck, Sparkles } from 'lucide-react'
import type { AdkTraceStatus, AgentEvent, AgentName } from '../types'

const meta: Record<AgentName, { icon: typeof Binoculars; color: string; code: string }> = {
  'Evidence Scout': { icon: Binoculars, color: '#49dfff', code: '01' },
  'Nano Designer': { icon: Sparkles, color: '#9a7dff', code: '02' },
  'Twin Simulator': { icon: Dna, color: '#75ffbd', code: '03' },
  'Safety Steward': { icon: ShieldCheck, color: '#ffb35d', code: '04' },
}

export function AgentFlightRecorder({ events, visible, approved, traceStatus }: { events: AgentEvent[]; visible: number; approved: boolean; traceStatus: AdkTraceStatus }) {
  const latest = new Map<AgentName, AgentEvent>()
  events.slice(0, visible).forEach(event => latest.set(event.agent, event))
  return <aside className="flight-recorder glass">
    <div className="panel-kicker"><span>AGENT FLEET</span><span className={`trace-mode ${traceStatus}`}>
      {traceStatus === 'succeeded' ? 'GEMINI · VERIFIED' : traceStatus === 'running' || traceStatus === 'queued' ? 'GEMINI · LIVE' : traceStatus === 'fallback' ? 'SAFE FALLBACK' : 'LOCAL TRACE'}
    </span></div>
    <h2>Four agents. One governed mission.</h2>
    <div className="agent-list">
      {(Object.keys(meta) as AgentName[]).map(name => {
        const m = meta[name], event = latest.get(name), Icon = m.icon
        const isApprovedSteward = approved && name === 'Safety Steward'
        const displayStatus = isApprovedSteward ? 'complete' : event?.status || 'waiting'
        const displaySummary = isApprovedSteward
          ? 'Human approval recorded. The governed research receipt is complete and auditable.'
          : event?.summary || 'Awaiting upstream evidence handoff.'
        return <motion.article key={name} className={`agent-card ${displayStatus}`}
          initial={{ opacity: .35, x: 12 }} animate={{ opacity: event ? 1 : .42, x: 0 }}>
          <div className="agent-icon" style={{ color: m.color, borderColor: `${m.color}55` }}><Icon size={17} /></div>
          <div><div className="agent-name"><span>{name}</span><small>{isApprovedSteward ? 'APPROVED' : event?.status || 'STANDBY'}</small></div>
          <p>{displaySummary}</p>
          {event?.tool_names?.length ? <div className="tool-badges">{event.tool_names.map(tool => <span key={tool}>{tool.replaceAll('_', ' ')}</span>)}</div> : null}</div>
          <span className="agent-code">{m.code}</span>
        </motion.article>
      })}
    </div>
    <div className="trace-proof"><span>TRACE RECEIPT</span><code>93f7c9bb4cc8…</code></div>
  </aside>
}
