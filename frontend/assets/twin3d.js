import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const ROSE = new THREE.Color('#ff665e');
const MINT = new THREE.Color('#62f6cb');
const AMBER = new THREE.Color('#ffc76b');
const BLUE = new THREE.Color('#66baf5');

function seededRandom(seed = 17) {
  let value = seed >>> 0;
  return () => {
    value = (value * 1664525 + 1013904223) >>> 0;
    return value / 4294967296;
  };
}

function tube(points, radius, material, segments = 48) {
  const curve = new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(...p)));
  return new THREE.Mesh(new THREE.TubeGeometry(curve, segments, radius, 10, false), material);
}

const tissueTextureCache = new Map();
function tissueTextures(base = '#d65f50') {
  if (tissueTextureCache.has(base)) return tissueTextureCache.get(base);
  const size=384, color=new THREE.Color(base), rand=seededRandom(parseInt(base.slice(1),16)^0x9e3779b9);
  const diffuse=document.createElement('canvas'); diffuse.width=diffuse.height=size;
  const x=diffuse.getContext('2d'), image=x.createImageData(size,size);
  const r0=Math.round(color.r*255),g0=Math.round(color.g*255),b0=Math.round(color.b*255);
  for(let i=0;i<image.data.length;i+=4){
    const grain=(rand()-.5)*25, blush=rand()<.045?18:0;
    image.data[i]=Math.max(0,Math.min(255,r0+grain+blush));
    image.data[i+1]=Math.max(0,Math.min(255,g0+grain*.42));
    image.data[i+2]=Math.max(0,Math.min(255,b0+grain*.25)); image.data[i+3]=255;
  }
  x.putImageData(image,0,0);
  // Sub-dermal capillary network. On a UV sphere these become fine organic
  // surface cues rather than the large decorative tubes used for major vessels.
  x.globalAlpha=.17; x.lineCap='round';
  for(let i=0;i<58;i++){
    const sx=rand()*size, sy=rand()*size, len=32+rand()*95;
    x.strokeStyle=i%5===0?'#7b2730':'#a43d3d'; x.lineWidth=.45+rand()*1.25;
    x.beginPath();x.moveTo(sx,sy);x.bezierCurveTo(sx+(rand()-.5)*len,sy+(rand()-.5)*len,sx+(rand()-.5)*len,sy+(rand()-.5)*len,sx+(rand()-.5)*len,sy+(rand()-.5)*len);x.stroke();
  }
  const bump=document.createElement('canvas'); bump.width=bump.height=192; const bx=bump.getContext('2d'), bi=bx.createImageData(192,192);
  for(let i=0;i<bi.data.length;i+=4){const v=116+Math.floor(rand()*38);bi.data[i]=bi.data[i+1]=bi.data[i+2]=v;bi.data[i+3]=255} bx.putImageData(bi,0,0);
  const map=new THREE.CanvasTexture(diffuse); map.colorSpace=THREE.SRGBColorSpace; map.wrapS=map.wrapT=THREE.RepeatWrapping; map.repeat.set(1.35,1.65);
  const bumpMap=new THREE.CanvasTexture(bump); bumpMap.wrapS=bumpMap.wrapT=THREE.RepeatWrapping; bumpMap.repeat.set(3.5,4.2);
  const result={map,bumpMap}; tissueTextureCache.set(base,result); return result;
}

function tissueMaterial(color = '#d65f50') {
  const tex=tissueTextures(color);
  return new THREE.MeshPhysicalMaterial({
    color:'#fff4ef', map:tex.map, bumpMap:tex.bumpMap, bumpScale:.027,
    roughness: .48,
    metalness: 0,
    clearcoat: .30,
    clearcoatRoughness: .60,
    sheen: .24,
    sheenColor: new THREE.Color('#ffd1bc')
  });
}

function organicTumorGeometry(seed = 1) {
  const geo = new THREE.SphereGeometry(1, 64, 48);
  const pos = geo.attributes.position;
  const phase = seed * 1.731;
  for (let i=0;i<pos.count;i++) {
    let x=pos.getX(i), y=pos.getY(i), z=pos.getZ(i);
    const v=new THREE.Vector3(x,y,z).normalize();
    // Layered low-frequency deformation keeps the focus organic while avoiding
    // the faceted/noisy look of random per-vertex displacement.
    const bulge=1
      +.075*Math.sin(v.x*4.8+v.y*2.7+phase)
      +.045*Math.sin(v.y*6.2-v.z*3.4+phase*.71)
      +.028*Math.sin((v.x+v.z)*8.1-phase*.43);
    x*=bulge*(1+.035*Math.sin(phase));
    y*=bulge*(.94+.035*Math.cos(phase*.8));
    z*=bulge*.76;
    pos.setXYZ(i,x,y,z);
  }
  geo.computeVertexNormals();
  return geo;
}

