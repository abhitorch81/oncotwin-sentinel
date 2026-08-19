import { Float, Line, OrbitControls, Sparkles, Text } from '@react-three/drei'
import { Canvas, useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import * as THREE from 'three'

function Tumour({ onSelect }: { onSelect: () => void }) {
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
    <pointLight color="#ff356d" intensity={5} distance={4} position={[.4, .5, 1]} />
  </group>
}

function NanoPath({ color, offset, rejected = false }: { color: string; offset: number; rejected?: boolean }) {
  const points = useMemo(() => Array.from({ length: 28 }, (_, i) => new THREE.Vector3(-4 + i * .27, offset + Math.sin(i * .65 + offset) * .18, Math.cos(i * .4) * .4)), [offset])
  return <group>
    <Line points={points} color={color} transparent opacity={rejected ? .22 : .62} lineWidth={1.2} />
    {points.filter((_, i) => i % 4 === 0).map((p, i) => <Float key={i} speed={2.5} floatIntensity={.18}>
      <mesh position={p}><sphereGeometry args={[.07, 16, 16]} /><meshStandardMaterial color={color} emissive={color} emissiveIntensity={2} /></mesh>
    </Float>)}
  </group>
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

export function TwinScene({ onCloneSelect, sceneAction }: { onCloneSelect: () => void; sceneAction?: string }) {
  const rank = actionRank[sceneAction || ''] || 0
  return <Canvas camera={{ position: [0, 1.1, 7.2], fov: 44 }} dpr={[1, 1.7]}>
    <color attach="background" args={['#030509']} />
    <fog attach="fog" args={['#030509', 7, 15]} />
    <ambientLight intensity={.4} />
    <directionalLight position={[4, 6, 6]} intensity={1.6} color="#8be9ff" />
    <Sparkles count={120} scale={[12, 7, 7]} size={1.2} speed={.25} color="#5de7ff" opacity={.2} />
    <Tumour onSelect={onCloneSelect} />
    {rank >= 2 && <NanoPath color="#44d7ff" offset={1.3} />}
    {rank >= 2 && <NanoPath color="#ff3f61" offset={.35} rejected />}
    {rank >= 2 && <NanoPath color="#75ffbd" offset={-1.0} />}
    {rank >= 3 && <OrganGhost position={[3.1, 1.15, -1.2]} label="LIVER RISK" color="#ff985d" />}
    {rank >= 3 && <OrganGhost position={[3.35, -1.3, -.7]} label="KIDNEY RISK" color="#b85cff" />}
    <OrbitControls enablePan={false} minDistance={5} maxDistance={10} autoRotate autoRotateSpeed={.18} />
  </Canvas>
}
