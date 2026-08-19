import { Mic, Send, Square } from 'lucide-react'
import { useState } from 'react'

export function CommandCapsule({ running, onRun }: { running: boolean; onRun: (prompt: string) => void }) {
  const [prompt, setPrompt] = useState('Investigate the resistant red clone and find a safer nanoparticle delivery strategy.')
  const [listening, setListening] = useState(false)
  const speak = () => {
    const Recognition = (window as unknown as { webkitSpeechRecognition?: new () => { lang: string; start: () => void; onresult: (e: { results: { 0: { transcript: string } }[] }) => void; onend: () => void } }).webkitSpeechRecognition
    if (!Recognition) { setListening(false); return }
    const recognition = new Recognition(); recognition.lang = 'en-US'; setListening(true)
    recognition.onresult = e => setPrompt(e.results[0][0].transcript)
    recognition.onend = () => setListening(false); recognition.start()
  }
  return <div className="command-capsule glass">
    <button className={`mic ${listening ? 'listening' : ''}`} onClick={speak} aria-label="Start voice input">{listening ? <Square size={16} /> : <Mic size={18} />}</button>
    <div><small>{listening ? 'LISTENING — INTERRUPT ANY TIME' : 'MISSION COMMAND · TEXT / VOICE / 3D'}</small>
      <input value={prompt} onChange={e => setPrompt(e.target.value)} onKeyDown={e => e.key === 'Enter' && onRun(prompt)} aria-label="Mission command" /></div>
    <button className="launch" disabled={running} onClick={() => onRun(prompt)} aria-label="Run mission"><Send size={17} /></button>
  </div>
}

