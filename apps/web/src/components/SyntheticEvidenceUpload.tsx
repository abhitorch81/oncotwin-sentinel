import { useEffect, useState } from 'react'
import { Eye, ImagePlus, ShieldCheck, Upload } from 'lucide-react'
import type { CandidateId, ImageEvidenceAnalysis } from '../types'

export function SyntheticEvidenceUpload({
  selectedCandidateId, simulationHour, busy, result, error, onAnalyze,
}: {
  selectedCandidateId: CandidateId | null
  simulationHour: number
  busy: boolean
  result: ImageEvidenceAnalysis | null
  error: string | null
  onAnalyze: (file: File) => void
}) {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  useEffect(() => {
    if (!file) { setPreview(null); return }
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  return <section className="synthetic-evidence glass">
    <div className="synthetic-evidence-title"><span><ImagePlus size={14} /> SYNTHETIC IMAGE EVIDENCE</span><b>GEMINI 3.5 VISION</b></div>
    <p>Upload a synthetic microscopy image. Raw pixels are analyzed in memory and never stored.</p>
    <label className={`evidence-drop ${preview ? 'has-preview' : ''}`}>
      {preview ? <img src={preview} alt="Synthetic evidence preview" /> : <><Upload size={18} /><strong>SELECT PNG · JPEG · WEBP</strong><small>5 MB maximum · synthetic data only</small></>}
      <input type="file" accept="image/png,image/jpeg,image/webp" onChange={event => setFile(event.target.files?.[0] || null)} />
    </label>
    <div className="evidence-context"><span>3D CONTEXT <b>{selectedCandidateId ? `CANDIDATE ${selectedCandidateId}` : 'R7 CLONE'}</b></span><span>TIME <b>T+{simulationHour}H</b></span></div>
    <button type="button" disabled={!file || busy} onClick={() => file && onAnalyze(file)}>
      <Eye size={14} /> {busy ? 'GEMINI 3.5 ANALYZING…' : 'ANALYZE WITH EVIDENCE SCOUT'}
    </button>
    {error && <em className="evidence-error">{error}</em>}
    {result && <div className="evidence-analysis">
      <div><small>{result.evidence_id}</small><b>{result.synthetic_pattern.replaceAll('_', ' ')}</b></div>
      <p>{result.summary}</p>
      <div className="evidence-metrics"><span>R7 MATCH <b>{Math.round(result.r7_similarity * 100)}%</b></span><span>MATRIX SIGNAL <b>{Math.round(result.matrix_resistance_signal * 100)}%</b></span><span>CONFIDENCE <b>{Math.round(result.confidence * 100)}%</b></span></div>
      <ul>{result.observations.map(item => <li key={item}>{item}</li>)}</ul>
      <div className="evidence-provenance"><ShieldCheck size={13} /><span>{result.model} · {result.prior_receipt_comparisons.length} prior receipts compared · raw image not stored</span></div>
      <code>SHA-256 {result.sha256.slice(0, 16)}… · RECEIPT {result.current_receipt_sha256_prefix}</code>
    </div>}
  </section>
}
