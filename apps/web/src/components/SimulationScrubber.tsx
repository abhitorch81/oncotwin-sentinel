import { Clock, Pause, Play } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import type { CSSProperties } from 'react'
import type { SimulationFrame } from '../types'

export function SimulationScrubber({ hour, timeline, onChange }: {
  hour: number
  timeline: SimulationFrame[]
  onChange: (hour: number) => void
}) {
  const [playing, setPlaying] = useState(false)
  const breachedAt = useMemo(() => timeline
    .filter(frame => frame.candidate_id === 'B' && frame.liver_accumulation > .45)
    .sort((a, b) => a.hour - b.hour)[0]?.hour, [timeline])
  useEffect(() => {
    if (!playing) return
    const timer = window.setInterval(() => {
      if (hour >= 24) { setPlaying(false); return }
      onChange(hour + 1)
    }, 360)
    return () => window.clearInterval(timer)
  }, [hour, onChange, playing])
  const toggle = () => {
    if (!playing && hour >= 24) onChange(0)
    setPlaying(value => !value)
  }
  return <section className="simulation-scrubber glass" aria-label="Synthetic simulation timeline">
    <button type="button" onClick={toggle} aria-label={playing ? 'Pause simulation' : 'Play simulation'}>
      {playing ? <Pause size={13} /> : <Play size={13} />}
    </button>
    <div className="timeline-clock"><Clock size={13} /><span>T+<strong>{String(hour).padStart(2, '0')}</strong>H</span></div>
    <div className="timeline-track">
      <input type="range" min="0" max="24" step="1" value={hour}
        aria-label="Simulation hour" aria-valuetext={`${hour} hours`}
        onChange={event => { setPlaying(false); onChange(Number(event.target.value)) }}
        style={{ '--timeline-progress': `${hour / 24 * 100}%` } as CSSProperties} />
      <div className="timeline-ticks">{[0, 6, 12, 18, 24].map(tick => <span key={tick}>{tick}H</span>)}</div>
    </div>
    <div className="timeline-breach"><i />B LIVER CEILING · T+{breachedAt ?? '—'}H</div>
    <small>SYNTHETIC KINETICS</small>
  </section>
}
