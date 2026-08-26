import type { CandidateId, CandidateResult } from '../types'

const colors = { A: '#49dfff', B: '#ff4568', C: '#75ffbd' }

function Metric({ label, value, inverse = false }: { label: string; value: number; inverse?: boolean }) {
  return <div className="metric"><span>{label}</span><div><i style={{ width: `${value * 100}%`, background: inverse ? '#ff6a78' : '#75ffbd' }} /></div><b>{Math.round(value * 100)}</b></div>
}

export function CandidateComparison({ results, selectedId, onSelect }: {
  results: CandidateResult[]
  selectedId?: CandidateId | null
  onSelect: (id: CandidateId) => void
}) {
  return <section className="candidate-strip glass">
    <div className="strip-title"><span>SIMULATION READOUT</span><strong>delivery / off-target / decision</strong></div>
    <div className="candidates">
      {results.map(result => <button type="button" key={result.candidate.id}
        aria-pressed={selectedId === result.candidate.id}
        onClick={() => onSelect(result.candidate.id)}
        className={`candidate ${result.decision} ${selectedId === result.candidate.id ? 'selected' : ''}`}>
        <header><span className="candidate-orb" style={{ background: colors[result.candidate.id as keyof typeof colors] }}>{result.candidate.id}</span>
          <div><strong>{result.candidate.name}</strong><small>{result.candidate.particle_size_nm}nm · {result.candidate.surface_charge_mv}mV</small></div>
          <em>{result.decision}</em></header>
        <Metric label="Tumour" value={result.tumour_payload_release} />
        <Metric label="Liver" value={result.liver_accumulation} inverse />
        <Metric label="Kidney" value={result.kidney_accumulation} inverse />
      </button>)}
    </div>
  </section>
}
