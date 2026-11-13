# Upgrading the Studio viewer from three.js 0.169 to r187

Main's goal (13 November 2026): upgrade before the first hosted deploy, and
keep the WebGL renderer for phones. This file is step 1: what the viewer
uses, and which of it changed between 0.169 and r187.

## What the viewer uses

Read on `main` at `5b105b3`. `package.json` pins `three` at `0.169.0`, and
Vite is `8.3.0`. Four source files import three.js:

- `src/main.js` and `src/preview-motion.js` import `three`.
- `src/main.js` imports `OrbitControls` and `RoomEnvironment` from the addons.
- `src/athlete-source.js` imports `GLTFLoader` from the addons. It calls
  `loadAsync` and `parseAsync` only.

The viewer also runs Tactics engine code on its own three.js:
`vite.config.mjs` aliases `@tactics` to the Tactics checkout and sets
`dedupe: ['three']`. `src/main.js` imports `skinned.ts`, `athleteMotion.ts`
and `athleteFootwork.ts`, and `skinned.ts` imports `figure.ts`. These four
use `GLTFLoader` and `SkeletonUtils` from `three/examples/jsm`, and `Bone`,
`SkinnedMesh`, `KeyframeTrack`, `Interpolant`, `PropertyBinding`,
`AnimationClip`, `BufferGeometry` and its attributes, `MeshStandardMaterial`,
`CatmullRomCurve3`, `Matrix4`, `Quaternion` and `Vector3`. The first version
of this survey missed them. None of these names is in the migration guide
from r170 to r187, and they set no `Material.type`, no `matrixAutoUpdate`
and no shadow map type. Their `MeshStandardMaterial` takes the light change
below.

The core names the viewer uses: `WebGLRenderer`, `Scene`, `PerspectiveCamera`,
`PMREMGenerator`, `MeshStandardMaterial`, `MeshBasicMaterial`, `Mesh`, `Group`,
`PlaneGeometry`, `RingGeometry`, `DirectionalLight`, `HemisphereLight`, `Fog`,
`Color`, `SkeletonHelper`, `AnimationMixer`, `AnimationClip`, `Vector3`,
`Quaternion`, `Euler`, `Box3`, `MathUtils`, `PCFSoftShadowMap`,
`ACESFilmicToneMapping`, `LoopOnce` and `DoubleSide`.

The renderer settings (`src/main.js:24-39`): antialias, a preserved drawing
buffer, a pixel ratio of at most 2, soft shadows, ACES filmic tone mapping at
exposure 1.0, and an environment from `PMREMGenerator.fromScene` of a
`RoomEnvironment`.

## What changed, from the three.js migration guide

The source is the migration guide of the three.js wiki, read on 13 November
2026, for every release from r170 to r187.

### One change needs code

- **r182: `PCFSoftShadowMap` is deprecated with `WebGLRenderer`.** Use
  `PCFShadowMap`, which is now soft too. The viewer sets it at
  `src/main.js:27`.

### Four changes alter the picture, with no code change

The viewer lights the athlete with a PMREM of `RoomEnvironment` on
`MeshStandardMaterial`. Each of these changes moves that light:

- **r181:** indirect specular light on PBR materials is computed differently,
  and rough materials (roughness above 0.5) look a little brighter. The ground
  has roughness 1.
- **r181:** PMREM reflections are improved.
- **r183:** the scene position of `RoomEnvironment` changed, so its PMREM
  light changes.
- **r187:** PMREMs are built on cube render targets, and materials may look
  slightly different.

No test reads the light. So a person must compare the athlete before and
after, on the same clip and camera. The owner reviews on a desktop.

### Checked, and no effect on the viewer

- r170: mipmaps follow `generateMipmaps` only. The viewer sets no filter.
- r175: `AnimationClip.parseAnimation()` is deprecated. The viewer does not
  call it. `Controls.connect()` needs a DOM element: `OrbitControls` already
  gets `renderer.domElement`.
- r176: `GLTFLoader` no longer detects WebP and AVIF. The athlete GLB has no
  WebP, AVIF, Draco or Meshopt data (no such name is in `athlete/`).
- r183: `Clock` is deprecated. The viewer does not use it.
- r184: the environment rotation now matches object rotation. The viewer sets
  no rotation on the environment or the background.
- r185: `updateWorldMatrix()` honours `matrixWorldNeedsUpdate` when
  `matrixAutoUpdate` is false. The viewer never sets `matrixAutoUpdate`.
- r186: `Object3D` has a `dispose()` method. The viewer calls `dispose()` only
  on `RoomEnvironment` and `PMREMGenerator`, which are three.js classes.
- r187: `setViewport()` and `setScissor()` no longer scale by the pixel ratio
  when a render target is bound. The viewer does not call them. The
  `setViewport` calls in `tests/` are Puppeteer page sizes.
- The animation classes (`AnimationMixer`, `AnimationClip`, `clipAction`,
  `setLoop`, `clampWhenFinished`, `setTime`) and `OrbitControls` have no
  entry in the guide from r170 to r187.

## The plan for steps 2 to 5

1. Write the tests first: a test that refuses `PCFSoftShadowMap`, and a test
   that reads the three.js version the build uses.
2. Set `three` to `0.187.0`, change the shadow map type, and keep
   `WebGLRenderer`.
3. Run the four node test files and the browser tests, and play all 18 clips.
4. Make the same screenshots before and after for the person who looks.
5. Pass the review, land, and rebuild the local Studio on port 5397 from
   `main`.
