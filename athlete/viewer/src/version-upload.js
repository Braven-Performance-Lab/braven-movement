// Putting an athlete version on the server, from the files a person picked in the browser.
//
// The Studio API and its bucket check each file against the manifest (athlete/studio-api
// versions.mjs). This module finds a mistake before 17 MB go up: no manifest among the files, a
// file the manifest names that is not there, or a file of another size. It sends only what
// Studio plays (the model and the movement library) and leaves the Blender masters on the disk.
//
// It does NOT replace `python athlete/athlete_manifest.py check`: that reads the model, and a
// browser cannot. An author runs the check before the upload.

const MANIFEST_NAME = 'athlete-manifest.json'
const PLAYED_ROLES = ['model', 'library']

// `files` is what a file input gives: objects with name, size and arrayBuffer().
// -> { manifestBytes, revision, files: [{ name, role, file }] }. Throws an Error a person can read.
export async function planUpload(files) {
  const all = Array.from(files ?? [])
  // A folder picker gives the files of every subfolder too, in no promised order. Only the
  // folder's own files count: "folder/file" has two parts, and a plain file has no path. A
  // backup subfolder with an earlier manifest must never go up in the place of the folder's own.
  const list = all.filter((f) => !f.webkitRelativePath || f.webkitRelativePath.split('/').length <= 2)
  const named = (name) => {
    const found = list.filter((f) => f.name === name)
    if (found.length > 1) throw new Error(`${name} is there more than one time. Choose one athlete folder.`)
    return found[0]
  }
  const manifestFile = named(MANIFEST_NAME)
  if (!manifestFile) {
    throw new Error(all.some((f) => f.name === MANIFEST_NAME)
      ? `There is no ${MANIFEST_NAME} in the folder itself, only in a folder inside it. Choose the athlete folder, not a folder above it.`
      : `There is no ${MANIFEST_NAME} among the files. Choose the athlete folder that the manifest check passed.`)
  }
  const manifestBytes = new Uint8Array(await manifestFile.arrayBuffer())
  let manifest = null
  try { manifest = JSON.parse(new TextDecoder().decode(manifestBytes)) } catch { manifest = null }
  if (!manifest || manifest.format !== 'braven-athlete-manifest' || !manifest.files || typeof manifest.files !== 'object') {
    throw new Error(`${MANIFEST_NAME} is not a Braven athlete manifest.`)
  }
  const wanted = Object.entries(manifest.files).filter(([, entry]) => PLAYED_ROLES.includes(entry?.role))
    .sort(([, a], [, b]) => PLAYED_ROLES.indexOf(a.role) - PLAYED_ROLES.indexOf(b.role))
  if (!wanted.some(([, entry]) => entry.role === 'model')) throw new Error('The manifest names no model.')
  const out = []
  for (const [name, entry] of wanted) {
    const file = named(name)
    if (!file) throw new Error(`${name} is not among the files, and the manifest names it.`)
    if (file.size !== entry.bytes) throw new Error(`${name} has ${file.size} bytes, and the manifest says ${entry.bytes}. It is not the file the manifest was written for.`)
    out.push({ name, role: entry.role, file })
  }
  return { manifestBytes, revision: manifest.asset?.revision ?? null, files: out }
}

// Sends the plan. `onStep(text)` reports each step. -> the version the server recorded.
export async function sendUpload(api, plan, onStep = () => {}) {
  onStep('Sending the manifest…')
  const version = await api.createVersion(plan.manifestBytes)
  if (version.state === 'published') throw new Error('This version is published already. A published version does not change.')
  for (const { name, file } of plan.files) {
    onStep(`Sending ${name} (${(file.size / 1048576).toFixed(1)} MB)…`)
    await api.putFile(version.id, name, new Uint8Array(await file.arrayBuffer()))
  }
  return version
}
