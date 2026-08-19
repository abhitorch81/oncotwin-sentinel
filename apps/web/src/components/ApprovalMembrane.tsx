import { motion } from 'framer-motion'
import { Fingerprint, LockKeyhole, ShieldAlert } from 'lucide-react'

export function ApprovalMembrane({ approved, onApprove }: { approved: boolean; onApprove: () => void }) {
  return <motion.section className={`approval-membrane ${approved ? 'approved' : ''}`} initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }}>
    <div className="membrane-pulse"><ShieldAlert size={22} /></div>
    <div><small>HUMAN AUTHORITY BOUNDARY</small><strong>{approved ? 'Research mission approved' : 'Autonomy paused before action'}</strong>
      <p>{approved ? 'An auditable approval event has been recorded.' : 'Voice cannot approve. Review the evidence receipt and use the explicit control.'}</p></div>
    <button onClick={onApprove} disabled={approved}><Fingerprint size={18} />{approved ? 'APPROVED' : 'HOLD TO APPROVE'}</button>
    <LockKeyhole size={16} className="lock" />
  </motion.section>
}

