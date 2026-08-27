import { Float, Line, OrbitControls, PerformanceMonitor, Sparkles, Text } from '@react-three/drei'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { RefObject } from 'react'
import * as THREE from 'three'
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib'
import type { CandidateId, CandidateResult, ScenePatch, SimulationFrame } from '../types'

export type RenderQuality = 'high' | 'balanced' | 'conservative'

function useReducedMotion() {
  const [reducedMotion, setReducedMotion] = useState(false)
  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)')
    const update = () => setReducedMotion(query.matches)
    update()
    query.addEventListener?.('change', update)
    return () => query.removeEventListener?.('change', update)
  }, [])
  return reducedMotion
}

function canUseWebGL() {
  if (typeof document === 'undefined') return true
  try {
    const canvas = document.createElement('canvas')
    return Boolean(canvas.getContext('webgl2') || canvas.getContext('webgl'))
  } catch {
    return false
  }
}

function SceneFallback({ reason }: { reason: string }) {
  return <div className="scene-fallback" role="status">
    <span>3D SAFE MODE</span>
    <strong>The scientific receipt remains available.</strong>
    <p>{reason} The agent trace, candidate comparison, evidence receipt, and approval boundary continue to work.</p>
  </div>
}

function AdaptiveQuality({ reducedMotion, onChange }: {
  reducedMotion: boolean
  onChange: (quality: RenderQuality) => void
}) {
  const { setDpr } = useThree()
  const quality = useRef<RenderQuality>('balanced')
  const apply = useCallback((next: RenderQuality) => {
    if (quality.current === next) return
    quality.current = next
    const deviceDpr = typeof window === 'undefined' ? 1 : window.devicePixelRatio || 1
    setDpr(next === 'high' ? Math.min(deviceDpr, 1.7) : next === 'balanced' ? Math.min(deviceDpr, 1.35) : 1)
    onChange(next)
  }, [onChange, setDpr])
  useEffect(() => {
    if (reducedMotion) apply('conservative')
  }, [apply, reducedMotion])
  if (reducedMotion) return null
  return <PerformanceMonitor flipflops={3}
    onIncline={() => apply('high')}
    onDecline={() => apply('conservative')}
    onFallback={() => apply('conservative')} />
}

function WebGLContextGuard({ onContextLost }: { onContextLost: (lost: boolean) => void }) {
  const { gl } = useThree()
  useEffect(() => {
    const canvas = gl.domElement
    const lost = (event: Event) => { event.preventDefault(); onContextLost(true) }
    const restored = () => onContextLost(false)
    canvas.addEventListener('webglcontextlost', lost)
    canvas.addEventListener('webglcontextrestored', restored)
    return () => {
      canvas.removeEventListener('webglcontextlost', lost)
      canvas.removeEventListener('webglcontextrestored', restored)
    }
  }, [gl, onContextLost])
  return null
}

const R7_POSITION: [number, number, number] = [
  Math.sin(7 * 4.1) * (1 + (7 % 5) * .08),
  Math.cos(7 * 2.3) * .78,
  Math.sin(7 * 1.7) * .72,
]

const candidateVisuals: Record<CandidateId, {
  name: string
  color: string
  radius: number
  forgePosition: [number, number, number]
  dockPosition: [number, number, number]
}> = {
  A: { name: 'ASTER-48', color: '#44d7ff', radius: .5, forgePosition: [-2.25, 1.25, -.35], dockPosition: [-1.45, -1.25, .25] },
  B: { name: 'BRIMSTONE-92', color: '#ff3f61', radius: .82, forgePosition: [0, 1.35, -.45], dockPosition: [0, -1.25, .25] },
  C: { name: 'CALYX-61', color: '#75ffbd', radius: .62, forgePosition: [2.25, 1.25, -.35], dockPosition: [1.45, -1.25, .25] },
}

const surfaceDirections = [
  [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1],
  [1, 1, 1], [-1, 1, 1], [1, -1, 1], [1, 1, -1], [-1, -1, 1], [-1, 1, -1],
].map(([x, y, z]) => new THREE.Vector3(x, y, z).normalize())

