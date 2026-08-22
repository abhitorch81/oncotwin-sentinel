import { Database, FileCheck2, History, RotateCcw } from 'lucide-react'
import type { MemoryProof, Mission } from '../types'

export function EvidenceReceipt({ mission, proof, restored, fallback }: { mission: Mission; proof: MemoryProof | null; restored: boolean; fallback: boolean }) {
  const memories = mission.receipt?.prior_memory_used || []
  return <section className="evidence-receipt glass">
    <div className="receipt-title"><span><FileCheck2 size={14} /> EVIDENCE RECEIPT</span><b className={proof?.healthy && !fallback ? 'healthy' : 'degraded'}>{fallback ? 'DEMO ONLY' : proof?.persistent ? 'FIRESTORE · PERSISTENT' : 'CHECKING MEMORY'}</b></div>
    <div className="receipt-grid">
      <div><small>MISSION</small><code>{mission.id}</code></div>
      <div><small>SHA-256</small><code>{mission.receipt?.receipt_sha256?.slice(0, 16)}…</code></div>
      <div><small>POLICY</small><code>{mission.receipt?.policy_version || 'nano-safety-v1'}</code></div>
    </div>
    <div className="memory-line"><History size={12} /><span>{memories.length} prior receipts retrieved</span>{memories.map(hash => <code key={hash}>{hash}</code>)}</div>
    <div className="persistence-line"><Database size={12} /> {proof?.mission_count ?? '—'} stored missions · {proof?.approval_count ?? '—'} approvals{restored ? <span><RotateCcw size={11} /> RESTORED AFTER RELOAD</span> : null}</div>
  </section>
}
