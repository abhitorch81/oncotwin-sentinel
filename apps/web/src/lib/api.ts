import type { Mission } from '../types'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function startMission(prompt: string): Promise<Mission> {
  const response = await fetch(`${API}/api/nano/missions/start`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt }),
  })
  if (!response.ok) throw new Error('Mission API unavailable')
  return response.json()
}

export async function approveMission(missionId: string): Promise<void> {
  const response = await fetch(`${API}/api/nano/missions/${missionId}/approve`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ actor: 'demo-researcher', channel: 'ui', confirmation: 'APPROVE SYNTHETIC RESEARCH MISSION' }),
  })
  if (!response.ok) throw new Error('Approval was denied')
}

