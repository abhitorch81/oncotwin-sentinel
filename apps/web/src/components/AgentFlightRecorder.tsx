import { motion } from 'framer-motion'
import { Binoculars, Dna, ShieldCheck, Sparkles } from 'lucide-react'
import type { AgentEvent, AgentName } from '../types'

const meta: Record<AgentName, { icon: typeof Binoculars; color: string; code: string }> = {
  'Evidence Scout': { icon: Binoculars, color: '#49dfff', code: '01' },
  'Nano Designer': { icon: Sparkles, color: '#9a7dff', code: '02' },
  'Twin Simulator': { icon: Dna, color: '#75ffbd', code: '03' },
  'Safety Steward': { icon: ShieldCheck, color: '#ffb35d', code: '04' },
}

export function AgentFlightRecorder({ events, visible }: { events: AgentEvent[]; visible: number }) {
  const latest = new Map<AgentName, AgentEvent>()
  events.slice(0, visible).forEach(event => latest.set(event.agent, event))
  return <aside className="flight-recorder glass">
    <div className="panel-kicker"><span>ADK FLEET</span><span className="live-dot">LIVE TRACE</span></div>
    <h2>Four agents. One governed mission.</h2>
    <div className="agent-list">
      {(Object.keys(meta) as AgentName[]).map(name => {
        const m = meta[name], event = latest.get(name), Icon = m.icon
        return <motion.article key={name} className={`agent-card ${event?.status || 'waiting'}`}
          initial={{ opacity: .35, x: 12 }} animate={{ opacity: event ? 1 : .42, x: 0 }}>
          <div className="agent-icon" style={{ color: m.color, borderColor: `${m.color}55` }}><Icon size={17} /></div>
          <div><div className="agent-name"><span>{name}</span><small>{event?.status || 'STANDBY'}</small></div>
          <p>{event?.summary || 'Awaiting upstream evidence handoff.'}</p></div>
          <span className="agent-code">{m.code}</span>
        </motion.article>
      })}
    </div>
    <div className="trace-proof"><span>TRACE RECEIPT</span><code>93f7c9bb4cc8…</code></div>
  </aside>
}

