import { motion } from 'framer-motion'
import { Binoculars, Dna, ShieldCheck, Sparkles } from 'lucide-react'
import type { AdkTraceStatus, AgentEvent, AgentName } from '../types'

const meta: Record<AgentName, { icon: typeof Binoculars; color: string; code: string }> = {
  'Evidence Scout': { icon: Binoculars, color: '#49dfff', code: '01' },
  'Nano Designer': { icon: Sparkles, color: '#9a7dff', code: '02' },
  'Twin Simulator': { icon: Dna, color: '#75ffbd', code: '03' },
  'Safety Steward': { icon: ShieldCheck, color: '#ffb35d', code: '04' },
}

export function AgentFlightRecorder({ events, visible, approved, traceStatus, receiptHash, activeSequence, onReplay }: { events: AgentEvent[]; visible: number; approved: boolean; traceStatus: AdkTraceStatus; receiptHash?: string; activeSequence?: number; onReplay?: (event: AgentEvent) => void }) {
  const latest = new Map<AgentName, AgentEvent>()
  const visibleEvents = events.slice(0, visible)
  visibleEvents.forEach(event => latest.set(event.agent, event))
  const activeAgent = visibleEvents.at(-1)?.agent
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
        const showArtifact = Boolean(event?.artifact && (activeAgent === name || displayStatus === 'blocked'))
        return <motion.article key={name} className={`agent-card ${displayStatus} ${showArtifact ? 'active-work' : ''} ${event?.sequence === activeSequence ? 'replaying' : ''}`}
          initial={{ opacity: .35, x: 12 }} animate={{ opacity: event ? 1 : .42, x: 0 }}>
          <div className="agent-icon" style={{ color: m.color, borderColor: `${m.color}55` }}><Icon size={17} /></div>
          <div><div className="agent-name"><span>{name}</span><small>{isApprovedSteward ? 'APPROVED' : event?.status || 'STANDBY'}</small></div>
          <p>{displaySummary}</p>
          {event?.tool_names?.length ? <div className="tool-badges">{event.tool_names.map(tool => <span key={tool}>{tool.replaceAll('_', ' ')}</span>)}</div> : null}</div>
          <span className="agent-code">{m.code}</span>
          {showArtifact && event?.artifact ? <div className="artifact-workbench">
            <div className="artifact-heading"><span>{event.artifact.kind.replaceAll('_', ' ')}</span>
              {event.artifact.confidence != null ? <em>{Math.round(event.artifact.confidence * 100)}% confidence</em> : null}</div>
            <strong>{event.artifact.title}</strong>
            <div className="artifact-metrics">{event.artifact.metrics.map(metric =>
              <span className={metric.tone} key={`${metric.label}-${metric.value}`}><small>{metric.label}</small><b>{metric.value}{metric.unit || ''}</b></span>)}</div>
            {event.artifact.evidence_ids.length ? <code>{event.artifact.evidence_ids.join(' · ')}</code> : null}
          </div> : null}
          {event && onReplay ? <button type="button" className="replay-work" onClick={() => onReplay(event)}>
            {event.sequence === activeSequence ? 'VIEWING IN 3D' : 'REPLAY WORK PRODUCT'}
          </button> : null}
        </motion.article>
      })}
    </div>
    <div className="trace-proof"><span>TRACE RECEIPT</span><code>{receiptHash ? `${receiptHash.slice(0, 12)}…` : 'pending'}</code></div>
  </aside>
}