function makeStudioEnvironment(renderer) {
  const studio=new THREE.Scene();
  studio.background=new THREE.Color('#101a16');
  const panelGeo=new THREE.PlaneGeometry(5.5,5.5);
  const addPanel=(color,intensity,position,rotation)=>{
    const c=new THREE.Color(color).multiplyScalar(intensity);
    const panel=new THREE.Mesh(panelGeo,new THREE.MeshBasicMaterial({color:c,side:THREE.DoubleSide}));
    panel.position.fromArray(position); panel.rotation.set(...rotation); studio.add(panel);
  };
  addPanel('#fff1df',1.8,[-3.8,3.3,2.5],[0,.72,-.30]);
  addPanel('#ffd2bc',1.15,[4.0,.8,2.0],[0,-.95,.15]);
  addPanel('#72cbb9',.78,[-3.4,.1,-2.7],[0,.58,.08]);
  const floor=new THREE.Mesh(new THREE.PlaneGeometry(12,12),new THREE.MeshBasicMaterial({color:'#24312b',side:THREE.DoubleSide}));
  floor.rotation.x=-Math.PI/2; floor.position.y=-3.4; studio.add(floor);
  const pmrem=new THREE.PMREMGenerator(renderer);
  const target=pmrem.fromScene(studio,.055); pmrem.dispose();
  panelGeo.dispose(); floor.geometry.dispose();
  studio.traverse(o=>{if(o.material)o.material.dispose()});
  return target;
}

function lungGeometry(phase = 0) {
  const geo = new THREE.SphereGeometry(1, 72, 56);
  const pos = geo.attributes.position;
  for (let i=0;i<pos.count;i++) {
    let x=pos.getX(i), y=pos.getY(i), z=pos.getZ(i);
    // Broad hilar middle, tapered apex/base and a small deterministic surface
    // undulation: enough to catch studio light without reading as procedural noise.
    const taper=.80+.20*Math.pow(Math.max(0,1-y*y),.55);
    const ripple=1+.018*Math.sin(x*15+y*8+phase)+.010*Math.sin(z*23-y*11+phase*.7);
    x*=taper*ripple; z*=ripple; y*=1+.008*Math.sin(x*17+phase);
    pos.setXYZ(i,x,y,z);
  }
  geo.computeVertexNormals();
  return geo;
}

function addLungVessels(group) {
  const artery = new THREE.MeshStandardMaterial({color: '#9d433f', roughness: .53});
  const vein = new THREE.MeshStandardMaterial({color: '#c9675e', roughness: .5});
  const paths = [
    [[-.48,.95,.64],[-.76,.48,.75],[-.88,-.10,.68],[-.68,-.68,.58]],
    [[-.53,.70,.66],[-.30,.25,.78],[-.45,-.30,.74],[-.22,-.83,.57]],
    [[.46,.94,.65],[.78,.55,.75],[.90,.03,.66],[.70,-.64,.57]],
    [[.54,.66,.70],[.31,.28,.80],[.48,-.24,.73],[.28,-.86,.56]],
    [[-.22,.48,.75],[-.52,.22,.79],[-.75,.04,.73]],
    [[.20,.42,.77],[.50,.17,.81],[.76,-.05,.69]],
    [[-.36,-.26,.74],[-.64,-.43,.69],[-.78,-.67,.55]],
    [[.37,-.24,.75],[.61,-.41,.69],[.75,-.70,.53]],
    [[-.34,.72,.69],[-.57,.60,.73],[-.77,.43,.64]],
    [[-.44,.32,.74],[-.66,.20,.73],[-.82,.02,.62]],
    [[-.31,-.04,.78],[-.55,-.18,.75],[-.73,-.37,.63]],
    [[.34,.74,.69],[.57,.61,.74],[.79,.41,.62]],
    [[.42,.34,.75],[.65,.19,.73],[.84,-.02,.60]],
    [[.29,-.02,.79],[.53,-.17,.75],[.73,-.37,.62]]
  ];
  paths.forEach((p, i) => group.add(tube(p, i < 4 ? .018 : .011, i % 3 === 0 ? vein : artery, 38)));
}

