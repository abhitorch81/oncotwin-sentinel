import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

const COLORS={mint:0x62f6cb,blue:0x66baf5,amber:0xffc76b,rose:0xff665e,purple:0xb987f5,deep:0x06130f};
const CASES=[
  {id:'feature_quality',position:[-4.25,2.15,0],color:COLORS.rose},
  {id:'cancer_progression',position:[0,3.15,-.15],color:COLORS.mint},
  {id:'model_drift',position:[4.25,2.15,0],color:COLORS.blue},
  {id:'schema_mutation',position:[4.55,-1.4,.1],color:COLORS.amber},
  {id:'biomarker_discordance',position:[2.05,-3.35,0],color:COLORS.purple},
  {id:'protein_conformation',position:[-2.05,-3.35,0],color:COLORS.blue},
  {id:'microenvironment_escape',position:[-4.55,-1.4,.1],color:COLORS.mint},
];

function material(color,emissiveIntensity=.55,opacity=1){return new THREE.MeshStandardMaterial({color,emissive:color,emissiveIntensity,roughness:.32,metalness:.18,transparent:opacity<1,opacity})}
function lineMaterial(color){return new THREE.LineDashedMaterial({color,transparent:true,opacity:.62,dashSize:.16,gapSize:.12})}
function ring(radius,color,tube=.018){return new THREE.Mesh(new THREE.TorusGeometry(radius,tube,8,96),material(color,.8,.72))}

function buildFeatureWorld(group,color,pickMeshes){
  const shell=new THREE.Mesh(new THREE.IcosahedronGeometry(.72,2),material(color,.38,.28));group.add(shell);pickMeshes.push(shell);
  const wire=new THREE.Mesh(new THREE.IcosahedronGeometry(.78,1),new THREE.MeshBasicMaterial({color,wireframe:true,transparent:true,opacity:.7}));group.add(wire);
  for(let i=0;i<11;i++){const s=.08+(i%3)*.025,node=new THREE.Mesh(new THREE.SphereGeometry(s,16,12),material(i<3?COLORS.rose:COLORS.mint,.9));const a=i/11*Math.PI*2;node.position.set(Math.cos(a)*(.42+(i%2)*.18),Math.sin(a)*(.42+(i%2)*.16),(i%3-.8)*.17);group.add(node)}
  group.userData.anim=t=>{wire.rotation.y=t*.45;shell.scale.setScalar(1+Math.sin(t*2.2)*.025)};
}

function buildProgressionWorld(group,color,pickMeshes){
  const nucleus=new THREE.Mesh(new THREE.SphereGeometry(.43,32,24),material(color,.5));group.add(nucleus);pickMeshes.push(nucleus);
  for(let i=0;i<4;i++){const tumor=new THREE.Mesh(new THREE.SphereGeometry(.13+i*.045,24,18),material(i===3?COLORS.rose:color,.8));const a=i*.82;tumor.position.set(-.48+i*.31,Math.sin(a)*.34,(i-1.5)*.1);tumor.userData.base=tumor.scale.clone();group.add(tumor)}
  const helix=new THREE.Group();for(let i=0;i<30;i++){const bead=new THREE.Mesh(new THREE.SphereGeometry(.025,8,6),new THREE.MeshBasicMaterial({color:i%2?COLORS.mint:COLORS.blue}));const a=i*.65;bead.position.set(Math.cos(a)*.56,-.58+i*.04,Math.sin(a)*.16);helix.add(bead)}group.add(helix);
  group.userData.anim=t=>{nucleus.rotation.y=t*.5;helix.rotation.y=-t*.7;group.children.slice(1,5).forEach((m,i)=>m.scale.setScalar(1+Math.sin(t*2+i)*.08))};
}

