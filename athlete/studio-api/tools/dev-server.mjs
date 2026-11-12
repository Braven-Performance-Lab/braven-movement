// The Studio API on this machine, for development and for screenshots. NOT the deployed service.
//
//   node tools/dev-server.mjs --athlete "<athlete output folder>" [--port 5398]
//
// It runs the same `handle()` as the Worker, with SQLite from Node in place of D1 and memory in
// place of R2 (the test stand-ins, tests/helpers.mjs). It adds one thing the Worker must never
// have: a stand-in for the Firebase sign-in service under /dev-identity/, which signs tokens
// with a key made at start. That key is the reason this server binds to 127.0.0.1 only, keeps
// nothing on disk, and is not imported by src/worker.mjs. Nothing here is a secret, and nothing
// here proves the behaviour of D1, R2 or Firebase.
//
// At start it invites three people, uploads the athlete folder as a version, and publishes it:
//   owner@braven.test (owner)   author@braven.test (author)   coach@braven.test (reviewer)
// A "sign-in mail" is a line in this terminal, and GET /dev-identity/last-link?email=... returns
// the same link for a script.
import http from 'node:http'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { createHash, randomBytes } from 'node:crypto'

import { handle } from '../src/worker.mjs'
import { PROJECT, fakeBucket, makeIssuer, testDb } from '../tests/helpers.mjs'

const args = process.argv.slice(2)
const option = (name, fallback) => { const i = args.indexOf(`--${name}`); return i >= 0 ? args[i + 1] : fallback }
const port = Number(option('port', '5398'))
const athlete = option('athlete', process.env.BRAVEN_ATHLETE_OUTPUT)
const HOST = '127.0.0.1'

const issuer = await makeIssuer()
const { db } = testDb()
const env = { DB: db, VERSIONS: fakeBucket(), FIREBASE_PROJECT_ID: PROJECT, ASSETS: { fetch: async () => new Response('The page is served by vite.', { status: 404 }) } }
const deps = { keys: issuer.keys, now: Date.now, id: () => crypto.randomUUID() }

const uidOf = (email) => `dev-${createHash('sha256').update(email).digest('hex').slice(0, 12)}`
const tokenFor = (email) => issuer.token(uidOf(email), email)
const call = async (method, pathname, { token, json, bytes } = {}) => {
  const headers = {}
  if (token) headers.authorization = `Bearer ${token}`
  if (bytes) headers['content-length'] = String(bytes.length)
  if (json) headers['content-type'] = 'application/json'
  const response = await handle(new Request(`http://${HOST}:${port}${pathname}`, { method, headers, body: bytes ?? (json ? JSON.stringify(json) : undefined) }), env, deps)
  const body = await response.json().catch(() => null)
  if (response.status >= 400) throw new Error(`${method} ${pathname} -> ${response.status} ${JSON.stringify(body)}`)
  return body
}

// --- the people and the version this server starts with
const people = { 'owner@braven.test': 'owner', 'author@braven.test': 'author', 'coach@braven.test': 'reviewer' }
for (const [email, role] of Object.entries(people)) {
  await db.prepare('INSERT INTO invitations (email, role, invited_by, created_at) VALUES (?, ?, ?, ?)').bind(email, role, 'dev-server', Date.now()).run()
  await call('GET', '/api/me', { token: await tokenFor(email) })
}
await call('PATCH', '/api/me', { token: await tokenFor('coach@braven.test'), json: { name: 'Coach (development)' } })
await call('PATCH', '/api/me', { token: await tokenFor('author@braven.test'), json: { name: 'Author (development)' } })
let published = 'no athlete folder given: no version is published'
if (athlete) {
  const manifestBytes = readFileSync(path.join(athlete, 'athlete-manifest.json'))
  const author = await tokenFor('author@braven.test')
  const version = await call('PUT', '/api/versions', { token: author, bytes: manifestBytes })
  for (const [name, entry] of Object.entries(JSON.parse(manifestBytes).files)) {
    if (!['model', 'library'].includes(entry.role)) continue
    await call('PUT', `/api/versions/${version.id}/files/${name}`, { token: author, bytes: readFileSync(path.join(athlete, name)) })
  }
  await call('POST', `/api/versions/${version.id}/publish`, { token: await tokenFor('owner@braven.test') })
  published = `version ${version.id.slice(0, 8)} (revision ${version.revision}) is published`
}

