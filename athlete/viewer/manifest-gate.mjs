import fs from 'node:fs'
import path from 'node:path'
import { createHash } from 'node:crypto'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

// Braven Studio serves an athlete only if its folder matches athlete-manifest.json, and then
// serves nothing but that manifest and the files it lists. The check is the reference validator
// in athlete/athlete_manifest.py, run as a process, so Studio and the host tests refuse the same
// sets with the same codes. Tactics' importer runs a mirror of it (tools/athlete-manifest.mjs).
//
// One check at start-up is not enough: the dev server streams files on every request and a
// build copies them at its end, and an export can rewrite the folder in between. So each file
// is hashed again when it is served or copied, against the manifest that was accepted.
const here = path.dirname(fileURLToPath(import.meta.url))
const VALIDATOR = path.resolve(here, '..', 'athlete_manifest.py')
export const STUDIO_FAMILY = 'braven-athlete-v6'
export const MANIFEST_NAME = 'athlete-manifest.json'
const TYPES = { '.glb': 'model/gltf-binary', '.blend': 'application/octet-stream', '.json': 'application/json' }
const sha256 = data => createHash('sha256').update(data).digest('hex')

export function checkAthlete(folder, { python = process.env.BRAVEN_PYTHON || 'python' } = {}) {
  const run = spawnSync(python, ['-B', VALIDATOR, 'check', folder, '--family', STUDIO_FAMILY], { encoding: 'utf8' })
  if (run.error) throw new Error(`Studio could not run the athlete manifest check: ${run.error.message}`)
  if (run.status !== 0) {
    const reason = (run.stderr || '').trim().split('\n').pop() || `exit ${run.status}`
    throw new Error(`Studio refuses the athlete in ${folder}. ${reason}`)
  }
  return JSON.parse(run.stdout.trim().split('\n').pop())
}

/**
 * Check the folder, then name exactly what Studio may serve: the manifest itself and each file
 * it lists, each with the hash it must still have. Nothing else in the folder is served.
 */
export function acceptAthlete(folder, options) {
  return acceptChecked(folder, checkAthlete(folder, options))
}

/** acceptAthlete after the check: `summary` is what athlete_manifest.py check printed. */
export function acceptChecked(folder, summary) {
  const manifestBytes = fs.readFileSync(path.join(folder, MANIFEST_NAME))
  // The file read here must be the one the validator checked, not one rewritten in between.
  if (sha256(manifestBytes) !== summary.manifestSha256)
    throw new Error(`${MANIFEST_NAME} changed after the check; start Studio again`)
  const manifest = JSON.parse(manifestBytes.toString('utf8'))
  const entries = new Map([[MANIFEST_NAME, { sha256: sha256(manifestBytes), type: TYPES['.json'] }]])
  for (const [name, entry] of Object.entries(manifest.files))
    entries.set(name, { sha256: entry.sha256.toLowerCase(), type: TYPES[path.extname(name)] ?? 'application/octet-stream', role: entry.role })
  const model = [...entries.values()].find(e => e.role === 'model')
  if (!model || model.sha256 !== summary.model.toLowerCase()) throw new Error('Studio read a different model hash than the check accepted')
  return { folder, entries, modelSha256: model.sha256, revision: manifest.asset.revision }
}

/** The bytes of one accepted file, or an error if it is not accepted or has changed since. */
export function readAccepted(accepted, name) {
  const entry = accepted.entries.get(name)
  if (!entry) throw new Error(`${name} is not a file this athlete's manifest lists`)
  const data = fs.readFileSync(path.join(accepted.folder, name))
  if (sha256(data) !== entry.sha256) throw new Error(`${name} changed after Studio checked the athlete; restart Studio`)
  return data
}

/**
 * Copy every accepted file into a build. The folder is checked again first, and the manifest
 * must be the one accepted at start-up, so a build never packages a folder that changed.
 */
export function copyAccepted(accepted, destination, options) {
  const again = acceptAthlete(accepted.folder, options)
  if (again.entries.get(MANIFEST_NAME).sha256 !== accepted.entries.get(MANIFEST_NAME).sha256)
    throw new Error('The athlete manifest changed during the build; build again')
  // An earlier build may have left files this manifest does not list, such as the legacy manifest.json.
  fs.rmSync(destination, { recursive: true, force: true })
  fs.mkdirSync(destination, { recursive: true })
  for (const name of accepted.entries.keys()) {
    // A listed path may have folders (the validator allows clips/x.json); make them.
    fs.mkdirSync(path.dirname(path.join(destination, name)), { recursive: true })
    fs.writeFileSync(path.join(destination, name), readAccepted(accepted, name))
    if (sha256(fs.readFileSync(path.join(destination, name))) !== accepted.entries.get(name).sha256)
      throw new Error(`${name} did not copy as checked`)
  }
}
