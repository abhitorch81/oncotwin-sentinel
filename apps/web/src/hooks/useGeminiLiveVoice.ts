import { useCallback, useEffect, useRef, useState } from 'react'
import { liveVoiceUrl, synthesizeVoice } from '../lib/api'

export type GovernedVoiceState = 'off' | 'connecting' | 'listening' | 'speaking' | 'interrupted' | 'error'

export type VoiceNavigation = {
  action: 'next_candidate' | 'previous_candidate' | 'select_candidate' |
    'next_hour' | 'previous_hour' | 'set_hour' | 'play_timeline' |
    'pause_timeline' | 'show_approval_boundary'
  candidate_id?: 'A' | 'B' | 'C'
  hour?: number
}

const STOP_INTENT = /^\s*(?:please\s+)?(?:stop(?:\s+(?:speaking|talking|now|please))?|be quiet|cancel(?:\s+speech)?|silence)\s*[.!?]?\s*$/i
const STOP_PREFIX = /^\s*(?:please\s+)?(?:stop(?:\s+(?:speaking|talking|now|please))?|be quiet|cancel(?:\s+speech)?|silence)\s*[,.;:!?-]*\s*/i

function parseVoiceNavigation(text: string): VoiceNavigation | null {
  const normalized = text.trim().toLowerCase().replaceAll('-', ' ')
  const candidate = normalized.match(/\b(?:show|select|focus(?: on)?|open|inspect)\s+(?:me\s+)?(?:the\s+)?(?:candidate\s+)?([abc])\b/i)
  if (candidate) return { action: 'select_candidate', candidate_id: candidate[1].toUpperCase() as 'A' | 'B' | 'C' }
  if (/\b(?:next|forward)\s+candidate\b/.test(normalized)) return { action: 'next_candidate' }
  if (/\b(?:previous|prior|back)\s+candidate\b/.test(normalized)) return { action: 'previous_candidate' }
  if (/\b(?:next|forward)\s+hour\b/.test(normalized)) return { action: 'next_hour' }
  if (/\b(?:previous|prior|back)\s+hour\b/.test(normalized)) return { action: 'previous_hour' }
  const hour = normalized.match(/\b(?:show|set|go|jump|move)(?:\s+to)?\s+(?:time\s+)?(?:t\s*\+?\s*)?(\d{1,2})(?:\s*(?:h|hour|hours))?\b/)
  if (hour) {
    const value = Number(hour[1])
    if (value >= 0 && value <= 24) return { action: 'set_hour', hour: value }
  }
  if (/\b(?:play|start|resume)\s+(?:the\s+)?timeline\b/.test(normalized)) return { action: 'play_timeline' }
  if (/\b(?:pause|stop)\s+(?:the\s+)?timeline\b/.test(normalized)) return { action: 'pause_timeline' }
  if (/\b(?:show|focus(?: on)?|open)\s+(?:the\s+)?(?:human\s+)?approval\s+boundary\b/.test(normalized)) {
    return { action: 'show_approval_boundary' }
  }
  return null
}

