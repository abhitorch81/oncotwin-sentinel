import type { AdkMissionTrace, AdkTraceEvent, AdkTraceStatus, ApprovalResponse, CandidateId, ContextualExplanation, MemoryProof, Mission } from '../types'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function startMission(prompt: string): Promise<Mission> {
  const response = await fetch(`${API}/api/nano/missions/start`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt }),
  })
  if (!response.ok) throw new Error('Mission API unavailable')
  return response.json()
}

export async function getMission(missionId: string): Promise<Mission> {
  const response = await fetch(`${API}/api/nano/missions/${missionId}`)
  if (!response.ok) throw new Error('Stored mission unavailable')
  return response.json()
}

export async function getAdkTrace(missionId: string): Promise<AdkMissionTrace> {
  const response = await fetch(`${API}/api/nano/missions/${missionId}/adk-trace`)
  if (!response.ok) throw new Error('ADK trace unavailable')
  return response.json()
}

export async function getMemoryProof(): Promise<MemoryProof> {
  const response = await fetch(`${API}/api/memory/proof`)
  if (!response.ok) throw new Error('Memory proof unavailable')
  return response.json()
}

export async function askMissionQuestion(
  missionId: string,
  question: string,
  selectedCandidateId: CandidateId | null,
  simulationHour: number,
): Promise<ContextualExplanation> {
  const response = await fetch(`${API}/api/nano/missions/${missionId}/commands`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      command: question,
      channel: 'text',
      selected_candidate_id: selectedCandidateId,
      simulation_hour: simulationHour,
    }),
  })
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { detail?: string } | null
    throw new Error(payload?.detail || 'Contextual explanation unavailable')
  }
  return response.json()
}

export async function requestMissionApproval(missionId: string): Promise<void> {
  const response = await fetch(`${API}/api/nano/missions/${missionId}/request-approval`, { method: 'POST' })
  if (!response.ok) throw new Error('Approval request was denied')
}

export async function approveMission(missionId: string): Promise<ApprovalResponse> {
  const response = await fetch(`${API}/api/nano/missions/${missionId}/approve`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ actor: 'demo-researcher', channel: 'ui', confirmation: 'APPROVE SYNTHETIC RESEARCH MISSION' }),
  })
  if (!response.ok) throw new Error('Approval was denied')
  return response.json()
}

export function streamAdkEvents(
  missionId: string,
  onEvent: (event: AdkTraceEvent) => void,
  onStatus: (status: AdkTraceStatus) => void,
  onTransportError: () => void,
): () => void {
  const source = new EventSource(`${API}/api/nano/missions/${missionId}/adk-events`)
  source.addEventListener('adk', message => {
    onEvent(JSON.parse((message as MessageEvent).data) as AdkTraceEvent)
  })
  source.addEventListener('status', message => {
    const payload = JSON.parse((message as MessageEvent).data) as { status: AdkTraceStatus }
    onStatus(payload.status)
    if (['disabled', 'succeeded', 'fallback'].includes(payload.status)) source.close()
  })
  source.onerror = () => { source.close(); onTransportError() }
  return () => source.close()
}
