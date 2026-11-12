// Athlete versions (specification 4: ACC-1, ACC-3, FBK-1; the 12.6 ruling).
//
// A version is named by the sha256 of the bytes of its athlete-manifest.json
// (docs/ATHLETE_MANIFEST.md). An author uploads a manifest and the files Studio plays; the
// bucket itself checks each file against the hash the manifest gives. The version is a draft
// until a person with the owner role publishes it. A reviewer sees published versions only, and
// a published version never changes.
//
// The bucket has no public address. Each file leaves through this Worker, behind the token.
import { event, json, readBytes, refuse, sha256Hex } from './http.mjs'
import { requireRole } from './people.mjs'

export const MANIFEST_NAME = 'athlete-manifest.json'
const MANIFEST_LIMIT = 1024 * 1024
const SHA256 = /^[0-9a-f]{64}$/
const FILE_NAME = /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/
// What Studio plays. The masters (.blend) are in the manifest and stay out of the bucket.
const SERVED_ROLES = ['model', 'library']
const CONTENT_TYPES = { model: 'model/gltf-binary', library: 'application/json', manifest: 'application/json' }

const key = (id, name) => `versions/${id}/${name}`

// -> { modelSha256, revision, served: { name: { role, bytes, sha256 } } }, or null when the text is
// not a manifest Studio can serve. The full check is athlete_manifest.py; this refuses what
// would make the routes below unsafe or useless.
export function readManifest(text) {
  let manifest
  try { manifest = JSON.parse(text) } catch { return null }
  if (!manifest || manifest.format !== 'braven-athlete-manifest' || manifest.formatVersion !== 1) return null
  if (!manifest.files || typeof manifest.files !== 'object' || Array.isArray(manifest.files)) return null
  const served = {}
  for (const [name, entry] of Object.entries(manifest.files)) {
    if (!FILE_NAME.test(name) || name === MANIFEST_NAME) return null
    if (!entry || typeof entry.role !== 'string' || !SHA256.test(entry.sha256 ?? '')) return null
    if (!Number.isInteger(entry.bytes) || entry.bytes < 1) return null
    if (SERVED_ROLES.includes(entry.role)) served[name] = { role: entry.role, bytes: entry.bytes, sha256: entry.sha256 }
  }
  for (const role of SERVED_ROLES) {
    if (Object.values(served).filter((entry) => entry.role === role).length !== 1) return null
  }
  if (!Array.isArray(manifest.clips) || manifest.clips.length === 0) return null
  for (const clip of manifest.clips) {
    if (!clip || typeof clip.id !== 'string' || clip.id.length === 0 || !(clip.seconds > 0)) return null
  }
  const revision = Number.isInteger(manifest.asset?.revision) ? manifest.asset.revision : null
  const model = Object.values(served).find((entry) => entry.role === 'model')
  return { manifest, served, modelSha256: model.sha256, revision }
}

const shown = (row) => ({
  id: row.id, state: row.state, revision: row.revision, modelSha256: row.model_sha256,
  createdAt: row.created_at, publishedAt: row.published_at,
})

// The version, when this member may see it. A reviewer is told a draft does not exist.
export async function visibleVersion(db, member, id) {
  if (!SHA256.test(id)) return null
  const row = await db.prepare('SELECT * FROM versions WHERE id = ?').bind(id).first()
  if (!row) return null
  if (row.state !== 'published' && member.role === 'reviewer') return null
  return row
}