function createLungs() {
  const group = new THREE.Group();
  group.userData.kind = 'lung';
  const tissues = [];
  const layers = new THREE.Group();
  const leftMat = tissueMaterial('#df6c59');
  const rightMat = tissueMaterial('#dc6656');
  const left = new THREE.Mesh(lungGeometry(.3), leftMat);
  left.scale.set(.78, 1.22, .61); left.position.set(-.49, -.05, 0); left.rotation.z = -.09;
  const right = new THREE.Mesh(lungGeometry(1.7), rightMat);
  right.scale.set(.84, 1.29, .64); right.position.set(.50, -.02, -.01); right.rotation.z = .07;
  group.add(left, right); tissues.push(leftMat, rightMat);

  // Pleural fissures make the silhouette read as a real multi-lobed lung.
  const fissureMat = new THREE.MeshStandardMaterial({color:'#8e3d36', roughness:.58});
  group.add(tube([[-.98,.04,.40],[-.70,-.08,.61],[-.42,-.18,.66],[-.20,-.34,.49]], .018, fissureMat));
  group.add(tube([[.12,.26,.49],[.40,.10,.66],[.68,-.02,.62],[1.00,-.20,.36]], .018, fissureMat));
  group.add(tube([[.18,-.34,.44],[.47,-.44,.64],[.74,-.51,.55],[.94,-.67,.31]], .014, fissureMat));

  // Trachea and cartilage rings.
  const airwayMat = new THREE.MeshPhysicalMaterial({color:'#e8a390',roughness:.52,clearcoat:.16});
  const trachea = new THREE.Mesh(new THREE.CylinderGeometry(.14,.18,.82,32), airwayMat);
  trachea.position.set(0,1.53,-.02); group.add(trachea);
  for (let i=0;i<7;i++) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(.155 + i*.002,.018,8,32), new THREE.MeshStandardMaterial({color:'#a8564b',roughness:.6}));
    ring.rotation.x = Math.PI/2; ring.position.set(0,1.20+i*.11,-.02); group.add(ring);
  }
  group.add(tube([[0,1.18,0],[-.08,1.01,.03],[-.40,.78,.08]], .095, airwayMat));
  group.add(tube([[0,1.18,0],[.10,1.01,.03],[.43,.78,.08]], .095, airwayMat));
  addLungVessels(layers);
  group.add(layers);
  group.userData.tissues = tissues;
  group.userData.layers = layers;
  group.userData.specimen = 'Pulmones';
  return group;
}

function deformHeartGeometry() {
  const geo = new THREE.SphereGeometry(1, 84, 64);
  const pos = geo.attributes.position;
  for (let i=0;i<pos.count;i++) {
    let x=pos.getX(i), y=pos.getY(i), z=pos.getZ(i);
    const yn=(y+1)/2;
    const taper=.31+.78*Math.pow(yn,.61);
    const ripple=1+.013*Math.sin(x*19+y*13)+.008*Math.sin(z*27-y*9);
    x *= .94*taper*ripple;
    z *= .74*(.60+.46*yn);
    y = y*1.18-.20;
    if (y > .43) x += Math.sign(x || 1) * .085 * ((y-.43)/.60);
    // A shallow anterior interventricular groove catches rim light and makes
    // the lower heart read as two muscular ventricles, not one stretched sphere.
    if(z>.25 && Math.abs(x)<.12) z-=.055*(1-Math.abs(x)/.12)*(1-Math.min(1,Math.abs(y+.15)));
    pos.setXYZ(i,x,y,z);
  }
  geo.computeVertexNormals();
  return geo;
}