function pcm16(buffer: Float32Array, sourceRate: number, targetRate = 16_000): ArrayBuffer {
  const ratio = sourceRate / targetRate
  const length = Math.max(1, Math.floor(buffer.length / ratio))
  const output = new Int16Array(length)
  for (let index = 0; index < length; index += 1) {
    const start = Math.floor(index * ratio)
    const end = Math.min(buffer.length, Math.floor((index + 1) * ratio))
    let sum = 0
    for (let cursor = start; cursor < end; cursor += 1) sum += buffer[cursor]
    const sample = Math.max(-1, Math.min(1, sum / Math.max(1, end - start)))
    output[index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff
  }
  return output.buffer
}

export function useGeminiLiveVoice({
  missionId,
  narration,
  narrationRevision,
  onNavigation,
  onCommand,
}: {
  missionId: string | null
  narration: string
  narrationRevision: number
  onNavigation: (navigation: VoiceNavigation) => void
  onCommand: (command: string) => void
}) {
  const [state, setState] = useState<GovernedVoiceState>('off')
  const [inputTranscript, setInputTranscript] = useState('')
  const [outputTranscript, setOutputTranscript] = useState('')
  const [errorDetail, setErrorDetail] = useState('')
  const [enabled, setEnabled] = useState(false)
  const socket = useRef<WebSocket | null>(null)
  const stream = useRef<MediaStream | null>(null)
  const context = useRef<AudioContext | null>(null)
  const processor = useRef<ScriptProcessorNode | null>(null)
  const player = useRef<HTMLAudioElement | null>(null)
  const playerUrl = useRef('')
  const narrationRef = useRef('')
  const narrationRevisionRef = useRef(0)
  const synthesisSequence = useRef(0)
  const navigationRef = useRef(onNavigation)
  const commandRef = useRef(onCommand)
  const pendingTranscript = useRef('')
  const commandTimer = useRef<number | null>(null)
  navigationRef.current = onNavigation
  commandRef.current = onCommand

  const clearPlayback = useCallback(() => {
    synthesisSequence.current += 1
    if (player.current) {
      player.current.pause()
      player.current.currentTime = 0
      player.current = null
    }
    if (playerUrl.current) URL.revokeObjectURL(playerUrl.current)
    playerUrl.current = ''
  }, [])

  const clearPendingCommand = useCallback(() => {
    if (commandTimer.current !== null) window.clearTimeout(commandTimer.current)
    commandTimer.current = null
    pendingTranscript.current = ''
  }, [])

  const stopSpeech = useCallback(() => {
    clearPlayback()
    if (socket.current?.readyState === WebSocket.OPEN) {
      socket.current.send(JSON.stringify({ type: 'interrupt' }))
    }
    setState(enabled ? 'listening' : 'interrupted')
  }, [clearPlayback, enabled])

  const stop = useCallback(() => {
    clearPendingCommand()
    clearPlayback()
    processor.current?.disconnect()
    processor.current = null
    stream.current?.getTracks().forEach(track => track.stop())
    stream.current = null
    socket.current?.close(1000, 'voice disabled')
    socket.current = null
    if (context.current && context.current.state !== 'closed') void context.current.close()
    context.current = null
    setEnabled(false)
    setState('off')
  }, [clearPendingCommand, clearPlayback])

  const start = useCallback(async () => {
    if (!missionId) {
      setErrorDetail('Start or restore a mission before opening live voice')
      setState('error')
      return
    }
    try {
      setErrorDetail('')
      setInputTranscript('')
      setState('connecting')
      const microphone = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      })
      stream.current = microphone
      const audioContext = new AudioContext({ latencyHint: 'interactive' })
      context.current = audioContext
      await audioContext.resume()
      const ws = new WebSocket(liveVoiceUrl(missionId))
      socket.current = ws

      ws.onmessage = event => {
        const message = JSON.parse(String(event.data)) as {
          type: string; text?: string; detail?: string; final?: boolean
        } & VoiceNavigation
        if (message.type === 'ready') {
          // Opening voice must not replay the already-visible scene narration. Doing so
          // creates an acoustic feedback loop when speakers, rather than headphones, are used.
          narrationRef.current = narration
          narrationRevisionRef.current = narrationRevision
          setEnabled(true)
          setState('listening')
        } else if (message.type === 'input_transcript' && message.text) {
          setInputTranscript(message.text)
          if (message.final) {
            if (STOP_INTENT.test(message.text)) {
              clearPendingCommand()
              stopSpeech()
            } else {
              const commandText = message.text.replace(STOP_PREFIX, '').trim()
              const navigation = parseVoiceNavigation(message.text) || parseVoiceNavigation(commandText)
              if (navigation) {
                clearPendingCommand()
                navigationRef.current(navigation)
                return
              }
              const previous = pendingTranscript.current.trim()
              const fragment = commandText
              if (!previous) pendingTranscript.current = fragment
              else if (fragment.startsWith(previous)) pendingTranscript.current = fragment
              else if (!previous.endsWith(fragment)) pendingTranscript.current = `${previous} ${fragment}`
              if (commandTimer.current !== null) window.clearTimeout(commandTimer.current)
              commandTimer.current = window.setTimeout(() => {
                const command = pendingTranscript.current.trim()
                pendingTranscript.current = ''
                commandTimer.current = null
                if (command) commandRef.current(command)
              }, 700)
            }
          }
        } else if (message.type === 'interrupted') {
          clearPlayback()
          setState('listening')
        } else if (message.type === 'turn_complete') {
          setState(current => current === 'speaking' ? current : 'listening')
        } else if (message.type === 'navigation') {
          navigationRef.current(message)
        } else if (message.type === 'error') {
          setErrorDetail(message.detail || 'Gemini 3.5 transcription failed')
          setState('error')
        }
      }
      ws.onerror = () => {
        setErrorDetail('Gemini 3.5 transcription WebSocket unavailable')
        setState('error')
      }
      ws.onclose = event => {
        if (event.code !== 1000) {
          setErrorDetail(`Gemini 3.5 transcription closed (${event.code})`)
          setState('error')
        }
      }
      ws.onopen = () => {
        const source = audioContext.createMediaStreamSource(microphone)
        const node = audioContext.createScriptProcessor(2048, 1, 1)
        const silent = audioContext.createGain()
        silent.gain.value = 0
        processor.current = node
        let speechFrames = 0
        let bargeInPreRoll: ArrayBuffer[] = []
        node.onaudioprocess = event => {
          if (ws.readyState !== WebSocket.OPEN) return
          const samples = event.inputBuffer.getChannelData(0)
          const packet = pcm16(samples, audioContext.sampleRate)
          let energy = 0
          for (const sample of samples) energy += sample * sample
          const rms = Math.sqrt(energy / samples.length)
          if (player.current) {
            // Preserve a short microphone pre-roll so Gemini receives the first consonant
            // of a barge-in such as "stop". Browser echo cancellation suppresses most of
            // Chirp playback; two sustained near-field frames trigger the interruption.
            bargeInPreRoll.push(packet)
            if (bargeInPreRoll.length > 10) bargeInPreRoll.shift()
            speechFrames = rms > 0.035 ? speechFrames + 1 : 0
            if (speechFrames < 2) return
            clearPlayback()
            clearPendingCommand()
            socket.current?.send(JSON.stringify({ type: 'interrupt' }))
            setState('listening')
            speechFrames = 0
            for (const bufferedPacket of bargeInPreRoll) ws.send(bufferedPacket)
            bargeInPreRoll = []
            return
          } else {
            speechFrames = 0
            bargeInPreRoll = []
          }
          ws.send(packet)
        }
        source.connect(node)
        node.connect(silent)
        silent.connect(audioContext.destination)
      }
    } catch (error) {
      stop()
      setErrorDetail(error instanceof Error ? error.message : 'Microphone startup failed')
      setState('error')
    }
  }, [clearPendingCommand, clearPlayback, missionId, narration, narrationRevision, stop, stopSpeech])

  const toggle = useCallback(() => {
    if (['connecting', 'listening', 'speaking', 'interrupted'].includes(state)) stop()
    else void start()
  }, [start, state, stop])

  useEffect(() => {
    if (!enabled || !narration) return
    if (narration === narrationRef.current && narrationRevision === narrationRevisionRef.current) return
    narrationRef.current = narration
    narrationRevisionRef.current = narrationRevision
    setOutputTranscript(narration)
    const sequence = synthesisSequence.current + 1
    synthesisSequence.current = sequence
    void synthesizeVoice(narration).then(blob => {
      if (sequence !== synthesisSequence.current) return
      if (player.current) {
        player.current.pause()
        player.current.currentTime = 0
      }
      if (playerUrl.current) URL.revokeObjectURL(playerUrl.current)
      playerUrl.current = URL.createObjectURL(blob)
      const audio = new Audio(playerUrl.current)
      player.current = audio
      audio.onplay = () => setState('speaking')
      audio.onended = () => {
        player.current = null
        setState('listening')
      }
      audio.onerror = () => {
        setErrorDetail('Google Cloud speech playback failed')
        setState('error')
      }
      return audio.play()
    }).catch(() => {
      if (sequence === synthesisSequence.current) {
        setErrorDetail('Google Cloud speech rendering failed')
        setState('error')
      }
    })
  }, [clearPlayback, enabled, narration, narrationRevision])

  useEffect(() => stop, [stop])

  return { state, enabled, inputTranscript, outputTranscript, errorDetail, toggle, stop, stopSpeech }
}
