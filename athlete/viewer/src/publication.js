import { validateSetup } from './workspace.js'

// The first native publication profile (BRV-0026). A snapshot is a closed document
// derived from a local setup; the local workspace keeps its wider playback tolerances.
export const PUBLICATION_PROFILE = Object.freeze({
  id:'braven-movement-native-clips-v1',
  modelId:'netball-athlete',
  modelRevision:8,
  glbSha256:'55c611f1a525c1ec873dfe2aa01970f806c1090c9081973ac14ca1148847a412',
  librarySha256:'b807503ad5c7e58217ab1fb988f72be5c181360689dd811928ea7abdab4fac51',
  heightMetres:1.75,
  // Measured on revision 8: all twelve library clips agree with the GLB exactly.
  durationToleranceSeconds:1e-4,
  cameraToleranceMetres:1e-9,
})

export class PublicationRefusal extends Error {
  constructor(code,message,setting) { super(message); this.name='PublicationRefusal'; this.code=code; this.setting=setting }
}
const refuse=(code,message,setting)=>{throw new PublicationRefusal(code,message,setting)}

const VIEWS={front:[0,1.75,4.1],side:[4.1,1.75,0],back:[0,1.75,-4.1],quarter:[2.2,1.8,3.55]}
// main.js gives these limits to OrbitControls, which moves the camera inside them.
export const CAMERA_DISTANCE=Object.freeze({min:1.2,max:7})
// The producer default camera: the camera the viewer shows after OrbitControls has
// applied its distance limits. main.js frames every view through this function,
// so the fixture and the viewer cannot disagree.
export function defaultCamera(clip,view='quarter') {
  let position=[...VIEWS[view]],target=[0,.93,0]
  if(clip==='Jump_reach') {
    target=[0,1.12,0]
    position=position.map((p,i)=>(p-target[i])*1.18+target[i])
  }
  // This framing is 7.07 m from its target, so the viewer shows it at 7 m.
  if(clip==='netball_bounce_pass'&&view==='quarter') {position=[5,2.5,6];target=[0,.8,1.3]}
  const offset=position.map((p,i)=>p-target[i]),distance=Math.hypot(...offset)
  const limited=Math.min(Math.max(distance,CAMERA_DISTANCE.min),CAMERA_DISTANCE.max)
  if(limited!==distance) position=offset.map((o,i)=>target[i]+o*limited/distance)
  return {position,target}
}

// Clips without a movement-library record (Defence, Jog, Jump_reach, Ready, Receive_pass)
// have nothing to check GLB agreement against, so the first profile does not publish them.
export const publishableClips=catalog=>catalog.animations.filter(a=>a.source==='Braven Movement').map(a=>a.id)

const SETUP_MEMBERS=['modelId','assetHash','clip','time','kit','height','speed','loop','driver','gait','scenario','carry','skeleton','wireframe','colours','camera','pose']
const near=(a,b,tolerance)=>a.length===b.length&&a.every((n,i)=>Math.abs(n-b[i])<=tolerance)

export function publicationSnapshot(setup,{catalog,library,assets}) {
  const P=PUBLICATION_PROFILE
  for(const key of Object.keys(setup??{})) if(!SETUP_MEMBERS.includes(key)) refuse('unknown-member',`Unknown setup member: ${key}.`,key)
  for(const key of Object.keys(setup?.colours??{})) if(!['primary','accent','shorts'].includes(key)) refuse('unknown-member',`Unknown kit colour: ${key}.`,`colours.${key}`)
  if(assets?.modelRevision!==P.modelRevision||assets?.glbSha256!==P.glbSha256||assets?.librarySha256!==P.librarySha256||catalog.assetHash!==P.glbSha256)
    refuse('asset-mismatch','The loaded model package is not the package this profile pins.')
  let valid
  try { valid=validateSetup(setup,catalog) } catch(error) { refuse('invalid-setup',error.message) }
  // gait and scenario drive only the Tactics preview. Studio saves them in every setup,
  // so in a clip setup they have no effect and the snapshot does not carry them.
  if(valid.driver!=='clips') refuse('unsupported-setting','Only a clip setup can be published. A Tactics preview stays local.','driver')
  for(const key of ['carry','skeleton','wireframe']) if(valid[key]) refuse('unsupported-setting',`Turn off ${key} to publish.`,key)
  if(valid.pose!==null) refuse('unsupported-setting','A saved pose cannot be published in this profile.','pose')
  if(Math.abs(valid.height-P.heightMetres)>1e-9) refuse('unsupported-setting',`Only the reference height ${P.heightMetres} m can be published.`,'height')
  if(!publishableClips(catalog).includes(valid.clip)) refuse('clip-not-publishable','This animation has no Braven Movement record, so it cannot be published.','clip')
  const clip=catalog.animations.find(a=>a.id===valid.clip)
  const record=library.techniques.find(t=>t.clip===valid.clip)
  if(!record||!(Math.abs(clip.duration-record.seconds)<=P.durationToleranceSeconds))
    refuse('duration-disagreement','The model clip and its Braven Movement record have different durations.','clip')
  if(!(valid.time>=0&&valid.time<=clip.duration)) refuse('time-out-of-range',`The time must be between 0 and ${clip.duration} s.`,'time')
  const camera=defaultCamera(valid.clip)
  if(!near(valid.camera.position,camera.position,P.cameraToleranceMetres)||!near(valid.camera.target,camera.target,P.cameraToleranceMetres))
    refuse('unsupported-setting','Only the default three-quarter camera can be published. Select the three-quarter view.','camera')
  return {kind:'braven-movement-setup-snapshot',schemaVersion:1,profile:P.id,
    model:{modelId:P.modelId,modelRevision:P.modelRevision,glbSha256:P.glbSha256,librarySha256:P.librarySha256},
    kit:valid.kit,colours:Object.fromEntries(['primary','accent','shorts'].map(k=>[k,valid.colours[k].toLowerCase()])),
    animation:{clipId:valid.clip,durationSeconds:clip.duration,timeSeconds:valid.time,speed:valid.speed,loop:valid.loop},
    heightMetres:P.heightMetres,camera,pose:null}
}