export async function versionRoutes(request, env, deps, member, method, path) {
  const db = env.DB
  const bucket = env.VERSIONS

  if (path === '/api/versions' && method === 'GET') {
    const all = member.role !== 'reviewer'
    const rows = await db.prepare(`SELECT id, state, revision, model_sha256, created_at, published_at FROM versions
      ${all ? '' : "WHERE state = 'published'"} ORDER BY COALESCE(published_at, created_at) DESC, id`).all()
    const current = await db.prepare("SELECT id FROM versions WHERE state = 'published' ORDER BY published_at DESC, id LIMIT 1").first()
    return json(200, { current: current?.id ?? null, versions: rows.results.map(shown) })
  }

  if (path === '/api/versions' && method === 'PUT') {
    requireRole(member, 'author', 'owner')
    const bytes = await readBytes(request, MANIFEST_LIMIT)
    let text
    try { text = new TextDecoder('utf-8', { fatal: true }).decode(bytes) } catch { refuse(400, 'bad_manifest') }
    const read = readManifest(text)
    if (!read) refuse(400, 'bad_manifest')
    const id = await sha256Hex(bytes)
    const existing = await db.prepare('SELECT * FROM versions WHERE id = ?').bind(id).first()
    if (existing) return json(200, shown(existing))
    await bucket.put(key(id, MANIFEST_NAME), bytes, { sha256: id, httpMetadata: { contentType: CONTENT_TYPES.manifest } })
    const at = deps.now()
    await db.batch([
      db.prepare(`INSERT INTO versions (id, model_sha256, revision, manifest, state, created_by, created_at)
                  VALUES (?, ?, ?, ?, 'draft', ?, ?)`).bind(id, read.modelSha256, read.revision, text, member.uid, at),
      event(db, deps, member.uid, 'version.created', id, { revision: read.revision, modelSha256: read.modelSha256 }),
    ])
    return json(201, shown({ id, state: 'draft', revision: read.revision, model_sha256: read.modelSha256, created_at: at, published_at: null }))
  }

  const publish = /^\/api\/versions\/([^/]+)\/publish$/.exec(path)
  if (publish && method === 'POST') {
    // The owner role, and so a person: no route gives an agent a way to publish (ruling 12.6).
    requireRole(member, 'owner')
    const row = await visibleVersion(db, member, publish[1])
    if (!row) refuse(404, 'no_such_version')
    if (row.state === 'published') refuse(409, 'already_published')
    const { served } = readManifest(row.manifest)
    const missing = []
    for (const name of [MANIFEST_NAME, ...Object.keys(served)]) {
      if (!(await bucket.head(key(row.id, name)))) missing.push(name)
    }
    if (missing.length) refuse(409, 'files_missing', { missing })
    const at = deps.now()
    await db.batch([
      db.prepare("UPDATE versions SET state = 'published', published_by = ?, published_at = ? WHERE id = ? AND state = 'draft'").bind(member.uid, at, row.id),
      event(db, deps, member.uid, 'version.published', row.id, { revision: row.revision }),
    ])
    return json(200, shown({ ...row, state: 'published', published_at: at }))
  }

  const file = /^\/api\/versions\/([^/]+)\/files\/([^/]+)$/.exec(path)
  if (file && (method === 'GET' || method === 'PUT')) {
    if (method === 'PUT') requireRole(member, 'author', 'owner')
    const row = await visibleVersion(db, member, file[1])
    if (!row) refuse(404, 'no_such_version')
    const { served } = readManifest(row.manifest)
    const name = file[2]

    if (method === 'GET') {
      const entry = name === MANIFEST_NAME ? { role: 'manifest', sha256: row.id } : served[name]
      if (!entry) refuse(404, 'no_such_file')
      const object = await bucket.get(key(row.id, name))
      if (!object) refuse(404, 'no_such_file')
      return new Response(object.body, {
        status: 200,
        headers: {
          'content-type': CONTENT_TYPES[entry.role],
          'content-length': String(object.size),
          // The address holds the hash, so the bytes behind it never change. `private`: a shared
          // cache must not hold what only a signed-in person may read.
          'cache-control': 'private, max-age=31536000, immutable',
          etag: `"${entry.sha256}"`,
          'x-content-type-options': 'nosniff',
        },
      })
    }

    const entry = served[name]
    if (!entry) refuse(404, 'no_such_file')
    if (row.state === 'published') refuse(409, 'already_published')
    if (Number(request.headers.get('content-length')) !== entry.bytes) refuse(422, 'wrong_size', { expected: entry.bytes })
    try {
      // The bucket hashes the stream and refuses bytes that do not match. The Worker never
      // holds the model in memory.
      await bucket.put(key(row.id, name), request.body, { sha256: entry.sha256, httpMetadata: { contentType: CONTENT_TYPES[entry.role] } })
    } catch (error) {
      if (/checksum|sha-?256|10037/i.test(String(error?.message))) refuse(422, 'wrong_bytes', { expected: entry.sha256 })
      throw error
    }
    await event(db, deps, member.uid, 'version.file_stored', row.id, { name, sha256: entry.sha256 }).run()
    return json(201, { id: row.id, name, sha256: entry.sha256, bytes: entry.bytes })
  }

  return null
}
