// Where the athlete comes from.
//
// Local Studio reads the checked athlete folder that the build served or copied
// (`/athlete-assets/`, vite.config.mjs). Hosted Studio has no such folder: a person signs in, and
// the published version comes through the Studio API, each file checked against the hash the
// version names (review-api.js). In the two modes the manifest is the only description of the
// model that Studio uses.
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { signIn } from './review-gate.js'

export const HOSTED = import.meta.env.VITE_STUDIO_MODE === 'hosted'

const fileOf = (manifest, role) => Object.entries(manifest.files).find(([, f]) => f.role === role)?.[0]

// -> { manifest, library, gltf, versionId, review }. `versionId` and `review` are null in local
// Studio. `onProgress(fraction or null)` reports the model download.
export async function openAthlete(onProgress) {
  return HOSTED ? openHosted(onProgress) : openLocal(onProgress)
}

async function openLocal(onProgress) {
  const response = await fetch('/athlete-assets/athlete-manifest.json')
  if (!response.ok) throw new Error('The model manifest is missing. Rebuild Studio with the athlete output directory.')
  const manifest = await response.json()
  const modelFile = fileOf(manifest, 'model')
  const libraryFile = fileOf(manifest, 'library')
  if (!modelFile) throw new Error('The athlete manifest names no model.')
  const library = await (libraryFile ? fetch('/athlete-assets/' + libraryFile) : Promise.reject())
    .then((r) => (r.ok ? r.json() : { techniques: [] })).catch(() => ({ techniques: [] }))
  const gltf = await new GLTFLoader().loadAsync('/athlete-assets/' + modelFile, (e) => onProgress(e.total ? e.loaded / e.total : null))
  return { manifest, library, gltf, modelFile, versionId: null, review: null }
}

async function openHosted(onProgress) {
  // Nothing of the athlete is asked for before the person is signed in and admitted.
  const review = await signIn()
  const { current } = await review.api.versions()
  if (!current) throw new Error('No athlete version is published yet. Ask Braven to publish one.')
  const manifest = await review.api.manifest(current)
  const modelFile = fileOf(manifest, 'model')
  const libraryFile = fileOf(manifest, 'library')
  if (!modelFile) throw new Error('The athlete manifest names no model.')
  const library = libraryFile
    ? JSON.parse(new TextDecoder().decode(await review.api.file(current, libraryFile, manifest.files[libraryFile].sha256)))
    : { techniques: [] }
  const bytes = await review.api.file(current, modelFile, manifest.files[modelFile].sha256, (loaded, total) => onProgress(total ? loaded / total : null))
  // The checked bytes are parsed. The loader never fetches the model by itself.
  const gltf = await new GLTFLoader().parseAsync(bytes.buffer, '')
  return { manifest, library, gltf, modelFile, versionId: current, review }
}