function createHeart() {
  const group = new THREE.Group();
  group.userData.kind = 'heart';
  const layers = new THREE.Group();
  const heartMat = tissueMaterial('#c94f46');
  const body = new THREE.Mesh(deformHeartGeometry(), heartMat);
  body.rotation.z = -.13; body.position.y = -.10; group.add(body);

  // Distinct atrial masses break the procedural teardrop silhouette and give
  // the great vessels a believable muscular origin.
  const atrialGeo=new THREE.SphereGeometry(1,52,36);
  const leftAtrium=new THREE.Mesh(atrialGeo,heartMat); leftAtrium.scale.set(.34,.30,.38); leftAtrium.position.set(-.38,.61,-.02); leftAtrium.rotation.z=-.22;
  const rightAtrium=new THREE.Mesh(atrialGeo,heartMat); rightAtrium.scale.set(.38,.34,.40); rightAtrium.position.set(.36,.57,-.04); rightAtrium.rotation.z=.18;
  group.add(leftAtrium,rightAtrium);

  const red = new THREE.MeshPhysicalMaterial({color:'#b64038',roughness:.42,clearcoat:.25});
  const blue = new THREE.MeshPhysicalMaterial({color:'#416f91',roughness:.46,clearcoat:.18});
  group.add(tube([[-.05,.72,-.05],[-.03,1.25,.00],[-.23,1.56,.02]],.105,blue));
  group.add(tube([[.18,.72,.02],[.27,1.28,.02],[.23,1.63,.02]],.105,red));
  group.add(tube([[.25,1.20,.00],[.58,1.36,-.02],[.72,1.18,.02]],.07,red));
  group.add(tube([[-.17,1.18,-.03],[-.43,1.37,-.05],[-.52,1.14,-.02]],.065,blue));

  // Coronary vessels on the anterior surface.
  const coronaryRed = new THREE.MeshStandardMaterial({color:'#8f302e',roughness:.48});
  const coronaryBlue = new THREE.MeshStandardMaterial({color:'#476c81',roughness:.48});
  const paths=[
    [[.20,.85,.54],[.28,.35,.63],[.18,-.20,.58],[.04,-.82,.36]],
    [[.12,.72,.56],[-.18,.45,.61],[-.42,.06,.51],[-.46,-.38,.35]],
    [[.30,.50,.55],[.55,.27,.49],[.61,-.08,.34]],
    [[-.14,.39,.59],[-.34,.18,.56],[-.55,-.04,.39]],
    [[.13,.03,.59],[.35,-.20,.55],[.45,-.48,.37]],
    [[-.04,.78,.60],[-.02,.38,.66],[-.08,-.10,.61],[-.13,-.64,.42]],
    [[-.03,.59,.64],[.20,.51,.62],[.43,.39,.54]],
    [[-.08,.56,.63],[-.28,.48,.61],[-.49,.31,.50]],
    [[.06,-.10,.60],[.25,-.32,.53],[.31,-.62,.38]],
    [[-.10,-.06,.60],[-.26,-.28,.51],[-.30,-.54,.36]]
  ];
  paths.forEach((p,i)=>layers.add(tube(p,i<2?.020:i===5?.017:.010,i%3===1?coronaryBlue:coronaryRed,44)));
  group.add(layers);
  group.userData.tissues=[heartMat]; group.userData.layers=layers; group.userData.specimen='Cor';
  return group;
}

function createPedestal() {
  const g=new THREE.Group();
  const side=new THREE.MeshPhysicalMaterial({color:'#d8c5b6',roughness:.72,clearcoat:.06});
  const top=new THREE.MeshPhysicalMaterial({color:'#ecded2',roughness:.68,clearcoat:.05});
  const base=new THREE.Mesh(new THREE.CylinderGeometry(1.62,1.76,.35,72),side); base.position.y=-1.56; base.receiveShadow=true;
  const cap=new THREE.Mesh(new THREE.CylinderGeometry(1.62,1.62,.07,72),top); cap.position.y=-1.36; cap.receiveShadow=true;
  g.add(base,cap); return g;
}

function makeCells(config, rand) {
  const palette=config.cell_types.map(x=>new THREE.Color(x.color));
  const positions=[], colors=[];
  for(let i=0;i<980;i++){
    const side=rand()>.5?1:-1; let x,y,z;
    do{x=rand()*2-1;y=rand()*2-1;z=rand()*2-1}while(x*x+y*y+z*z>1);
    positions.push(side*.48+x*.63,y*1.04-.05,z*.48);
    const q=rand(), idx=q<.38?0:q<.63?1:q<.85?2:3, c=palette[idx]||MINT;
    colors.push(c.r,c.g,c.b);
  }
  const geo=new THREE.BufferGeometry();
  geo.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  geo.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
  return new THREE.Points(geo,new THREE.PointsMaterial({size:.038,vertexColors:true,transparent:true,opacity:.82,blending:THREE.AdditiveBlending,depthWrite:false}));
}

