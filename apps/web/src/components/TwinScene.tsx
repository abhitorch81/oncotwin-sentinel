import { Float, Line, OrbitControls, Sparkles, Text } from '@react-three/drei'
import { Canvas, useFrame } from '@react-three/fiber'
import { useEffect, useMemo, useRef } from 'react'
import type { RefObject } from 'react'
import * as THREE from 'three'
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib'
import type { CandidateId, ScenePatch } from '../types'

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

function CameraDirector({ target = 'overview', controls }: {
  target?: ScenePatch['camera_target'] | 'overview'
  controls: RefObject<OrbitControlsImpl | null>
}) {
  const focus = useRef(new THREE.Vector3(...cameraShots.overview.focus))
  const moving = useRef(true)
  const reducedMotion = useMemo(() => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches, [])
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

function CloneSignalOverlay() {
  const ring = useRef<THREE.Mesh>(null)
  useFrame(({ clock }) => {
    if (!ring.current) return
    const pulse = 1 + Math.sin(clock.elapsedTime * 3.2) * .1
    ring.current.scale.setScalar(pulse)
    ring.current.rotation.z = clock.elapsedTime * .35
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

function Tumour({ onSelect, overlay }: { onSelect: () => void; overlay?: ScenePatch['overlay'] }) {
  const group = useRef<THREE.Group>(null)
  const cells = useMemo(() => Array.from({ length: 34 }, (_, i) => ({
    p: [Math.sin(i * 4.1) * (1.0 + (i % 5) * .08), Math.cos(i * 2.3) * .78, Math.sin(i * 1.7) * .72] as [number, number, number],
    s: .19 + (i % 4) * .035,
  })), [])
  useFrame((_, delta) => { if (group.current) group.current.rotation.y += delta * .055 })
  return <group ref={group} onClick={(e) => { e.stopPropagation(); onSelect() }}>
    {cells.map((cell, i) => <mesh key={i} position={cell.p} scale={cell.s}>
      <icosahedronGeometry args={[1, 2]} />
      <meshPhysicalMaterial color={i === 7 ? '#ff315e' : '#7134a8'} emissive={i === 7 ? '#b60035' : '#180926'} emissiveIntensity={i === 7 ? 2.4 : .7} roughness={.25} transmission={.18} />
    </mesh>)}
    {overlay === 'clone_signal' && <CloneSignalOverlay />}
    <pointLight color="#ff356d" intensity={5} distance={4} position={[.4, .5, 1]} />
  </group>
}

function CandidateForgeOverlay() {
  const slots = [
    { id: 'A', color: '#44d7ff', position: [-2.25, 1.25, -.35] as [number, number, number] },
    { id: 'B', color: '#ff3f61', position: [0, 1.35, -.45] as [number, number, number] },
    { id: 'C', color: '#75ffbd', position: [2.25, 1.25, -.35] as [number, number, number] },
  ]
  return <group>
    {slots.map((slot, index) => <Float key={slot.id} speed={1.4 + index * .15} floatIntensity={.12} position={slot.position}>
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

function CandidateBody({ id, docked, selected, quarantined, preferred, onSelect }: {
  id: CandidateId
  docked: boolean
  selected: boolean
  quarantined: boolean
  preferred: boolean
  onSelect: (id: CandidateId) => void
}) {
  const group = useRef<THREE.Group>(null)
  const selection = useRef<THREE.Mesh>(null)
  const visual = candidateVisuals[id]
  const targetPosition = useMemo(() => new THREE.Vector3(...(docked ? visual.dockPosition : visual.forgePosition)), [docked, visual])
  const targetScale = (docked ? .62 : 1) * (selected ? 1.13 : 1)
  const targetScaleVector = useMemo(() => new THREE.Vector3(targetScale, targetScale, targetScale), [targetScale])
  useEffect(() => () => { document.body.style.cursor = 'default' }, [])
  useFrame(({ clock }, delta) => {
    if (!group.current) return
    const alpha = 1 - Math.exp(-4 * Math.min(delta, .1))
    group.current.position.lerp(targetPosition, alpha)
    group.current.scale.lerp(targetScaleVector, alpha)
    group.current.rotation.y += delta * (id === 'B' ? .42 : .28)
    if (selection.current) {
      selection.current.rotation.z = clock.elapsedTime * .55
      selection.current.scale.setScalar(1 + Math.sin(clock.elapsedTime * 3) * .04)
    }
  })
  return <group ref={group} position={visual.forgePosition}
    onClick={event => { event.stopPropagation(); onSelect(id) }}
    onPointerOver={event => { event.stopPropagation(); document.body.style.cursor = 'pointer' }}
    onPointerOut={() => { document.body.style.cursor = 'default' }}>
    <mesh scale={visual.radius}>
      {id === 'A' ? <sphereGeometry args={[1, 28, 22]} /> : id === 'B' ? <dodecahedronGeometry args={[1, 1]} /> : <icosahedronGeometry args={[1, 2]} />}
      <meshPhysicalMaterial color={visual.color} emissive={visual.color} emissiveIntensity={selected ? 1.25 : .55}
        metalness={id === 'B' ? .2 : .05} roughness={id === 'A' ? .18 : .3} transmission={id === 'A' ? .24 : .08} />
    </mesh>
    <CandidateSurface id={id} color={visual.color} radius={visual.radius} />
    {(selected || quarantined || preferred) && <mesh ref={selection} rotation={[Math.PI / 2, 0, 0]}>
      <torusGeometry args={[visual.radius * 1.62, .025, 10, 72]} />
      <meshBasicMaterial color={quarantined ? '#ff315e' : preferred ? '#75ffbd' : '#f3fbff'} transparent opacity={.88} />
    </mesh>}
    <Text position={[0, -visual.radius * 1.65, 0]} fontSize={docked ? .13 : .16} color={visual.color} anchorX="center">{id} · {visual.name}</Text>
    {(quarantined || preferred) && <Text position={[0, visual.radius * 1.65, 0]} fontSize={.1}
      color={quarantined ? '#ff6682' : '#75ffbd'} anchorX="center">{quarantined ? 'QUARANTINED' : 'PREFERRED'}</Text>}
  </group>
}

function CandidateGallery({ rank, selectedId, onSelect }: {
  rank: number
  selectedId?: CandidateId | null
  onSelect: (id: CandidateId) => void
}) {
  return <group>{(['A', 'B', 'C'] as CandidateId[]).map(id =>
    <CandidateBody key={id} id={id} docked={rank >= 3} selected={selectedId === id}
      quarantined={rank >= 4 && id === 'B'} preferred={rank >= 4 && id === 'C'} onSelect={onSelect} />)}</group>
}

function NanoPath({ id, color, destination, speed, opacity = .7 }: {
  id: 'A' | 'B' | 'C'
  color: string
  destination: [number, number, number]
  speed: number
  opacity?: number
}) {
  const particles = useRef<THREE.Group>(null)
  const reducedMotion = useMemo(() => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches, [])
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
    if (!particles.current || reducedMotion) return
    particles.current.children.forEach((particle, index) => {
      const progress = (clock.elapsedTime * speed + index / particleCount) % 1
      particle.position.copy(curve.getPointAt(progress))
    })
  })
  return <group>
    <Line points={linePoints} color={color} transparent opacity={opacity * .55} lineWidth={id === 'C' ? 1.8 : 1.1} />
    <group ref={particles}>{Array.from({ length: particleCount }, (_, index) =>
      <mesh key={index} position={curve.getPointAt(index / particleCount)}>
        <sphereGeometry args={[id === 'B' ? .075 : .06, 12, 12]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={2.2} transparent opacity={opacity} />
      </mesh>)}</group>
    <Text position={destination} fontSize={.11} color={color} anchorX="center">{id}</Text>
  </group>
}

function DistributionOverlay() {
  return <group>
    <NanoPath id="A" color="#44d7ff" destination={[.35, .18, .15]} speed={.1} opacity={.72} />
    <NanoPath id="B" color="#ff3f61" destination={[3.1, 1.15, -1.2]} speed={.16} opacity={.78} />
    <NanoPath id="C" color="#75ffbd" destination={[-.1, -.18, .12]} speed={.13} opacity={.95} />
  </group>
}

function QuarantineOverlay() {
  const cage = useRef<THREE.Group>(null)
  useFrame(({ clock }) => {
    if (!cage.current) return
    cage.current.rotation.y = clock.elapsedTime * .38
    const pulse = 1 + Math.sin(clock.elapsedTime * 4) * .035
    cage.current.scale.setScalar(pulse)
  })
  return <group position={[3.1, 1.15, -1.2]}>
    <group ref={cage}>
      <mesh><boxGeometry args={[1.35, 1.75, 1.15]} /><meshBasicMaterial color="#ff315e" wireframe transparent opacity={.46} /></mesh>
      <mesh rotation={[Math.PI / 4, 0, Math.PI / 4]}><torusGeometry args={[.9, .025, 10, 64]} /><meshBasicMaterial color="#ff5879" transparent opacity={.8} /></mesh>
    </group>
    <pointLight color="#ff315e" intensity={3} distance={3} />
    <Text position={[0, 1.15, 0]} fontSize={.14} color="#ff6b87" anchorX="center">B · QUARANTINED</Text>
    <Text position={[0, -.98, 0]} fontSize={.09} color="#9e6674" anchorX="center">LIVER CEILING BREACHED</Text>
  </group>
}

function ApprovalBoundaryOverlay() {
  const membrane = useRef<THREE.Group>(null)
  useFrame((_, delta) => { if (membrane.current) membrane.current.rotation.y += delta * .045 })
  return <group ref={membrane}>
    <mesh scale={[3.25, 2.15, 1.35]}><sphereGeometry args={[1, 32, 20]} /><meshBasicMaterial color="#ffb35d" wireframe transparent opacity={.09} /></mesh>
    <mesh rotation={[Math.PI / 2, 0, 0]}><torusGeometry args={[2.7, .025, 10, 96]} /><meshBasicMaterial color="#ffb35d" transparent opacity={.5} /></mesh>
    <mesh rotation={[Math.PI / 2, 0, Math.PI / 2]}><torusGeometry args={[2.15, .018, 10, 96]} /><meshBasicMaterial color="#75ffbd" transparent opacity={.32} /></mesh>
    <Text position={[0, 2.25, 0]} fontSize={.16} color="#ffc47d" anchorX="center">HUMAN AUTHORITY BOUNDARY</Text>
  </group>
}

function SceneOverlay({ overlay, rank }: { overlay?: ScenePatch['overlay']; rank: number }) {
  return <>
    {overlay === 'candidate_blueprints' && <CandidateForgeOverlay />}
    {rank >= 3 && <DistributionOverlay />}
    {overlay === 'safety_quarantine' && <QuarantineOverlay />}
    {overlay === 'approval_membrane' && <ApprovalBoundaryOverlay />}
  </>
}

function OrganGhost({ position, label, color }: { position: [number, number, number]; label: string; color: string }) {
  return <group position={position}>
    <mesh scale={[.55, .78, .32]}><sphereGeometry args={[1, 32, 32]} /><meshPhysicalMaterial color={color} transparent opacity={.12} wireframe /></mesh>
    <Text position={[0, -.95, 0]} fontSize={.16} color="#758092" anchorX="center">{label}</Text>
  </group>
}

const actionRank: Record<string, number> = {
  focus_clone: 1, spawn_candidates: 2, run_particle_paths: 3,
  reject_candidate: 4, show_approval_membrane: 5,
}

export function TwinScene({ onCloneSelect, onCandidateSelect, selectedCandidateId, sceneAction, scenePatch }: {
  onCloneSelect: () => void
  onCandidateSelect: (id: CandidateId) => void
  selectedCandidateId?: CandidateId | null
  sceneAction?: string
  scenePatch?: ScenePatch
}) {
  const rank = actionRank[sceneAction || ''] || 0
  const controls = useRef<OrbitControlsImpl>(null)
  return <Canvas camera={{ position: [0, 1.1, 7.2], fov: 44 }} dpr={[1, 1.7]}>
    <CameraDirector target={scenePatch?.camera_target || 'overview'} controls={controls} />
    <color attach="background" args={['#030509']} />
    <fog attach="fog" args={['#030509', 7, 15]} />
    <ambientLight intensity={.4} />
    <directionalLight position={[4, 6, 6]} intensity={1.6} color="#8be9ff" />
    <Sparkles count={120} scale={[12, 7, 7]} size={1.2} speed={.25} color="#5de7ff" opacity={.2} />
    <Tumour onSelect={onCloneSelect} overlay={scenePatch?.overlay} />
    <SceneOverlay overlay={scenePatch?.overlay} rank={rank} />
    {rank >= 2 && <CandidateGallery rank={rank} selectedId={selectedCandidateId} onSelect={onCandidateSelect} />}
    {rank >= 3 && <OrganGhost position={[3.1, 1.15, -1.2]} label="LIVER RISK" color="#ff985d" />}
    {rank >= 3 && <OrganGhost position={[3.35, -1.3, -.7]} label="KIDNEY RISK" color="#b85cff" />}
    <OrbitControls ref={controls} enablePan={false} minDistance={3.8} maxDistance={10} enableDamping dampingFactor={.08} />
  </Canvas>
}
