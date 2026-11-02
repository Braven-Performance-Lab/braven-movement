import test from 'node:test'
import assert from 'node:assert/strict'
import { makeCatalog } from '../src/catalog.js'
import { PUBLICATION_PROFILE, defaultCamera, publishableClips, publicationSnapshot, PublicationRefusal } from '../src/publication.js'

const P = PUBLICATION_PROFILE
const library = {techniques:[
  {clip:'netball_chest_pass',seconds:1.5833333333333333,sourceChecksPassed:true,coachApproved:false},
  {clip:'netball_bounce_pass',seconds:1.7666666666666666,sourceChecksPassed:true,coachApproved:false},
]}
const clips = [{name:'netball_chest_pass',duration:1.5833333333333333},{name:'netball_bounce_pass',duration:1.7666666666666666},
  {name:'Jump_reach',duration:2},{name:'Jog',duration:1.0333333333333334}]
const catalog = makeCatalog(clips, library, P.glbSha256, P.modelRevision)
const assets = {modelRevision:P.modelRevision,glbSha256:P.glbSha256,librarySha256:P.librarySha256}
const setup = (over={}) => ({modelId:'netball-athlete',assetHash:P.glbSha256,clip:'netball_chest_pass',time:0.7,kit:'shorts',height:1.75,speed:1,loop:true,
  colours:{primary:'#087E76',accent:'#ef775e',shorts:'#202b31'},driver:'clips',gait:'run',carry:false,skeleton:false,wireframe:false,
  camera:defaultCamera('netball_chest_pass'),pose:null,...over})
const snapshot = s => publicationSnapshot(s, {catalog, library, assets})
const refuses = (s, code, setting) => assert.throws(() => snapshot(s), e => e instanceof PublicationRefusal && e.code === code && (setting === undefined || e.setting === setting))

test('the default cameras are the three source framings, with the Jump_reach offset computed as the viewer computes it',()=>{
  assert.deepEqual(defaultCamera('netball_chest_pass'),{position:[2.2,1.8,3.55],target:[0,.93,0]})
  // [5,2.5,6] is 7.07 m from its target; OrbitControls shows it at maxDistance 7.
  // These values were read from the running Studio on revision 8.
  const bounce = defaultCamera('netball_bounce_pass')
  assert.deepEqual(bounce.target,[0,.8,1.3])
  const shown = [4.950737714883371,2.483250823060347,5.953693451990369]
  assert.ok(bounce.position.every((n,i)=>Math.abs(n-shown[i])<1e-9), `bounce camera ${bounce.position}`)
  assert.ok(Math.abs(Math.hypot(...bounce.position.map((n,i)=>n-bounce.target[i]))-7)<1e-12)
  const jump = defaultCamera('Jump_reach')
  assert.deepEqual(jump.target,[0,1.12,0])
  assert.deepEqual(jump.position,[(2.2-0)*1.18+0,(1.8-1.12)*1.18+1.12,(3.55-0)*1.18+0])
  // The bounce-pass framing belongs to the quarter view only.
  assert.deepEqual(defaultCamera('netball_bounce_pass','front'),{position:[0,1.75,4.1],target:[0,.93,0]})
})
test('only clips with a movement-library record are publishable in the first profile',()=>{
  assert.deepEqual(publishableClips(catalog),['netball_chest_pass','netball_bounce_pass'])
  refuses(setup({clip:'Jog',camera:defaultCamera('Jog')}),'clip-not-publishable','clip')
})
test('a default setup becomes a closed snapshot with case-normalised colours and the canonical camera',()=>{
  const s = snapshot(setup())
  assert.deepEqual(s,{kind:'braven-movement-setup-snapshot',schemaVersion:1,profile:P.id,
    model:{modelId:'netball-athlete',modelRevision:P.modelRevision,glbSha256:P.glbSha256,librarySha256:P.librarySha256},
    kit:'shorts',colours:{primary:'#087e76',accent:'#ef775e',shorts:'#202b31'},
    animation:{clipId:'netball_chest_pass',durationSeconds:1.5833333333333333,timeSeconds:0.7,speed:1,loop:true},
    heightMetres:1.75,camera:{position:[2.2,1.8,3.55],target:[0,.93,0]},pose:null})
})
test('Studio saves gait and scenario in every setup; in a clip setup they have no effect and are not published',()=>{
  const s = snapshot(setup({scenario:'gait',gait:'sprint'}))
  assert.deepEqual(s, snapshot(setup()))
  assert.equal(JSON.stringify(s).includes('gait'), false)
})
test('time is strict [0, duration], although the local workspace accepts 0.01 s more',()=>{
  assert.equal(snapshot(setup({time:0})).animation.timeSeconds,0)
  assert.equal(snapshot(setup({time:1.5833333333333333})).animation.timeSeconds,1.5833333333333333)
  refuses(setup({time:1.5833333333333333+.005}),'time-out-of-range','time')
  refuses(setup({time:-0.001}),'invalid-setup')
})
test('every unsupported non-default setting refuses by name and does not strip',()=>{
  refuses(setup({driver:'tactics',time:1}),'unsupported-setting','driver')
  refuses(setup({driver:'tactics',scenario:'receive-pivot',time:1}),'unsupported-setting','driver')
  for (const key of ['carry','skeleton','wireframe']) refuses(setup({[key]:true}),'unsupported-setting',key)
  refuses(setup({height:1.8}),'unsupported-setting','height')
  refuses(setup({camera:{position:[2.2,1.8,3.6],target:[0,.93,0]}}),'unsupported-setting','camera')
  refuses(setup({pose:{Head:{quaternion:[0,0,0,1],position:[0,0,0],scale:[1,1,1]}}}),'unsupported-setting','pose')
})
test('the setup is not changed by a refusal or by a snapshot',()=>{
  const s = setup({height:1.8}); const before = structuredClone(s)
  assert.throws(()=>snapshot(s)); assert.deepEqual(s,before)
  const t = setup(); const kept = structuredClone(t); snapshot(t); assert.deepEqual(t,kept)
})
test('unknown members refuse',()=>{
  refuses(setup({note:'x'}),'unknown-member','note')
  refuses(setup({colours:{primary:'#087e76',accent:'#ef775e',shorts:'#202b31',trim:'#000000'}}),'unknown-member','colours.trim')
})
test('the pinned package must be the loaded package',()=>{
  assert.throws(()=>publicationSnapshot(setup(),{catalog,library,assets:{...assets,librarySha256:'b'.repeat(64)}}),e=>e.code==='asset-mismatch')
  assert.throws(()=>publicationSnapshot(setup(),{catalog,library,assets:{...assets,modelRevision:7}}),e=>e.code==='asset-mismatch')
  const other = makeCatalog(clips, library, 'c'.repeat(64), P.modelRevision)
  assert.throws(()=>publicationSnapshot({...setup(),assetHash:'c'.repeat(64)},{catalog:other,library,assets}),e=>e.code==='asset-mismatch')
})
test('a GLB clip whose duration disagrees with its library record refuses',()=>{
  const drift = makeCatalog([{name:'netball_chest_pass',duration:1.6}], library, P.glbSha256, P.modelRevision)
  assert.throws(()=>publicationSnapshot(setup(),{catalog:drift,library,assets}),e=>e.code==='duration-disagreement')
})