const cameraShots: Record<ScenePatch['camera_target'] | 'overview', {
  position: [number, number, number]
  focus: [number, number, number]
  fov: number
}> = {
  overview: { position: [0, 1.1, 7.2], focus: [0, 0, 0], fov: 44 },
  clone_r7: { position: [1.35, .72, 4.45], focus: [.42, .18, 0], fov: 39 },
  candidate_forge: { position: [-1.9, 1.65, 6.05], focus: [-.15, .15, 0], fov: 43 },
  tumour_core: { position: [.35, .62, 5.05], focus: [0, -.05, 0], fov: 41 },
  liver_sink: { position: [4.35, 2.25, 4.75], focus: [2.55, .9, -.7], fov: 42 },
  approval_boundary: { position: [0, 2.65, 7.45], focus: [0, .15, 0], fov: 46 },
}

function CameraDirector({ target = 'overview', controls, reducedMotion }: {
  target?: ScenePatch['camera_target'] | 'overview'
  controls: RefObject<OrbitControlsImpl | null>
  reducedMotion: boolean
}) {
  const focus = useRef(new THREE.Vector3(...cameraShots.overview.focus))
  const moving = useRef(true)
  const shot = cameraShots[target]
  const targetPosition = useMemo(() => new THREE.Vector3(...shot.position), [shot])
  const targetFocus = useMemo(() => new THREE.Vector3(...shot.focus), [shot])
  useEffect(() => { moving.current = true }, [target])
  useFrame(({ camera }, delta) => {
    if (!moving.current) return
    const alpha = reducedMotion ? 1 : 1 - Math.exp(-2.8 * Math.min(delta, .1))
    const perspectiveCamera = camera as THREE.PerspectiveCamera
    if (controls.current) controls.current.enabled = false
    camera.position.lerp(targetPosition, alpha)
    focus.current.lerp(targetFocus, alpha)
    perspectiveCamera.fov = THREE.MathUtils.lerp(perspectiveCamera.fov, shot.fov, alpha)
    perspectiveCamera.updateProjectionMatrix()
    camera.lookAt(focus.current)
    if (reducedMotion || (camera.position.distanceTo(targetPosition) < .025 && focus.current.distanceTo(targetFocus) < .025)) {
      moving.current = false
      if (controls.current) {
        controls.current.target.copy(targetFocus)
        controls.current.enabled = true
        controls.current.update()
      }
    }
  })
  return null
}

function CloneSignalOverlay({ reducedMotion }: { reducedMotion: boolean }) {
  const ring = useRef<THREE.Mesh>(null)
  useFrame(({ clock }) => {
    if (!ring.current) return
    const pulse = reducedMotion ? 1 : 1 + Math.sin(clock.elapsedTime * 3.2) * .1
    ring.current.scale.setScalar(pulse)
    if (!reducedMotion) ring.current.rotation.z = clock.elapsedTime * .35
  })
  return <group position={R7_POSITION}>
    <mesh ref={ring} rotation={[Math.PI / 2, 0, 0]}>
      <torusGeometry args={[.42, .018, 10, 72]} />
      <meshBasicMaterial color="#ff4b72" transparent opacity={.9} />
    </mesh>
    <mesh scale={1.8}><icosahedronGeometry args={[.31, 2]} /><meshBasicMaterial color="#ff315e" wireframe transparent opacity={.2} /></mesh>
    <Line points={[[.35, .22, 0], [.85, .62, .12], [1.3, .62, .12]]} color="#ff5879" transparent opacity={.72} lineWidth={1} />
    {[0, 1, 2].map(index => <mesh key={index} position={[.62 + index * .24, .62, .12]}>
      <sphereGeometry args={[.035, 10, 10]} /><meshBasicMaterial color={index === 0 ? '#ff5879' : '#75dfff'} />
    </mesh>)}
    <Text position={[1.3, .78, .12]} fontSize={.1} color="#ff8aa0" anchorX="right">R7 SIGNAL LOCKED</Text>
  </group>
}

