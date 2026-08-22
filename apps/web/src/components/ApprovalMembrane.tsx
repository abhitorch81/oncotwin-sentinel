import { motion } from 'framer-motion'
import { Fingerprint, LockKeyhole, ShieldAlert } from 'lucide-react'

type Props = {
  approved: boolean
  onApprove: () => void
  busy?: boolean
  auditAvailable?: boolean
  error?: string | null
}

export function ApprovalMembrane({ approved, onApprove, busy = false, auditAvailable = true, error }: Props) {
  return <motion.section className={`approval-membrane ${approved ? 'approved' : ''}`} initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }}>
    <div className="membrane-pulse"><ShieldAlert size={22} /></div>
    <div><small>HUMAN AUTHORITY BOUNDARY</small><strong>{approved ? 'Research mission approved' : 'Autonomy paused before action'}</strong>
      <p>{approved ? 'An auditable approval event has been recorded.' : error || (auditAvailable ? 'Voice cannot approve. Review the evidence receipt and use the explicit control.' : 'Demo fallback cannot create an auditable approval event.')}</p></div>
    <button onClick={onApprove} disabled={approved || busy || !auditAvailable}><Fingerprint size={18} />{approved ? 'APPROVED' : busy ? 'RECORDING…' : auditAvailable ? 'REVIEW & APPROVE' : 'AUDIT UNAVAILABLE'}</button>
    <LockKeyhole size={16} className="lock" />
  </motion.section>
}
