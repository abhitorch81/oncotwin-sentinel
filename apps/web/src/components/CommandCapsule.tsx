import { Mic, Send, Square } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { GovernedVoiceState } from '../hooks/useGeminiLiveVoice'

export function CommandCapsule({ running, onRun, suggestion, contextual = false,
  voiceState, voiceTranscript, agentTranscript, voiceError, onVoiceToggle }: {
  running: boolean
  onRun: (prompt: string) => void
  suggestion?: string
  contextual?: boolean
  voiceState: GovernedVoiceState
  voiceTranscript: string
  agentTranscript: string
  voiceError: string
  onVoiceToggle: () => void
}) {
  const [prompt, setPrompt] = useState(suggestion || 'Investigate the resistant red clone and find a safer nanoparticle delivery strategy.')
  useEffect(() => { if (suggestion) setPrompt(suggestion) }, [suggestion])
  useEffect(() => { if (voiceTranscript) setPrompt(voiceTranscript) }, [voiceTranscript])
  const active = !['off', 'error'].includes(voiceState)
  const status = voiceState === 'speaking' ? 'AGENT SPEAKING · SPEAK TO INTERRUPT'
      : voiceState === 'interrupted' ? 'PLAYBACK INTERRUPTED · SPEAK NOW'
        : voiceState === 'connecting' ? 'OPENING SECURE DUPLEX VOICE SESSION'
        : voiceState === 'listening' ? 'GEMINI 3.5 VOICE COMMAND · LISTENING'
          : voiceState === 'error' ? `LIVE VOICE ERROR · ${voiceError || 'TEXT READY'}`
            : contextual ? 'MISSION QUESTION · TEXT / GEMINI 3.5 VOICE / 3D' : 'MISSION COMMAND · TEXT / GEMINI 3.5 VOICE / 3D'
  return <div className="command-capsule glass">
    <button className={`mic voice-${voiceState}`} onClick={onVoiceToggle}
      aria-label={voiceState === 'speaking' ? 'Stop agent speech' : active ? 'Close governed voice' : 'Start governed voice'}>
      {active ? <Square size={16} /> : <Mic size={18} />}
    </button>
    <div><small>{status}</small>
      <input value={prompt} onChange={e => setPrompt(e.target.value)} onKeyDown={e => e.key === 'Enter' && onRun(prompt)} aria-label="Mission command" /></div>
    <button className="launch" disabled={running} onClick={() => onRun(prompt)} aria-label="Run mission"><Send size={17} /></button>
    {agentTranscript && active && <output className="voice-transcript" aria-live="polite"><b>GEMINI</b>{agentTranscript}</output>}
  </div>
}