function Tumour({ onSelect, overlay, reducedMotion, signal }: {
  onSelect: () => void
  overlay?: ScenePatch['overlay']
  reducedMotion: boolean
  signal: number
}) {
  const group = useRef<THREE.Group>(null)
  const cells = useMemo(() => Array.from({ length: 34 }, (_, i) => ({
    p: [Math.sin(i * 4.1) * (1.0 + (i % 5) * .08), Math.cos(i * 2.3) * .78, Math.sin(i * 1.7) * .72] as [number, number, number],
    s: .19 + (i % 4) * .035,
  })), [])
  useFrame((_, delta) => { if (group.current && !reducedMotion) group.current.rotation.y += delta * .055 })
  return <group ref={group} scale={.94 + signal * .06} onClick={(e) => { e.stopPropagation(); onSelect() }}>
    {cells.map((cell, i) => <mesh key={i} position={cell.p} scale={cell.s}>
      <icosahedronGeometry args={[1, 2]} />
      <meshPhysicalMaterial color={i === 7 ? '#ff315e' : '#7134a8'} emissive={i === 7 ? '#b60035' : '#180926'} emissiveIntensity={i === 7 ? 2.4 : .7} roughness={.25} transmission={.18} />
    </mesh>)}
    {overlay === 'clone_signal' && <CloneSignalOverlay reducedMotion={reducedMotion} />}
    <pointLight color="#ff356d" intensity={1.5 + signal * 5.5} distance={4} position={[.4, .5, 1]} />
  </group>
}

function CandidateForgeOverlay({ reducedMotion }: { reducedMotion: boolean }) {
  const slots = [
    { id: 'A', color: '#44d7ff', position: [-2.25, 1.25, -.35] as [number, number, number] },
    { id: 'B', color: '#ff3f61', position: [0, 1.35, -.45] as [number, number, number] },
    { id: 'C', color: '#75ffbd', position: [2.25, 1.25, -.35] as [number, number, number] },
  ]
  return <group>
    {slots.map((slot, index) => <Float key={slot.id} speed={reducedMotion ? 0 : 1.4 + index * .15} floatIntensity={reducedMotion ? 0 : .12} position={slot.position}>
      <mesh rotation={[Math.PI / 2, 0, 0]}><torusGeometry args={[.52, .018, 10, 64]} /><meshBasicMaterial color={slot.color} transparent opacity={.75} /></mesh>
      <Text position={[0, -.72, 0]} fontSize={.13} color={slot.color} anchorX="center">{slot.id} · FORGE SLOT</Text>
    </Float>)}
    <Line points={[[-3.1, .25, 0], [3.1, .25, 0]]} color="#604f91" transparent opacity={.34} lineWidth={1} />
  </group>
}

function CandidateSurface({ id, color, radius }: { id: CandidateId; color: string; radius: number }) {
  const features = useMemo(() => surfaceDirections.map(direction => {
    const surface = direction.clone().multiplyScalar(radius * 1.02)
    const tip = direction.clone().multiplyScalar(radius * (id === 'B' ? 1.42 : 1.34))
    const quaternion = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction)
    return { surface, tip, quaternion }
  }), [id, radius])
  if (id === 'A') return <>
    <mesh><sphereGeometry args={[radius * 1.18, 28, 20]} /><meshPhysicalMaterial color={color} transparent opacity={.1} transmission={.25} wireframe /></mesh>
    {features.slice(0, 8).map((feature, index) => <mesh key={index} position={feature.tip.clone().multiplyScalar(.9)}>
      <sphereGeometry args={[.035, 8, 8]} /><meshBasicMaterial color="#b9f5ff" transparent opacity={.72} />
    </mesh>)}
  </>
  if (id === 'B') return <>{features.map((feature, index) =>
    <mesh key={index} position={feature.tip.clone().lerp(feature.surface, .48)} quaternion={feature.quaternion}>
      <coneGeometry args={[.075, radius * .42, 7]} /><meshStandardMaterial color={color} emissive={color} emissiveIntensity={.8} />
    </mesh>)}</>
  return <>{features.map((feature, index) => <group key={index}>
    <Line points={[feature.surface, feature.tip]} color={color} transparent opacity={.74} lineWidth={.7} />
    <mesh position={feature.tip}><octahedronGeometry args={[.065, 0]} /><meshStandardMaterial color={color} emissive={color} emissiveIntensity={1.3} /></mesh>
  </group>)}</>
}