function buildDriftWorld(group,color,pickMeshes){
  const core=new THREE.Mesh(new THREE.SphereGeometry(.28,24,18),material(color,.72));group.add(core);pickMeshes.push(core);
  for(let i=0;i<5;i++){const r=ring(.38+i*.13,i===4?COLORS.rose:color,.014);r.rotation.x=Math.PI/2+(i%2)*.18;r.userData.speed=.3+i*.13;group.add(r)}
  const arrow=new THREE.Mesh(new THREE.ConeGeometry(.12,.42,18),material(COLORS.rose,.9));arrow.rotation.z=-Math.PI/2;arrow.position.x=.78;group.add(arrow);
  group.userData.anim=t=>{group.children.slice(1,6).forEach((r,i)=>{r.rotation.z=t*r.userData.speed;r.scale.setScalar(1+Math.sin(t*1.7+i)*.035)});arrow.position.x=.72+Math.sin(t*1.8)*.12};
}

function buildSchemaWorld(group,color,pickMeshes){
  const base=new THREE.Mesh(new THREE.CylinderGeometry(.7,.76,.12,32),material(color,.25,.5));base.position.y=-.54;group.add(base);pickMeshes.push(base);
  for(let i=0;i<5;i++){const broken=i===3,col=new THREE.Mesh(new THREE.BoxGeometry(.18,.65+i*.08,.18),material(broken?COLORS.rose:color,broken?.95:.45));col.position.set((i-2)*.25,-.16+(i*.04),broken?.25:0);col.rotation.z=broken?.18:0;group.add(col)}
  const patch=ring(.86,COLORS.mint,.025);patch.rotation.x=Math.PI/2;group.add(patch);
  group.userData.anim=t=>{patch.rotation.z=t*.8;group.children[4].position.z=.2+Math.sin(t*2)*.08};
}

function buildBiomarkerWorld(group,color,pickMeshes){
  const core=new THREE.Mesh(new THREE.OctahedronGeometry(.28,2),material(color,.8,.82));group.add(core);pickMeshes.push(core);
  const modules=[];
  for(let arm=0;arm<3;arm++){
    const module=new THREE.Group(),angle=arm*Math.PI*2/3;module.position.set(Math.cos(angle)*.58,Math.sin(angle)*.58,(arm-1)*.09);
    const moduleColor=[COLORS.blue,COLORS.mint,COLORS.rose][arm];
    const node=new THREE.Mesh(new THREE.SphereGeometry(.14,20,14),material(moduleColor,.9));module.add(node);
    const orbit=ring(.22,moduleColor,.012);orbit.rotation.x=Math.PI/2;module.add(orbit);group.add(module);modules.push(module);
    const points=[new THREE.Vector3(),module.position.clone()];group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points),new THREE.LineBasicMaterial({color:moduleColor,transparent:true,opacity:.65})));
  }
  const discord=ring(.88,COLORS.rose,.018);discord.rotation.x=Math.PI/2;group.add(discord);
  group.userData.anim=t=>{core.rotation.x=t*.55;core.rotation.y=-t*.7;modules.forEach((m,i)=>{m.rotation.z=t*(.55+i*.12);const phase=i===2?Math.sin(t*3.4)*.16:Math.sin(t*2+i)*.04;m.position.z=(i-1)*.09+phase});discord.rotation.z=-t*.48};
}

function buildProteinWorld(group,color,pickMeshes){
  const backbone=new THREE.Group(),beads=[];
  for(let i=0;i<26;i++){
    const u=i/25,a=u*Math.PI*5.6,r=.36+.14*Math.sin(u*Math.PI*3);const bead=new THREE.Mesh(new THREE.SphereGeometry(.055,12,9),material(i%5===0?COLORS.rose:color,.78));bead.position.set(Math.cos(a)*r,(u-.5)*1.15,Math.sin(a)*r*.55);backbone.add(bead);beads.push(bead);
    if(i>0){const prev=beads[i-1].position,mid=prev.clone().add(bead.position).multiplyScalar(.5),len=prev.distanceTo(bead.position),bond=new THREE.Mesh(new THREE.CylinderGeometry(.018,.018,len,7),material(COLORS.mint,.35,.75));bond.position.copy(mid);bond.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),bead.position.clone().sub(prev).normalize());backbone.add(bond)}
  }
  group.add(backbone);pickMeshes.push(beads[12]);const nativeRing=ring(.92,COLORS.mint,.016);nativeRing.rotation.x=Math.PI/2;group.add(nativeRing);const rift=ring(.63,COLORS.rose,.014);rift.rotation.y=Math.PI/2;group.add(rift);
  group.userData.anim=t=>{backbone.rotation.y=t*.42;backbone.rotation.z=Math.sin(t*.7)*.22;beads.forEach((bead,i)=>bead.scale.setScalar(1+(i%5===0?Math.sin(t*3+i)*.18:0)));nativeRing.rotation.z=t*.3;rift.rotation.x=-t*.5};
}