// --- the stand-in for the sign-in service
const links = new Map()    // email -> { code, link }
const refresh = new Map()  // refresh token -> email
const json = (res, status, body) => { res.writeHead(status, { 'content-type': 'application/json' }); res.end(JSON.stringify(body)) }
const session = async (email) => {
  const refreshToken = randomBytes(24).toString('hex')
  refresh.set(refreshToken, email)
  return { idToken: await tokenFor(email), refreshToken, localId: uidOf(email), email, expiresIn: '3600' }
}

async function identity(req, res, url, body) {
  if (req.method === 'GET' && url.pathname === '/dev-identity/last-link') {
    const found = links.get(String(url.searchParams.get('email')).toLowerCase())
    return found ? json(res, 200, { link: found.link }) : json(res, 404, { error: 'no link' })
  }
  if (req.method !== 'POST') return json(res, 404, { error: { message: 'NOT_FOUND' } })
  if (url.pathname === '/dev-identity/accounts:sendOobCode') {
    const { email, continueUrl } = JSON.parse(body)
    const code = randomBytes(12).toString('hex')
    const link = `${continueUrl}?mode=signIn&oobCode=${code}`
    links.set(email.toLowerCase(), { code, link })
    console.log(`\n[sign-in mail to ${email}]  ${link}\n`)
    return json(res, 200, { email })
  }
  if (url.pathname === '/dev-identity/accounts:signInWithEmailLink') {
    const { email, oobCode } = JSON.parse(body)
    const sent = links.get(String(email).toLowerCase())
    if (!sent || sent.code !== oobCode) {
      const forOther = [...links.values()].some((l) => l.code === oobCode)
      return json(res, 400, { error: { message: forOther ? 'INVALID_EMAIL_FOR_LINK' : 'INVALID_OOB_CODE' } })
    }
    links.delete(email.toLowerCase())
    return json(res, 200, await session(email.toLowerCase()))
  }
  if (url.pathname === '/dev-identity/token') {
    const email = refresh.get(new URLSearchParams(body.toString()).get('refresh_token'))
    if (!email) return json(res, 400, { error: { message: 'INVALID_REFRESH_TOKEN' } })
    const next = await session(email)
    return json(res, 200, { id_token: next.idToken, refresh_token: next.refreshToken, expires_in: '3600' })
  }
  return json(res, 404, { error: { message: 'NOT_FOUND' } })
}

http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${HOST}:${port}`)
    const chunks = []
    for await (const chunk of req) chunks.push(chunk)
    const body = Buffer.concat(chunks)
    if (url.pathname.startsWith('/dev-identity/')) return await identity(req, res, url, body)
    const headers = new Headers()
    for (const [name, value] of Object.entries(req.headers)) if (typeof value === 'string' && !['host', 'connection'].includes(name)) headers.set(name, value)
    const hasBody = !['GET', 'HEAD'].includes(req.method)
    const response = await handle(new Request(url, { method: req.method, headers, body: hasBody ? body : undefined }), env, deps)
    res.writeHead(response.status, Object.fromEntries(response.headers))
    res.end(Buffer.from(await response.arrayBuffer()))
  } catch (error) {
    console.error(error)
    json(res, 500, { error: 'dev_server', message: String(error?.message) })
  }
}).listen(port, HOST, () => {
  console.log(`Studio API for DEVELOPMENT on http://${HOST}:${port}  (memory only; sign-in is a stand-in, not Firebase)`)
  console.log(published)
  console.log(`people: ${Object.entries(people).map(([email, role]) => `${email} (${role})`).join(', ')}`)
})