function CandidateBody({ id, name, sizeNm, docked, selected, quarantined, preferred, onSelect, reducedMotion }: {
  id: CandidateId
  name?: string
  sizeNm?: number
  docked: boolean
  selected: boolean
  quarantined: boolean
  preferred: boolean
  onSelect: (id: CandidateId) => void
  reducedMotion: boolean
}) {
  const group = useRef<THREE.Group>(null)
  const selection = useRef<THREE.Mesh>(null)
  const visual = candidateVisuals[id]
  const referenceSize = id === 'A' ? 48 : id === 'B' ? 92 : 61
  const radius = visual.radius * THREE.MathUtils.clamp((sizeNm || referenceSize) / referenceSize, .62, 1.38)
  const targetPosition = useMemo(() => new THREE.Vector3(...(docked ? visual.dockPosition : visual.forgePosition)), [docked, visual])
  const targetScale = (docked ? .62 : 1) * (selected ? 1.13 : 1)
  const targetScaleVector = useMemo(() => new THREE.Vector3(targetScale, targetScale, targetScale), [targetScale])
  useEffect(() => () => { document.body.style.cursor = 'default' }, [])
  useFrame(({ clock }, delta) => {
    if (!group.current) return
    const alpha = reducedMotion ? 1 : 1 - Math.exp(-4 * Math.min(delta, .1))
    group.current.position.lerp(targetPosition, alpha)
    group.current.scale.lerp(targetScaleVector, alpha)
    if (!reducedMotion) group.current.rotation.y += delta * (id === 'B' ? .42 : .28)
    if (selection.current) {
      selection.current.rotation.z = reducedMotion ? 0 : clock.elapsedTime * .55
      selection.current.scale.setScalar(reducedMotion ? 1 : 1 + Math.sin(clock.elapsedTime * 3) * .04)
    }
  })
  return <group ref={group} position={visual.forgePosition}
    onClick={event => { event.stopPropagation(); onSelect(id) }}
    onPointerOver={event => { event.stopPropagation(); document.body.style.cursor = 'pointer' }}
    onPointerOut={() => { document.body.style.cursor = 'default' }}>
    <mesh scale={radius}>
      {id === 'A' ? <sphereGeometry args={[1, 28, 22]} /> : id === 'B' ? <dodecahedronGeometry args={[1, 1]} /> : <icosahedronGeometry args={[1, 2]} />}
      <meshPhysicalMaterial color={visual.color} emissive={visual.color} emissiveIntensity={selected ? 1.25 : .55}
        metalness={id === 'B' ? .2 : .05} roughness={id === 'A' ? .18 : .3} transmission={id === 'A' ? .24 : .08} />
    </mesh>
    <CandidateSurface id={id} color={visual.color} radius={radius} />
    {(selected || quarantined || preferred) && <mesh ref={selection} rotation={[Math.PI / 2, 0, 0]}>
      <torusGeometry args={[radius * 1.62, .025, 10, 72]} />
      <meshBasicMaterial color={quarantined ? '#ff315e' : preferred ? '#75ffbd' : '#f3fbff'} transparent opacity={.88} />
    </mesh>}
    <Text position={[0, -radius * 1.65, 0]} fontSize={docked ? .13 : .16} color={visual.color} anchorX="center">{id} · {(name || visual.name).toUpperCase()}</Text>
    {(quarantined || preferred) && <Text position={[0, radius * 1.65, 0]} fontSize={.1}
      color={quarantined ? '#ff6682' : '#75ffbd'} anchorX="center">{quarantined ? 'QUARANTINED' : 'PREFERRED'}</Text>}
  </group>
}

function CandidateGallery({ rank, selectedId, onSelect, reducedMotion, quarantineActive, candidates }: {
  rank: number
  selectedId?: CandidateId | null
  onSelect: (id: CandidateId) => void
  reducedMotion: boolean
  quarantineActive: boolean
  candidates: CandidateResult[]
}) {
  return <group>{(['A', 'B', 'C'] as CandidateId[]).map(id => {
    const result = candidates.find(item => item.candidate.id === id)
    return <CandidateBody key={id} id={id} name={result?.candidate.name} sizeNm={result?.candidate.particle_size_nm}
      docked={rank >= 3} selected={selectedId === id}
      quarantined={rank >= 4 && quarantineActive && id === 'B'} preferred={rank >= 4 && id === 'C'} onSelect={onSelect} reducedMotion={reducedMotion} />
  })}</group>
}

