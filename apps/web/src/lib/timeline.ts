import type { CandidateResult, SimulationFrame } from '../types'

const clamp = (value: number) => Math.max(0, Math.min(1, Math.round(value * 1000) / 1000))

function saturation(hour: number, timeConstant: number) {
  if (hour <= 0) return 0
  return (1 - Math.exp(-hour / timeConstant)) / (1 - Math.exp(-24 / timeConstant))
}

export function buildFallbackTimeline(results: CandidateResult[]): SimulationFrame[] {
  return Array.from({ length: 25 }, (_, hour) => results.map(result => {
    const candidate = result.candidate
    return {
      hour,
      candidate_id: candidate.id,
      tumour_penetration: clamp(result.tumour_penetration * saturation(hour, 4.8 + candidate.particle_size_nm / 45)),
      tumour_payload_release: clamp(result.tumour_payload_release * saturation(hour, Math.max(2.5, candidate.release_half_life_hours / Math.log(2)))),
      liver_accumulation: clamp(result.liver_accumulation * (candidate.id === 'B' ? (hour / 24) ** 1.35 : saturation(hour, 8.5))),
      kidney_accumulation: clamp(result.kidney_accumulation * saturation(hour, 6.2 + candidate.particle_size_nm / 55)),
    }
  })).flat()
}