function buildMicroenvironmentWorld(group,color,pickMeshes){
  const tumor=new THREE.Mesh(new THREE.IcosahedronGeometry(.48,3),material(COLORS.rose,.72,.76));group.add(tumor);pickMeshes.push(tumor);const shell=ring(.82,color,.024);shell.rotation.x=Math.PI/2;group.add(shell);
  const immune=[];for(let i=0;i<18;i++){const cell=new THREE.Mesh(new THREE.SphereGeometry(.045+(i%3)*.008,10,8),material(i%4===0?COLORS.amber:color,.7));cell.userData.angle=i/18*Math.PI*2;cell.userData.radius=.72+(i%4)*.09;cell.userData.speed=.28+(i%5)*.035;group.add(cell);immune.push(cell)}
  const breach=new THREE.Mesh(new THREE.TorusGeometry(.45,.035,8,48,Math.PI*.62),material(COLORS.rose,1));breach.rotation.z=-.35;breach.position.x=.58;group.add(breach);
  group.userData.anim=t=>{tumor.rotation.x=t*.24;tumor.rotation.y=t*.35;shell.rotation.z=t*.42;immune.forEach((cell,i)=>{const a=cell.userData.angle+t*cell.userData.speed,r=cell.userData.radius+(i%4===0?Math.max(0,Math.sin(t*.75))*.38:0);cell.position.set(Math.cos(a)*r,Math.sin(a)*r,(i%5-2)*.055)});breach.scale.setScalar(1+Math.sin(t*2.4)*.12)};
}

function makeWorld(spec,pickMeshes){
  const group=new THREE.Group();group.position.set(...spec.position);group.userData.caseId=spec.id;group.userData.basePosition=group.position.clone();
  const halo=ring(1.02,spec.color,.025);halo.rotation.x=Math.PI/2;group.add(halo);group.userData.halo=halo;
  if(spec.id==='feature_quality')buildFeatureWorld(group,spec.color,pickMeshes);
  if(spec.id==='cancer_progression')buildProgressionWorld(group,spec.color,pickMeshes);
  if(spec.id==='model_drift')buildDriftWorld(group,spec.color,pickMeshes);
  if(spec.id==='schema_mutation')buildSchemaWorld(group,spec.color,pickMeshes);
  if(spec.id==='biomarker_discordance')buildBiomarkerWorld(group,spec.color,pickMeshes);
  if(spec.id==='protein_conformation')buildProteinWorld(group,spec.color,pickMeshes);
  if(spec.id==='microenvironment_escape')buildMicroenvironmentWorld(group,spec.color,pickMeshes);
  group.traverse(obj=>{if(obj.isMesh)obj.userData.caseId=spec.id});return group;
}