function NanoPath({ id, color, destination, speed, opacity = .7, reducedMotion, timeProgress, deliverySignal }: {
  id: 'A' | 'B' | 'C'
  color: string
  destination: [number, number, number]
  speed: number
  opacity?: number
  reducedMotion: boolean
  timeProgress: number
  deliverySignal: number
}) {
  const particles = useRef<THREE.Group>(null)
  const curve = useMemo(() => new THREE.CatmullRomCurve3([
    new THREE.Vector3(-4.2, id === 'A' ? 1.3 : id === 'B' ? .35 : -1.15, .15),
    new THREE.Vector3(-2.4, id === 'A' ? .85 : id === 'B' ? .25 : -.72, -.25),
    new THREE.Vector3(-.65, id === 'A' ? .35 : id === 'B' ? .12 : -.3, .25),
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(...destination),
  ]), [destination, id])
  const linePoints = useMemo(() => curve.getPoints(56), [curve])
  const particleCount = id === 'C' ? 9 : 7
  useFrame(({ clock }) => {
    if (!particles.current) return
    particles.current.children.forEach((particle, index) => {
      const trail = index / particleCount * .2
      const shimmer = reducedMotion ? 0 : Math.sin(clock.elapsedTime * speed * 12 + index) * .012
      const progress = THREE.MathUtils.clamp(timeProgress - trail + shimmer, 0, 1)
      particle.visible = timeProgress > trail * .7
      particle.position.copy(curve.getPointAt(progress))
      particle.scale.setScalar(.55 + deliverySignal * .65)
    })
  })
  return <group>
    <Line points={linePoints} color={color} transparent opacity={opacity * (.12 + timeProgress * .5)} lineWidth={id === 'C' ? 1.8 : 1.1} />
    <group ref={particles}>{Array.from({ length: particleCount }, (_, index) =>
      <mesh key={index} position={curve.getPointAt(index / particleCount)}>
        <sphereGeometry args={[id === 'B' ? .075 : .06, 12, 12]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={2.2} transparent opacity={opacity} />
      </mesh>)}</group>
    <Text position={destination} fontSize={.11} color={color} anchorX="center">{id}</Text>
  </group>
}

function DistributionOverlay({ reducedMotion, hour, frames }: {
  reducedMotion: boolean
  hour: number
  frames: SimulationFrame[]
}) {
  const timeProgress = hour / 24
  const signal = (id: CandidateId) => frames.find(frame => frame.candidate_id === id)?.tumour_payload_release ?? 0
  return <group>
    <NanoPath id="A" color="#44d7ff" destination={[.35, .18, .15]} speed={.1} opacity={.72}
      reducedMotion={reducedMotion} timeProgress={timeProgress} deliverySignal={signal('A')} />
    <NanoPath id="B" color="#ff3f61" destination={[3.1, 1.15, -1.2]} speed={.16} opacity={.78}
      reducedMotion={reducedMotion} timeProgress={timeProgress} deliverySignal={signal('B')} />
    <NanoPath id="C" color="#75ffbd" destination={[-.1, -.18, .12]} speed={.13} opacity={.95}
      reducedMotion={reducedMotion} timeProgress={timeProgress} deliverySignal={signal('C')} />
  </group>
}

function QuarantineOverlay({ reducedMotion, signal, active }: { reducedMotion: boolean; signal: number; active: boolean }) {
  const cage = useRef<THREE.Group>(null)
  useFrame(({ clock }) => {
    if (!cage.current) return
    cage.current.rotation.y = reducedMotion ? 0 : clock.elapsedTime * .38
    const pulse = reducedMotion ? 1 : 1 + Math.sin(clock.elapsedTime * 4) * .035
    cage.current.scale.setScalar(pulse)
  })
  return <group position={[3.1, 1.15, -1.2]}>
    <group ref={cage}>
      <mesh><boxGeometry args={[1.35, 1.75, 1.15]} /><meshBasicMaterial color="#ff315e" wireframe transparent opacity={active ? .46 : .12 + signal * .18} /></mesh>
      <mesh rotation={[Math.PI / 4, 0, Math.PI / 4]}><torusGeometry args={[.9, .025, 10, 64]} /><meshBasicMaterial color={active ? '#ff5879' : '#ffb35d'} transparent opacity={active ? .8 : .22} /></mesh>
    </group>
    <pointLight color={active ? '#ff315e' : '#ffb35d'} intensity={active ? 3 : signal} distance={3} />
    <Text position={[0, 1.15, 0]} fontSize={.14} color={active ? '#ff6b87' : '#ffbd72'} anchorX="center">{active ? 'B · QUARANTINED' : 'B · RISK RISING'}</Text>
    <Text position={[0, -.98, 0]} fontSize={.09} color="#9e6674" anchorX="center">{active ? 'LIVER CEILING BREACHED' : '45% CEILING MONITORED'}</Text>
  </group>
}

function ApprovalBoundaryOverlay({ reducedMotion }: { reducedMotion: boolean }) {
  const membrane = useRef<THREE.Group>(null)
  useFrame((_, delta) => { if (membrane.current && !reducedMotion) membrane.current.rotation.y += delta * .045 })
  return <group ref={membrane}>
    <mesh scale={[3.25, 2.15, 1.35]}><sphereGeometry args={[1, 32, 20]} /><meshBasicMaterial color="#ffb35d" wireframe transparent opacity={.09} /></mesh>
    <mesh rotation={[Math.PI / 2, 0, 0]}><torusGeometry args={[2.7, .025, 10, 96]} /><meshBasicMaterial color="#ffb35d" transparent opacity={.5} /></mesh>
    <mesh rotation={[Math.PI / 2, 0, Math.PI / 2]}><torusGeometry args={[2.15, .018, 10, 96]} /><meshBasicMaterial color="#75ffbd" transparent opacity={.32} /></mesh>
    <Text position={[0, 2.25, 0]} fontSize={.16} color="#ffc47d" anchorX="center">HUMAN AUTHORITY BOUNDARY</Text>
  </group>
}

function SceneOverlay({ overlay, rank, reducedMotion, hour, frames }: {
  overlay?: ScenePatch['overlay']
  rank: number
  reducedMotion: boolean
  hour: number
  frames: SimulationFrame[]
}) {
  const bLiver = frames.find(frame => frame.candidate_id === 'B')?.liver_accumulation ?? 0
  return <>
    {overlay === 'candidate_blueprints' && <CandidateForgeOverlay reducedMotion={reducedMotion} />}
    {rank >= 3 && <DistributionOverlay reducedMotion={reducedMotion} hour={hour} frames={frames} />}
    {overlay === 'safety_quarantine' && <QuarantineOverlay reducedMotion={reducedMotion} signal={bLiver} active={bLiver > .45} />}
    {overlay === 'approval_membrane' && <ApprovalBoundaryOverlay reducedMotion={reducedMotion} />}
  </>
}

function OrganGhost({ position, label, color, signal }: { position: [number, number, number]; label: string; color: string; signal: number }) {
  return <group position={position} scale={.9 + signal * .18}>
    <mesh scale={[.55, .78, .32]}><sphereGeometry args={[1, 32, 32]} /><meshPhysicalMaterial color={color} transparent opacity={.06 + signal * .28} wireframe /></mesh>
    <pointLight color={color} intensity={signal * 2.6} distance={2.4} />
    <Text position={[0, -.95, 0]} fontSize={.16} color="#758092" anchorX="center">{label}</Text>
  </group>
}

const actionRank: Record<string, number> = {
  focus_clone: 1, spawn_candidates: 2, run_particle_paths: 3,
  reject_candidate: 4, show_approval_membrane: 5,
}

export function TwinScene({ onCloneSelect, onCandidateSelect, selectedCandidateId, sceneAction, scenePatch,
  onPerformanceChange, simulationHour = 24, simulationFrames = [], candidateResults = [] }: {
  onCloneSelect: () => void
  onCandidateSelect: (id: CandidateId) => void
  selectedCandidateId?: CandidateId | null
  sceneAction?: string
  scenePatch?: ScenePatch
  onPerformanceChange?: (quality: RenderQuality, reducedMotion: boolean) => void
  simulationHour?: number
  simulationFrames?: SimulationFrame[]
  candidateResults?: CandidateResult[]
}) {
  const rank = actionRank[sceneAction || ''] || 0
  const tumourSignal = Math.max(0, ...simulationFrames.map(frame => frame.tumour_payload_release))
  const liverSignal = Math.max(0, ...simulationFrames.map(frame => frame.liver_accumulation))
  const kidneySignal = Math.max(0, ...simulationFrames.map(frame => frame.kidney_accumulation))
  const quarantineActive = (simulationFrames.find(frame => frame.candidate_id === 'B')?.liver_accumulation ?? 0) > .45
  const controls = useRef<OrbitControlsImpl>(null)
  const reducedMotion = useReducedMotion()
  const webglAvailable = useMemo(canUseWebGL, [])
  const [contextLost, setContextLost] = useState(false)
  const [renderQuality, setRenderQuality] = useState<RenderQuality>('balanced')
  const sparkleCount = reducedMotion ? 24 : renderQuality === 'high' ? 120 : renderQuality === 'balanced' ? 80 : 40
  const reportQuality = useCallback((quality: RenderQuality) => {
    setRenderQuality(quality)
    onPerformanceChange?.(quality, reducedMotion)
  }, [onPerformanceChange, reducedMotion])
  useEffect(() => {
    if (reducedMotion) reportQuality('conservative')
  }, [reducedMotion, reportQuality])
  if (!webglAvailable) return <SceneFallback reason="WebGL is unavailable in this browser." />
  return <>
  <Canvas camera={{ position: [0, 1.1, 7.2], fov: 44 }} dpr={reducedMotion ? 1 : [1, 1.35]}
    performance={{ min: .45, max: 1, debounce: 200 }}
    gl={{ antialias: true, powerPreference: 'high-performance', alpha: false }}
    fallback={<SceneFallback reason="The browser could not initialize the WebGL renderer." />}>
    <AdaptiveQuality reducedMotion={reducedMotion} onChange={reportQuality} />
    <WebGLContextGuard onContextLost={setContextLost} />
    <CameraDirector target={scenePatch?.camera_target || 'overview'} controls={controls} reducedMotion={reducedMotion} />
    <color attach="background" args={['#030509']} />
    <fog attach="fog" args={['#030509', 7, 15]} />
    <ambientLight intensity={.4} />
    <directionalLight position={[4, 6, 6]} intensity={1.6} color="#8be9ff" />
    <Sparkles key={`sparkles-${sparkleCount}`} count={sparkleCount}
      scale={[12, 7, 7]} size={1.2} speed={reducedMotion ? 0 : .25} color="#5de7ff" opacity={.2} />
    <Tumour onSelect={onCloneSelect} overlay={scenePatch?.overlay} reducedMotion={reducedMotion} signal={tumourSignal} />
    <SceneOverlay overlay={scenePatch?.overlay} rank={rank} reducedMotion={reducedMotion}
      hour={simulationHour} frames={simulationFrames} />
    {rank >= 2 && <CandidateGallery rank={rank} selectedId={selectedCandidateId} onSelect={onCandidateSelect}
      reducedMotion={reducedMotion} quarantineActive={quarantineActive} candidates={candidateResults} />}
    {rank >= 3 && <OrganGhost position={[3.1, 1.15, -1.2]} label="LIVER RISK" color="#ff985d" signal={liverSignal} />}
    {rank >= 3 && <OrganGhost position={[3.35, -1.3, -.7]} label="KIDNEY RISK" color="#b85cff" signal={kidneySignal} />}
    <OrbitControls ref={controls} enablePan={false} minDistance={3.8} maxDistance={10}
      enableDamping={!reducedMotion} dampingFactor={.08} />
  </Canvas>
  {contextLost && <SceneFallback reason="The graphics context was interrupted. It will recover automatically when the browser restores it." />}
  </>
}
