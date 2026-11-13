import * as THREE from 'three'

// The WebGL renderer's settings, in one place so that tests/three-version.test.mjs can read
// what the page uses. The viewer keeps WebGLRenderer, not WebGPURenderer, for phones.
export const RENDERER_SETTINGS = Object.freeze({
  contextAttributes: Object.freeze({ antialias: true, preserveDrawingBuffer: true }),
  maxPixelRatio: 2,
  // r182 made PCFShadowMap soft and deprecated PCFSoftShadowMap with WebGLRenderer.
  shadowMapType: THREE.PCFShadowMap,
  toneMapping: THREE.ACESFilmicToneMapping,
  toneMappingExposure: 1.0,
})

export function createRenderer() {
  const s = RENDERER_SETTINGS
  const renderer = new THREE.WebGLRenderer({ ...s.contextAttributes })
  renderer.setPixelRatio(Math.min(devicePixelRatio, s.maxPixelRatio))
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = s.shadowMapType
  renderer.toneMapping = s.toneMapping
  renderer.toneMappingExposure = s.toneMappingExposure
  return renderer
}
