import { Box, BrainCircuit, Database, Image, Mic, MousePointer2, Timer } from 'lucide-react'
import type { AdkTraceStatus, CandidateId, ImageEvidenceAnalysis } from '../types'

export type InputModality = 'text' | 'voice' | 'image' | '3d' | 'timeline'

export function ModalityTrace({ modality, candidateId, hour, evidence, adkStatus, persistent }: {
  modality: InputModality
  candidateId: CandidateId | null
  hour: number
  evidence: ImageEvidenceAnalysis | null
  adkStatus: AdkTraceStatus
  persistent: boolean
}) {
  const InputIcon = modality === 'voice' ? Mic : modality === 'image' ? Image : modality === 'timeline' ? Timer : MousePointer2
  return <section className="modality-trace glass" aria-label="Active multimodal provenance trace">
    <div className="trace-node active"><InputIcon size={13}/><span>INPUT</span><b>{modality.toUpperCase()}</b></div><i>→</i>
    <div className="trace-node"><BrainCircuit size={13}/><span>REASONING</span><b>GEMINI 3.5 · ADK {adkStatus.toUpperCase()}</b></div><i>→</i>
    {evidence && <><div className="trace-node image"><Image size={13}/><span>EVIDENCE</span><b>{evidence.evidence_id}</b></div><i>→</i></>}
    <div className="trace-node"><Box size={13}/><span>3D CONTEXT</span><b>{candidateId ? `CANDIDATE ${candidateId}` : 'R7'} · T+{hour}H</b></div><i>→</i>
    <div className={`trace-node ${persistent ? 'stored' : ''}`}><Database size={13}/><span>PROVENANCE</span><b>{persistent ? 'FIRESTORE' : 'LOCAL'}</b></div>
  </section>
}
