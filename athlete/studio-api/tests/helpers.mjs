// What the Studio API tests stand on: a real SQLite behind the D1 interface, a token issuer
// with its own key, and a bucket that checks a sha256 the way R2 does.
//
// The migration FILE is executed, so the schema under test is the schema D1 gets. A fake that
// answers whatever the test handed it cannot tell a wrong query from a right one.
import { DatabaseSync } from 'node:sqlite'
import { createHash, webcrypto } from 'node:crypto'
import { readFileSync, readdirSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { KeyStore } from '../src/firebase.mjs'
import { handle } from '../src/worker.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const MIGRATIONS = path.join(here, '..', 'migrations')
export const PROJECT = 'studio-test-project'

export const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex')

export function testDb() {
  const sqlite = new DatabaseSync(':memory:')
  sqlite.exec('PRAGMA foreign_keys = ON')
  for (const name of readdirSync(MIGRATIONS).filter((n) => n.endsWith('.sql')).sort()) {
    sqlite.exec(readFileSync(path.join(MIGRATIONS, name), 'utf8'))
  }
  const prepare = (sql) => {
    let bindings = []
    const stmt = {
      sql,
      get bindings() { return bindings },
      // D1 stores NULL for undefined; node:sqlite throws on it.
      bind: (...values) => { bindings = values.map((v) => (v === undefined ? null : v)); return stmt },
      first: async () => sqlite.prepare(sql).get(...bindings) ?? null,
      all: async () => ({ results: sqlite.prepare(sql).all(...bindings), success: true }),
      run: async () => { const r = sqlite.prepare(sql).run(...bindings); return { success: true, meta: { changes: Number(r.changes) } } },
    }
    return stmt
  }
  const db = {
    prepare,
    // D1 runs a batch as one transaction: all of it, or none of it.
    batch: async (statements) => {
      sqlite.exec('BEGIN')
      try {
        const out = []
        for (const s of statements) out.push(await s.run())
        sqlite.exec('COMMIT')
        return out
      } catch (error) {
        sqlite.exec('ROLLBACK')
        throw error
      }
    },
  }
  return { db, sqlite, rows: (sql, ...values) => sqlite.prepare(sql).all(...values) }
}

const b64url = (bytes) => Buffer.from(bytes).toString('base64url')

// An issuer with its own RSA key. `keys` is a KeyStore whose fetch returns that key, so the
// handler verifies a real signature and never reaches Google.
export async function makeIssuer({ kid = 'test-key', now = () => Date.now() } = {}) {
  const pair = await webcrypto.subtle.generateKey(
    { name: 'RSASSA-PKCS1-v1_5', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' },
    true, ['sign', 'verify'])
  const jwk = await webcrypto.subtle.exportKey('jwk', pair.publicKey)
  let fetches = 0
  const fetchKeys = async () => {
    fetches += 1
    return new Response(JSON.stringify({ keys: [{ kid, kty: 'RSA', n: jwk.n, e: jwk.e, alg: 'RS256' }] }),
      { headers: { 'cache-control': 'public, max-age=3600' } })
  }
  const sign = async (claims, { header = {}, key = pair.privateKey } = {}) => {
    const head = b64url(JSON.stringify({ alg: 'RS256', kid, typ: 'JWT', ...header }))
    const body = b64url(JSON.stringify(claims))
    const signature = await webcrypto.subtle.sign('RSASSA-PKCS1-v1_5', key, new TextEncoder().encode(`${head}.${body}`))
    return `${head}.${body}.${b64url(new Uint8Array(signature))}`
  }
  const token = (uid, email, extra = {}) => {
    const seconds = Math.floor(now() / 1000)
    return sign({
      aud: PROJECT, iss: `https://securetoken.google.com/${PROJECT}`, sub: uid, iat: seconds - 10, exp: seconds + 3600,
      ...(email ? { email, email_verified: true } : {}), ...extra,
    })
  }
  return { keys: new KeyStore(fetchKeys, 'https://keys.test/', now), sign, token, fetchCount: () => fetches, pair }
}

// R2 as far as the API uses it. `put` with a sha256 refuses bytes that do not hash to it, which
// is the check the real bucket makes on the stream.
export function fakeBucket() {
  const objects = new Map()
  return {
    objects,
    async put(key, value, options = {}) {
      const bytes = Buffer.from(await new Response(value).arrayBuffer())
      if (options.sha256 && sha256(bytes) !== options.sha256) throw new Error('The SHA-256 checksum you specified did not match what we received.')
      objects.set(key, { bytes, httpMetadata: options.httpMetadata ?? {} })
      return { key, size: bytes.length }
    },
    async head(key) {
      const found = objects.get(key)
      return found ? { key, size: found.bytes.length } : null
    },
    async get(key) {
      const found = objects.get(key)
      if (!found) return null
      return { key, size: found.bytes.length, body: new Response(found.bytes).body, httpMetadata: found.httpMetadata }
    },
  }
}

// A small athlete version: a manifest in the real format, and bytes that match it.
export function athleteVersion({ revision = 9, glb = 'glb bytes of revision 9', library = '{"techniques":[]}' } = {}) {
  const files = {
    'netball-athlete.glb': Buffer.from(glb),
    'movement-library.json': Buffer.from(library),
    'netball-athlete.blend': Buffer.from('the master, which Studio never serves'),
  }
  const entry = (name, role) => ({ role, bytes: files[name].length, sha256: sha256(files[name]) })
  const manifest = Buffer.from(JSON.stringify({
    format: 'braven-athlete-manifest', formatVersion: 1,
    asset: { name: 'Braven netball athlete', revision, parentSha256: null },
    sport: 'netball',
    rig: { family: 'braven-athlete-v6', contractBones: ['root', 'pelvis', 'calf_l', 'calf_r', 'hand_r'], jointCount: 70 },
    files: {
      'netball-athlete.glb': entry('netball-athlete.glb', 'model'),
      'movement-library.json': entry('movement-library.json', 'library'),
      'netball-athlete.blend': entry('netball-athlete.blend', 'master'),
    },
    clips: [
      { id: 'Jog', kind: 'general', seconds: 1.2, fps: 30, review: 'not-graded' },
      { id: 'netball_chest_pass', kind: 'technique', seconds: 2.5, fps: 30, review: 'needs-review' },
    ],
  }, null, 2))
  return { manifest, id: sha256(manifest), files, modelSha256: sha256(files['netball-athlete.glb']) }
}

// One API with its database, bucket and clock, and one function to call it.
export async function makeApp() {
  let clock = Date.UTC(2026, 10, 12, 12, 0, 0)
  let serial = 0
  const now = () => clock
  const issuer = await makeIssuer({ now })
  const { db, sqlite, rows } = testDb()
  const bucket = fakeBucket()
  const env = {
    DB: db, VERSIONS: bucket, FIREBASE_PROJECT_ID: PROJECT,
    ASSETS: { fetch: async () => new Response('the Studio page', { headers: { 'content-type': 'text/html' } }) },
  }
  const deps = { keys: issuer.keys, now, id: () => `id-${String(++serial).padStart(4, '0')}` }

  const call = async (method, pathname, { token, json, bytes, headers = {} } = {}) => {
    const init = { method, headers: { ...headers } }
    if (token) init.headers.authorization = `Bearer ${token}`
    if (json !== undefined) { init.body = JSON.stringify(json); init.headers['content-type'] = 'application/json' }
    if (bytes !== undefined) { init.body = bytes; init.headers['content-length'] = String(bytes.length) }
    const response = await handle(new Request(`https://studio.test${pathname}`, init), env, deps)
    const text = await response.clone().text()
    let body = null
    try { body = JSON.parse(text) } catch { body = text }
    return { status: response.status, body, response }
  }

  // People in a state the tests start from: an invitation row is the only way in, as in production.
  const invite = (email, role) => sqlite.prepare(
    'INSERT INTO invitations (email, role, invited_by, created_at) VALUES (?, ?, ?, ?)').run(email.toLowerCase(), role, 'seed', clock)
  const person = async (uid, email, role) => {
    invite(email, role)
    const token = await issuer.token(uid, email)
    const me = await call('GET', '/api/me', { token })
    if (me.status !== 200) throw new Error(`could not admit ${email}: ${me.status} ${JSON.stringify(me.body)}`)
    return token
  }
  // A version an author uploaded and, when asked, the owner published.
  const version = async ({ authorToken, ownerToken, publish = true, ...options } = {}) => {
    const v = athleteVersion(options)
    const made = await call('PUT', '/api/versions', { token: authorToken, bytes: v.manifest })
    if (made.status !== 201) throw new Error(`manifest refused: ${made.status} ${JSON.stringify(made.body)}`)
    for (const name of ['netball-athlete.glb', 'movement-library.json']) {
      const put = await call('PUT', `/api/versions/${v.id}/files/${name}`, { token: authorToken, bytes: v.files[name] })
      if (put.status !== 201) throw new Error(`${name} refused: ${put.status} ${JSON.stringify(put.body)}`)
    }
    if (publish) {
      const done = await call('POST', `/api/versions/${v.id}/publish`, { token: ownerToken })
      if (done.status !== 200) throw new Error(`publish refused: ${done.status} ${JSON.stringify(done.body)}`)
    }
    return v
  }
  return { call, env, deps, issuer, sqlite, rows, bucket, invite, person, version, advance: (ms) => { clock += ms }, now }
}