export function createProofGalaxy(canvas,callbacks={}){
  const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true,powerPreference:'high-performance'});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;
  const scene=new THREE.Scene();scene.fog=new THREE.FogExp2(COLORS.deep,.045);
  const camera=new THREE.PerspectiveCamera(42,1,.1,80);camera.position.set(0,.35,14.5);
  const controls=new OrbitControls(camera,canvas);controls.enableDamping=true;controls.enablePan=false;controls.minDistance=9;controls.maxDistance=19;controls.autoRotate=true;controls.autoRotateSpeed=.35;
  scene.add(new THREE.AmbientLight(0x7bcbb0,1.15));const key=new THREE.PointLight(COLORS.mint,18,20);key.position.set(0,2,6);scene.add(key);const rim=new THREE.PointLight(COLORS.purple,11,18);rim.position.set(-5,-2,3);scene.add(rim);

  const starsGeo=new THREE.BufferGeometry(),stars=[];for(let i=0;i<700;i++){const r=7+Math.random()*11,a=Math.random()*Math.PI*2,b=(Math.random()-.5)*Math.PI;stars.push(Math.cos(a)*Math.cos(b)*r,Math.sin(b)*r,Math.sin(a)*Math.cos(b)*r)}starsGeo.setAttribute('position',new THREE.Float32BufferAttribute(stars,3));scene.add(new THREE.Points(starsGeo,new THREE.PointsMaterial({color:COLORS.mint,size:.025,transparent:true,opacity:.38})));

  const core=new THREE.Group();scene.add(core);const coreSolid=new THREE.Mesh(new THREE.IcosahedronGeometry(1.05,3),material(COLORS.mint,.72,.26));const coreWire=new THREE.Mesh(new THREE.IcosahedronGeometry(1.2,1),new THREE.MeshBasicMaterial({color:COLORS.mint,wireframe:true,transparent:true,opacity:.86}));core.add(coreSolid,coreWire,ring(1.48,COLORS.mint,.018),ring(1.72,COLORS.purple,.012));core.children[2].rotation.x=Math.PI/2;core.children[3].rotation.y=Math.PI/2;
  const pickMeshes=[],worlds=new Map(),beams=[];
  CASES.forEach(spec=>{const world=makeWorld(spec,pickMeshes);worlds.set(spec.id,world);scene.add(world);const curve=new THREE.QuadraticBezierCurve3(new THREE.Vector3(),new THREE.Vector3(spec.position[0]*.48,spec.position[1]*.48,1.2),new THREE.Vector3(...spec.position));const geo=new THREE.BufferGeometry().setFromPoints(curve.getPoints(70)),beam=new THREE.Line(geo,lineMaterial(spec.color));beam.computeLineDistances();beams.push(beam);scene.add(beam)});
  let selected='feature_quality',proofStrength=0;
  function select(caseId,notify=true){selected=caseId;worlds.forEach((world,id)=>{const active=id===caseId;world.userData.halo.material.opacity=active?1:.3;world.scale.setScalar(active?1.16:.88)});if(notify)callbacks.onSelect?.(caseId)}select(selected,false);
  const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();canvas.addEventListener('pointerup',event=>{const rect=canvas.getBoundingClientRect();pointer.set((event.clientX-rect.left)/rect.width*2-1,-(event.clientY-rect.top)/rect.height*2+1);raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObjects(pickMeshes,true)[0];const caseId=hit?.object?.userData?.caseId;if(caseId)select(caseId,true)});
  function resize(){const rect=canvas.getBoundingClientRect();if(!rect.width||!rect.height)return;renderer.setSize(rect.width,rect.height,false);camera.aspect=rect.width/rect.height;camera.updateProjectionMatrix()}
  let frame=0,disposed=false;const clock=new THREE.Clock();function animate(){if(disposed)return;frame=requestAnimationFrame(animate);resize();const t=clock.getElapsedTime();coreWire.rotation.x=t*.2;coreWire.rotation.y=t*.32;core.children[2].rotation.z=t*.24;core.children[3].rotation.z=-t*.18;core.scale.setScalar(1+Math.sin(t*2.3)*(.018+proofStrength*.018));worlds.forEach((world,id)=>{world.position.y=world.userData.basePosition.y+Math.sin(t*1.2+CASES.findIndex(x=>x.id===id))*.08;world.userData.anim?.(t)});beams.forEach((beam,i)=>{beam.material.dashOffset=-t*(.25+proofStrength*.9);beam.material.opacity=.42+proofStrength*.45+(i===CASES.findIndex(x=>x.id===selected)?.18:0)});controls.update();renderer.render(scene,camera)}animate();
  callbacks.onReady?.({version:'THREE.JS PROOF GALAXY',worlds:CASES.length});
  return {select,setEvidence(success,total){proofStrength=total?success/total:0;controls.autoRotateSpeed=.35+proofStrength*.45},focus(){controls.autoRotate=true},dispose(){disposed=true;cancelAnimationFrame(frame);renderer.dispose()}};
}
