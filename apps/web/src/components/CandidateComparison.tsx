import type { CandidateId, CandidateResult, SimulationFrame } from '../types'

const colors = { A: '#49dfff', B: '#ff4568', C: '#75ffbd' }

function Metric({ label, value, inverse = false }: { label: string; value: number; inverse?: boolean }) {
  return <div className="metric"><span>{label}</span><div><i style={{ width: `${value * 100}%`, background: inverse ? '#ff6a78' : '#75ffbd' }} /></div><b>{Math.round(value * 100)}</b></div>
}

export function CandidateComparison({ results, selectedId, onSelect, frames, hour = 24 }: {
  results: CandidateResult[]
  selectedId?: CandidateId | null
  onSelect: (id: CandidateId) => void
  frames?: SimulationFrame[]
  hour?: number
}) {
  return <section className="candidate-strip glass">
    <div className="strip-title"><span>SIMULATION READOUT · T+{String(hour).padStart(2, '0')}H</span><strong>delivery / off-target / decision</strong></div>
    <div className="candidates">
      {results.map(result => {
        const frame = frames?.find(item => item.candidate_id === result.candidate.id)
        return <button type="button" key={result.candidate.id}
        aria-pressed={selectedId === result.candidate.id}
        onClick={() => onSelect(result.candidate.id)}
        className={`candidate ${result.decision} ${selectedId === result.candidate.id ? 'selected' : ''}`}>
        <header><span className="candidate-orb" style={{ background: colors[result.candidate.id as keyof typeof colors] }}>{result.candidate.id}</span>
          <div><strong>{result.candidate.name}</strong><small>{result.candidate.particle_size_nm}nm · {result.candidate.surface_charge_mv}mV</small></div>
          <em>{result.decision}</em></header>
        <Metric label="Tumour" value={frame?.tumour_payload_release ?? result.tumour_payload_release} />
        <Metric label="Liver" value={frame?.liver_accumulation ?? result.liver_accumulation} inverse />
        <Metric label="Kidney" value={frame?.kidney_accumulation ?? result.kidney_accumulation} inverse />
      </button>})}
    </div>
  </section>
}