export function createTwin3D(canvas, config, callbacks={}) {
  const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true,powerPreference:'high-performance'});
  renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.toneMapping=THREE.ACESFilmicToneMapping; renderer.toneMappingExposure=1.08;
  renderer.shadowMap.enabled=true; renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  const gl=renderer.getContext();
  const webglVersion=String(gl.getParameter(gl.VERSION)).replace(/\s*\([^)]*\)/g,'');
  const onContextLost=e=>{e.preventDefault();callbacks.onError?.('WebGL context lost. Reload or enable hardware acceleration.')};
  canvas.addEventListener('webglcontextlost',onContextLost,false);

  const scene=new THREE.Scene(); scene.fog=new THREE.FogExp2('#06110d',.055);
  const studioEnvironment=makeStudioEnvironment(renderer); scene.environment=studioEnvironment.texture; scene.environmentIntensity=.92;
  const camera=new THREE.PerspectiveCamera(36,1,.05,30); camera.position.set(0,.12,5.65);
  const controls=new OrbitControls(camera,canvas); controls.enableDamping=true; controls.dampingFactor=.06; controls.enablePan=false; controls.minDistance=3.0; controls.maxDistance=7; controls.autoRotate=true; controls.autoRotateSpeed=.38; controls.target.set(0,.05,0);

  scene.add(new THREE.HemisphereLight('#fff5e6','#07110d',1.18));
  const key=new THREE.DirectionalLight('#fff0df',3.65); key.position.set(-3.1,3.7,4.8); key.castShadow=true; key.shadow.mapSize.set(2048,2048); key.shadow.bias=-.00035; scene.add(key);
  const fill=new THREE.PointLight('#ff9a7d',15,8,2); fill.position.set(2.7,1.4,3.4); scene.add(fill);
  const rim=new THREE.PointLight('#5ed7c2',10,8,2); rim.position.set(-2.8,.4,-3.2); scene.add(rim);

  const rand=seededRandom(713);
  const dustPos=[]; for(let i=0;i<150;i++)dustPos.push((rand()-.5)*8,(rand()-.5)*5,(rand()-.5)*6);
  const dustGeo=new THREE.BufferGeometry(); dustGeo.setAttribute('position',new THREE.Float32BufferAttribute(dustPos,3));
  const dust=new THREE.Points(dustGeo,new THREE.PointsMaterial({color:'#346355',size:.012,transparent:true,opacity:.26})); scene.add(dust);

  const world=new THREE.Group(); scene.add(world);
  const pedestal=createPedestal(); world.add(pedestal);
  const lung=createLungs(), heart=createHeart(); world.add(lung,heart); heart.visible=false;
  lung.traverse(o=>{if(o.isMesh)o.castShadow=true}); heart.traverse(o=>{if(o.isMesh)o.castShadow=true});
  const specimens={lung,heart};
  const anatomyLayer=new THREE.Group(); world.add(anatomyLayer);
  const anatomyModels=new Map(), anatomyLoads=new Map();
  const gltfLoader=new GLTFLoader();
  const anatomyFiles={lung:'/assets/models/anatomy/lung.glb',heart:'/assets/models/anatomy/heart.glb',liver:'/assets/models/anatomy/liver.glb',kidney:'/assets/models/anatomy/kidney.glb'};
  const anatomyNames={lung:'Pulmones',heart:'Cor',liver:'Hepar',kidney:'Ren'};
  const kindForCohort={LUAD:'lung',LIHC:'liver',KIRC:'kidney',PAAD:'heart',COAD:'heart',SKCM:'heart',GBM:'heart'};

  function normalizeAnatomy(root,kind){
    root.updateMatrixWorld(true);
    const box=new THREE.Box3().setFromObject(root), center=new THREE.Vector3(), size=new THREE.Vector3(); box.getCenter(center);box.getSize(size);
    root.position.sub(center);
    const maxDim=Math.max(size.x,size.y,size.z)||1, wrap=new THREE.Group(); wrap.add(root); wrap.scale.setScalar(2.72/maxDim); wrap.position.y=-.03;
    if(kind==='lung')wrap.rotation.y=-.08;
    if(kind==='heart')wrap.rotation.z=-.06;
    if(kind==='liver')wrap.rotation.set(.04,-.20,-.06);
    if(kind==='kidney')wrap.rotation.set(.02,.26,-.10);
    wrap.updateWorldMatrix(true,true);
    const meshStats=[];
    wrap.traverse(o=>{if(!o.isMesh)return;o.castShadow=true;o.receiveShadow=true;const mats=Array.isArray(o.material)?o.material:[o.material];mats.forEach(m=>{if(!m)return;if('roughness'in m)m.roughness=Math.max(.39,Math.min(.68,m.roughness??.52));if('metalness'in m)m.metalness=0;if('envMapIntensity'in m)m.envMapIntensity=.88;m.needsUpdate=true});
      if(!o.geometry.boundingBox)o.geometry.computeBoundingBox();
      const dims=new THREE.Vector3(); o.geometry.boundingBox?.getSize(dims);
      const worldScale=new THREE.Vector3(); o.getWorldScale(worldScale); dims.multiply(worldScale).set(Math.abs(dims.x),Math.abs(dims.y),Math.abs(dims.z));
      const maxAxis=Math.max(dims.x,dims.y,dims.z)||1, minAxis=Math.min(dims.x,dims.y,dims.z);
      meshStats.push({mesh:o,volume:dims.x*dims.y*dims.z,thickness:minAxis/maxAxis});
    });
    // The anatomical GLBs often contain long vessel/airway meshes around the
    // organ. Lesions should attach to dominant tissue volumes, never whichever
    // auxiliary mesh happens to be closest to the camera ray.
    const maxVolume=Math.max(...meshStats.map(x=>x.volume),0);
    let tissueMeshes=meshStats.filter(x=>x.volume>=maxVolume*.055&&x.thickness>=.13).map(x=>x.mesh);
    if(!tissueMeshes.length&&meshStats.length)tissueMeshes=[meshStats.sort((a,b)=>b.volume-a.volume)[0].mesh];
    wrap.userData.tissueMeshes=tissueMeshes;
    wrap.visible=false; return wrap;
  }
  function loadAnatomy(kind){
    if(anatomyModels.has(kind))return Promise.resolve(anatomyModels.get(kind));
    if(anatomyLoads.has(kind))return anatomyLoads.get(kind);
    const promise=new Promise(resolve=>gltfLoader.load(anatomyFiles[kind],gltf=>{const model=normalizeAnatomy(gltf.scene,kind);anatomyLayer.add(model);anatomyModels.set(kind,model);anatomyLoads.delete(kind);resolve(model);if(kind===currentKind&&!compare)activateSpecimen(kind)},undefined,error=>{console.warn(`High-detail ${kind} model unavailable; procedural fallback remains active.`,error);anatomyLoads.delete(kind);resolve(null)}));
    anatomyLoads.set(kind,promise);return promise;
  }
  const cells=makeCells(config,rand); cells.visible=false; world.add(cells);

  const lesionGroup=new THREE.Group(); world.add(lesionGroup);
  const lesions=[];
  const tumorTex=tissueTextures('#c64b42');
  const lesionPositions={
    lung:[[-.30,.46,.63],[.64,.22,.60],[.55,-.60,.55],[-.72,-.68,.48],[.78,.78,.42]],
    heart:[[.28,.38,.57],[.50,.08,.49],[-.31,.08,.52],[.24,-.59,.39],[-.48,-.43,.33]]
  };
  const lesionData=[...config.lesions];
  while(lesionData.length<5)lesionData.push({id:`L${lesionData.length+1}`,label:'Advanced focus',appears_at:4,risk:.96});
  lesionData.forEach((data,idx)=>{
    const g=new THREE.Group();
    const mesh=new THREE.Mesh(organicTumorGeometry(idx+1),new THREE.MeshPhysicalMaterial({color:idx===0?'#fff0e7':'#f6d1c8',map:tumorTex.map,bumpMap:tumorTex.bumpMap,bumpScale:.042,emissive:'#4a0d0b',emissiveIntensity:.10,roughness:.42,clearcoat:.32,clearcoatRoughness:.48,sheen:.22,sheenColor:new THREE.Color('#ff9f8c')}));
    mesh.castShadow=true; mesh.receiveShadow=true;
    mesh.userData.lesion=data;
    const ring=new THREE.Mesh(new THREE.TorusGeometry(1.10,.065,12,56),new THREE.MeshBasicMaterial({color:'#fffaf2',transparent:true,opacity:.84,depthTest:true}));
    // The group is oriented to the organ surface normal after ray projection.
    // Keep only the inspection ring proud of the tissue; the tumour body itself
    // is intentionally sunk into the mesh.
    ring.position.z=.76; g.add(mesh,ring); g.visible=false; lesionGroup.add(g);
    lesions.push({data,group:g,mesh,ring,base:.065+data.risk*.042});
  });

  let kind='lung', currentKind='lung', stageIndex=3, layersVisible=false, crossSection=false, compare=false, isolated=false, disposed=false, hovered=null, cue='idle', cueUntil=0;
  const raycaster=new THREE.Raycaster(), pointer=new THREE.Vector2();
  const surfaceZ=new THREE.Vector3(0,0,1);
  const surfaceAnchors={
    lung:[[-.42,-.08],[.42,-.06],[.42,-.62],[-.42,-.64],[.48,-.34]],
    heart:[[-.28,.28],[.27,.32],[.30,-.22],[-.25,-.28],[.02,-.04]],
    liver:[[-.45,.20],[.36,.18],[.38,-.25],[-.38,-.22],[.02,-.04]],
    // This asset includes renal artery/vein + ureter on its right side. Keep
    // progression foci on the parenchyma instead of the hilar plumbing.
    kidney:[[-.43,.28],[-.30,.02],[-.38,-.27],[-.16,.43],[-.18,-.42]]
  };

  function snapLesionsToSurface(model,modelKind){
    model.updateWorldMatrix(true,true);
    const anchors=surfaceAnchors[modelKind]||surfaceAnchors.heart;
    const tissueMeshes=model.userData.tissueMeshes?.length?model.userData.tissueMeshes:[];
    lesions.forEach((item,i)=>{
      const [baseX,baseY]=anchors[i%anchors.length]; let hit=null;
      // The HD assets have irregular outlines. Try tiny neighbouring offsets if
      // an anchor lands in a fissure or airway gap instead of tissue.
      const attempts=[[0,0],[-.08,0],[.08,0],[0,-.08],[0,.08],[-.08,-.08],[.08,-.08]];
      for(const [dx,dy] of attempts){
        raycaster.set(new THREE.Vector3(baseX+dx,baseY+dy,4),new THREE.Vector3(0,0,-1));
        hit=(tissueMeshes.length?raycaster.intersectObjects(tissueMeshes,false):raycaster.intersectObject(model,true)).find(x=>x.object?.isMesh)||null;
        if(hit)break;
      }
      if(!hit)return;
      const normal=hit.face?.normal?.clone().transformDirection(hit.object.matrixWorld).normalize()||new THREE.Vector3(0,0,1);
      // Keep the normal facing the camera side used for placement.
      if(normal.z<0)normal.negate();
      const embed=Math.max(.050,item.group.scale.x*.60);
      item.group.position.copy(hit.point).addScaledVector(normal,-embed);
      item.group.quaternion.setFromUnitVectors(surfaceZ,normal);
      item.group.userData.surfaceAttached=true;
    });
  }

  function activateSpecimen(nextKind){
    currentKind=nextKind;
    anatomyModels.forEach((model,k)=>model.visible=k===nextKind&&!compare);
    const hd=anatomyModels.get(nextKind);
    lung.visible=!hd&&!compare&&nextKind==='lung';
    heart.visible=!hd&&!compare&&nextKind!=='lung';
    if(hd){lung.visible=false;heart.visible=false}
    if(hd)snapLesionsToSurface(hd,nextKind);
    const specimenName=anatomyNames[nextKind]||'Context specimen';
    callbacks.onSpecimen?.(`${specimenName}${hd?' · HD':' · loading HD'}`,nextKind);
    setTissueMode();
  }

  function positionLesions(){
    const positionKind=kind==='lung'?'lung':'heart'; lesions.forEach((item,i)=>item.group.position.fromArray(lesionPositions[positionKind][i]));
  }
  function setTissueMode(){
    Object.values(specimens).forEach(s=>s.userData.tissues.forEach(m=>{m.transparent=crossSection;m.opacity=crossSection?.30:1;m.depthWrite=!crossSection}));
    anatomyModels.forEach(model=>model.traverse(o=>{if(!o.isMesh)return;const mats=Array.isArray(o.material)?o.material:[o.material];mats.forEach(m=>{m.transparent=crossSection;m.opacity=crossSection?.30:1;m.depthWrite=!crossSection;m.needsUpdate=true})}));
    cells.visible=layersVisible||crossSection;
  }
  function setCohort(code='LUAD'){
    kind=kindForCohort[code]||'heart';
    positionLesions();
    if(!compare){lung.position.x=0;heart.position.x=0;lung.scale.setScalar(1);heart.scale.setScalar(1);activateSpecimen(kind)}
    loadAnatomy(kind);
    cells.visible=(layersVisible||crossSection)&&kind==='lung';
    setStage(stageIndex,'cohort');
    const hd=anatomyModels.get(kind); if(hd)snapLesionsToSurface(hd,kind);
  }
  function focusAnatomy(nextKind='lung'){
    if(!['lung','heart','liver','kidney'].includes(nextKind))return false;
    kind=nextKind; compare=false; loadAnatomy(kind); activateSpecimen(kind); resetCamera(); return true;
  }
  function setStage(index,source='ui'){
    stageIndex=Math.max(0,Math.min(config.stages.length-1,Number(index)||0));
    const stage=config.stages[stageIndex];
    lesions.forEach((item,i)=>{
      item.group.visible=item.data.appears_at<=stageIndex;
      const age=Math.max(0,stageIndex-item.data.appears_at);
      item.group.scale.setScalar(item.base*(1+stage.burden*.82+age*.16));
      item.ring.scale.setScalar(.84+Math.sin((i+1)*1.7)*.06);
    });
    callbacks.onStage?.(stage,source);
  }
  function pulse(nextCue='context-pulse'){
    cue=nextCue; cueUntil=performance.now()+1600;
    if(cue==='risk-focus'){
      const target=lesions.filter(x=>x.group.visible).sort((a,b)=>b.data.risk-a.data.risk)[0];
      if(target)callbacks.onSelect?.(target.data);
    }
  }
  function resetCamera(){camera.position.set(0,.12,5.65);controls.target.set(0,.05,0);controls.autoRotate=true;controls.update()}
  function command(name){
    if(name==='rotate'){controls.autoRotate=!controls.autoRotate;return {active:controls.autoRotate}}
    if(name==='zoom'){camera.position.setLength(camera.position.length()>4.25?3.75:5.65);controls.update();return {active:camera.position.length()<4.25}}
    if(name==='isolate'){isolated=!isolated;pedestal.visible=!isolated;dust.visible=!isolated;return {active:isolated}}
    if(name==='cross-section'){crossSection=!crossSection;setTissueMode();return {active:crossSection}}
    if(name==='layers'){layersVisible=!layersVisible;setTissueMode();return {active:layersVisible}}
    if(name==='compare'){
      compare=!compare;
      anatomyModels.forEach(model=>model.visible=false);
      if(compare){lung.visible=heart.visible=true;lung.scale.setScalar(.68);heart.scale.setScalar(.68);lung.position.x=-.85;heart.position.x=.85}
      else activateSpecimen(kind);
      return {active:compare};
    }
    if(name==='reset'){compare=false;crossSection=false;layersVisible=false;isolated=false;pedestal.visible=dust.visible=true;setTissueMode();activateSpecimen(kind);resetCamera();return {active:false}}
    return {active:false};
  }

  function pick(event,select=false){
    const rect=canvas.getBoundingClientRect(); pointer.x=((event.clientX-rect.left)/rect.width)*2-1; pointer.y=-((event.clientY-rect.top)/rect.height)*2+1;
    raycaster.setFromCamera(pointer,camera); const hit=raycaster.intersectObjects(lesions.filter(x=>x.group.visible).map(x=>x.mesh),false)[0];
    hovered=hit?.object||null; canvas.style.cursor=hovered?'pointer':'grab'; if(hovered&&select)callbacks.onSelect?.(hovered.userData.lesion);
  }
  canvas.addEventListener('pointermove',e=>pick(e,false)); canvas.addEventListener('click',e=>pick(e,true));

  function resize(){const r=canvas.getBoundingClientRect(),w=Math.max(1,r.width),h=Math.max(1,r.height);renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}
  const observer=new ResizeObserver(resize); observer.observe(canvas); resize();
  const clock=new THREE.Clock();
  function frame(now=performance.now()){
    if(disposed)return; const dt=Math.min(clock.getDelta(),.04), t=clock.elapsedTime; controls.update(dt);
    lesions.forEach((item,i)=>{if(!item.group.visible)return;const beat=1+Math.sin(t*(1.7+item.data.risk*.55)+i)*.014;item.mesh.scale.setScalar(beat*(hovered===item.mesh?1.10:1));item.ring.material.opacity=.70+.14*Math.sin(t*1.7+i)});
    if(now<cueUntil&&(cue==='catalog-scan'||cue==='lineage-pulse'))fill.intensity=15+Math.sin(t*7)*3;else fill.intensity+=(15-fill.intensity)*.08;
    dust.rotation.y+=.00025; renderer.render(scene,camera);
  }

  positionLesions(); setTissueMode(); setStage(3,'boot'); loadAnatomy('lung'); renderer.setAnimationLoop(frame); callbacks.onSpecimen?.('Pulmones · loading HD','lung'); callbacks.onReady?.({version:webglVersion});
  return {setStage,setCohort,focusAnatomy,pulse,command,resetCamera,getState(){return{kind,stageIndex,layersVisible,crossSection,compare,isolated,autoRotate:controls.autoRotate}},destroy(){disposed=true;renderer.setAnimationLoop(null);observer.disconnect();controls.dispose();canvas.removeEventListener('webglcontextlost',onContextLost);studioEnvironment.dispose();renderer.dispose()}};
}
