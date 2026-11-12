// The review loop on the Studio page, without a page: the sign-in session, the API calls and
// the comment rules (specification 4, phase A).
import assert from 'node:assert/strict'
import test from 'node:test'
import { createHash } from 'node:crypto'

import { PENDING_EMAIL_KEY, SESSION_KEY, SignInError, createSession } from '../src/session.js'
import { ApiError, createApi } from '../src/review-api.js'
import { approvalText, approvers, bodyParts, buildComment, commentableClip, formatRange, markers, phaseAt, splitByVersion, threads } from '../src/comments.js'

const memory = () => {
  const map = new Map()
  return { map, getItem: (k) => (map.has(k) ? map.get(k) : null), setItem: (k, v) => { map.set(k, String(v)) }, removeItem: (k) => { map.delete(k) } }
}
const answer = (status, body) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } })

// A sign-in service that records what it was asked.
function identity(replies) {
  const calls = []
  const fetch = async (url, init) => {
    calls.push({ url: String(url), init, body: init.headers['content-type'].includes('json') ? JSON.parse(init.body) : Object.fromEntries(new URLSearchParams(init.body)) })
    const reply = replies.shift()
    if (reply instanceof Error) throw reply
    return answer(reply.status ?? 200, reply.body)
  }
  return { fetch, calls }
}
const LINK = 'https://studio.example/?apiKey=k&oobCode=CODE123&mode=signIn&lang=en'

test('a sign-in link is asked for the typed address, and the address is kept for the return', async () => {
  const service = identity([{ body: { email: 'coach@example.org' } }])
  const storage = memory()
  const session = createSession({ apiKey: 'public-key', storage, fetch: service.fetch })
  await session.sendLink('  coach@example.org ', 'https://studio.example/')
  assert.match(service.calls[0].url, /accounts:sendOobCode\?key=public-key$/)
  assert.deepEqual(service.calls[0].body, { requestType: 'EMAIL_SIGNIN', email: 'coach@example.org', continueUrl: 'https://studio.example/', canHandleCodeInApp: true })
  assert.equal(session.pendingEmail(), 'coach@example.org')
  assert.equal(session.current(), null, 'asking for a link is not a sign-in')
})

test('text that is not an address asks for no mail', async () => {
  const service = identity([])
  const session = createSession({ apiKey: 'k', storage: memory(), fetch: service.fetch })
  for (const bad of ['', 'coach', 'coach@', 'a b@c.d']) {
    await assert.rejects(session.sendLink(bad, 'https://studio.example/'), (e) => e instanceof SignInError && e.code === 'INVALID_EMAIL')
  }
  assert.equal(service.calls.length, 0)
})

test('only an address with a sign-in code is a sign-in link', () => {
  const session = createSession({ apiKey: 'k', storage: memory(), fetch: async () => answer(200, {}) })
  assert.equal(session.linkCode(LINK), 'CODE123')
  assert.equal(session.linkCode('https://studio.example/'), null)
  assert.equal(session.linkCode('https://studio.example/?mode=resetPassword&oobCode=X'), null)
  assert.equal(session.linkCode('not a url'), null)
})

test('the link signs the person in: the refresh token is stored and the ID token is not', async () => {
  const service = identity([{ body: { idToken: 'ID-1', refreshToken: 'REFRESH-1', localId: 'uid-coach', email: 'coach@example.org', expiresIn: '3600' } }])
  const storage = memory()
  storage.setItem(PENDING_EMAIL_KEY, 'coach@example.org')
  const session = createSession({ apiKey: 'k', storage, fetch: service.fetch, now: () => 1_000_000 })
  assert.deepEqual(await session.completeLink(LINK), { uid: 'uid-coach', email: 'coach@example.org' })
  assert.deepEqual(service.calls[0].body, { email: 'coach@example.org', oobCode: 'CODE123' })
  assert.deepEqual(JSON.parse(storage.getItem(SESSION_KEY)), { uid: 'uid-coach', email: 'coach@example.org', refreshToken: 'REFRESH-1' })
  assert.ok(![...storage.map.values()].some((v) => v.includes('ID-1')), 'the ID token is not in storage')
  assert.equal(storage.getItem(PENDING_EMAIL_KEY), null)
  assert.equal(await session.token(), 'ID-1')
  assert.equal(service.calls.length, 1, 'a fresh token needs no refresh')
})

test('a link opened on another device asks for the address, and does not guess it', async () => {
  const service = identity([])
  const session = createSession({ apiKey: 'k', storage: memory(), fetch: service.fetch })
  await assert.rejects(session.completeLink(LINK), (e) => e.code === 'email_needed')
  assert.equal(service.calls.length, 0)
})

test('a used link says so in words a person can act on', async () => {
  const service = identity([{ status: 400, body: { error: { message: 'INVALID_OOB_CODE' } } }])
  const session = createSession({ apiKey: 'k', storage: memory(), fetch: service.fetch })
  await assert.rejects(session.completeLink(LINK, 'coach@example.org'), (e) => e.code === 'INVALID_OOB_CODE' && /Ask for a new one/.test(e.message))
  assert.equal(session.current(), null)
})

test('a token near its end is refreshed once, for all who wait', async () => {
  let clock = 0
  const service = identity([
    { body: { idToken: 'ID-1', refreshToken: 'REFRESH-1', localId: 'uid', email: 'c@e.org', expiresIn: '3600' } },
    { body: { id_token: 'ID-2', refresh_token: 'REFRESH-2', expires_in: '3600' } },
  ])
  const storage = memory()
  const session = createSession({ apiKey: 'k', storage, fetch: service.fetch, now: () => clock })
  await session.completeLink(LINK, 'c@e.org')
  clock = 3600_000 - 4 * 60_000 // four minutes left: inside the margin
  assert.deepEqual(await Promise.all([session.token(), session.token(), session.token()]), ['ID-2', 'ID-2', 'ID-2'])
  assert.equal(service.calls.length, 2, 'one refresh for three callers')
  assert.match(service.calls[1].url, /securetoken\.googleapis\.com\/v1\/token\?key=k$/)
  assert.deepEqual(service.calls[1].body, { grant_type: 'refresh_token', refresh_token: 'REFRESH-1' })
  assert.equal(JSON.parse(storage.getItem(SESSION_KEY)).refreshToken, 'REFRESH-2', 'a replaced refresh token is kept')
})

test('a refused refresh signs the person out; a lost connection does not', async () => {
  const stored = JSON.stringify({ uid: 'uid', email: 'c@e.org', refreshToken: 'R' })
  const offline = memory(); offline.setItem(SESSION_KEY, stored)
  const down = createSession({ apiKey: 'k', storage: offline, fetch: identity([new TypeError('failed to fetch')]).fetch })
  await assert.rejects(down.token(), (e) => e.code === 'offline')
  assert.deepEqual(down.current(), { uid: 'uid', email: 'c@e.org' })

  const refused = memory(); refused.setItem(SESSION_KEY, stored)
  const gone = createSession({ apiKey: 'k', storage: refused, fetch: identity([{ status: 400, body: { error: { message: 'TOKEN_EXPIRED' } } }]).fetch })
  await assert.rejects(gone.token(), (e) => e.code === 'TOKEN_EXPIRED')
  assert.equal(gone.current(), null)
  await assert.rejects(gone.token(), (e) => e.code === 'signed_out')
})

test('stored text that is not a session is no session', () => {
  for (const value of ['{', '"text"', '{"uid":"u"}', '{"refreshToken":"r"}', 'null']) {
    const storage = memory(); storage.setItem(SESSION_KEY, value)
    assert.equal(createSession({ apiKey: 'k', storage, fetch: async () => answer(200, {}) }).current(), null, value)
  }
})

test('sign-out forgets the session and the pending address', async () => {
  const storage = memory()
  storage.setItem(SESSION_KEY, JSON.stringify({ uid: 'u', email: 'c@e.org', refreshToken: 'R' }))
  storage.setItem(PENDING_EMAIL_KEY, 'c@e.org')
  const session = createSession({ apiKey: 'k', storage, fetch: async () => answer(200, {}) })
  session.signOut()
  assert.equal(storage.map.size, 0)
})

// ---- the API calls

const sha = (bytes) => createHash('sha256').update(bytes).digest('hex')
function server(routes) {
  const calls = []
  const fetch = async (url, init) => {
    calls.push({ url, init })
    const route = routes[`${init.method} ${url}`]
    if (!route) return answer(404, { error: 'no_such_route' })
    return typeof route === 'function' ? route(init) : route
  }
  return { fetch, calls }
}
const signedIn = { token: async () => 'ID-TOKEN' }

test('each call carries the token, to a path on the page\'s own origin', async () => {
  const api = server({ 'GET /api/me': answer(200, { uid: 'u', role: 'reviewer' }) })
  assert.deepEqual(await createApi({ session: signedIn, fetch: api.fetch }).me(), { uid: 'u', role: 'reviewer' })
  assert.equal(api.calls[0].init.headers.authorization, 'Bearer ID-TOKEN')
})

test('a refusal becomes words a coach can act on, with its code kept', async () => {
  const api = server({ 'GET /api/me': answer(403, { error: 'not_invited' }), 'GET /api/versions': answer(401, { error: 'bad_token', reason: 'expired' }) })
  const client = createApi({ session: signedIn, fetch: api.fetch })
  await assert.rejects(client.me(), (e) => e instanceof ApiError && e.status === 403 && e.code === 'not_invited' && /no invitation/.test(e.message))
  await assert.rejects(client.versions(), (e) => e.status === 401 && /Sign in again/.test(e.message))
  const offline = createApi({ session: signedIn, fetch: async () => { throw new TypeError('failed') } })
  await assert.rejects(offline.me(), (e) => e.code === 'offline')
})

test('a file is handed on only when its bytes have the hash the version names', async () => {
  const glb = new TextEncoder().encode('the model bytes')
  const id = 'a'.repeat(64)
  const api = server({ [`GET /api/versions/${id}/files/netball-athlete.glb`]: () => new Response(glb, { headers: { 'content-length': String(glb.length) } }) })
  const client = createApi({ session: signedIn, fetch: api.fetch })
  const progress = []
  const bytes = await client.file(id, 'netball-athlete.glb', sha(glb), (loaded, total) => progress.push([loaded, total]))
  assert.deepEqual([...bytes], [...glb])
  assert.deepEqual(progress.at(-1), [glb.length, glb.length])
  await assert.rejects(client.file(id, 'netball-athlete.glb', sha('other bytes')), (e) => e.code === 'wrong_bytes' && /did not load it/.test(e.message))
})

test('the manifest must hash to the version id it was asked for', async () => {
  const manifest = new TextEncoder().encode(JSON.stringify({ format: 'braven-athlete-manifest', clips: [] }))
  const id = sha(manifest)
  const other = 'b'.repeat(64)
  const api = server({
    [`GET /api/versions/${id}/files/athlete-manifest.json`]: () => new Response(manifest),
    [`GET /api/versions/${other}/files/athlete-manifest.json`]: () => new Response(manifest),
  })
  const client = createApi({ session: signedIn, fetch: api.fetch })
  assert.equal((await client.manifest(id)).format, 'braven-athlete-manifest')
  await assert.rejects(client.manifest(other), (e) => e.code === 'wrong_bytes')
})

test('a comment and an answer are posted as the API reads them', async () => {
  const api = server({ 'POST /api/comments': (init) => answer(201, { id: 'c1', got: JSON.parse(init.body) }), 'GET /api/comments?version=v1&clip=Jog': answer(200, { comments: [], truncated: false }) })
  const client = createApi({ session: signedIn, fetch: api.fetch })
  assert.deepEqual((await client.answer('c0', 'Fixed.')).got, { parentId: 'c0', body: 'Fixed.' })
  assert.deepEqual(await client.comments({ versionId: 'v1', clipId: 'Jog' }), { comments: [], truncated: false })
})

// ---- the comment rules

const manifest = {
  rig: { contractBones: ['root', 'pelvis', 'calf_l', 'hand_r', 'clavicle_l'] },
  clips: [{ id: 'netball_chest_pass', seconds: 2.5, fps: 30 }, { id: 'Receive_pass', seconds: 3, fps: 30 }],
}
const clip = commentableClip(manifest, 'netball_chest_pass', 2.5)
const person = (name, role = 'reviewer') => ({ uid: name, name, role })
const made = (id, extra = {}) => ({ id, versionId: 'v2', clipId: 'netball_chest_pass', tStart: 1, tEnd: null, kind: 'looks-wrong', body: 'x', parentId: null, author: person('Erin'), createdAt: 10, ...extra })

test('a comment is offered only on a clip the version has, at the length the version gives', () => {
  assert.deepEqual(clip, { id: 'netball_chest_pass', seconds: 2.5, end: 2.5 + 1 / 30 })
  assert.equal(commentableClip(manifest, 'Moonwalk', 2.5), null)
  // A movement at another length than the version gives is not the version's clip.
  assert.equal(commentableClip(manifest, 'Receive_pass', 5.4), null)
  assert.notEqual(commentableClip(manifest, 'Receive_pass', 3.02), null, 'inside one frame is the same clip')
  // Studio builds its receive-and-pass sequence under the clip's own name and at its own length.
  assert.equal(commentableClip(manifest, 'Receive_pass', 3, ['Receive_pass']), null)
  assert.notEqual(commentableClip(manifest, 'netball_chest_pass', 2.5, ['Receive_pass']), null)
})

test('the body parts offered are the ones this rig has, in a coach\'s words, and the ball', () => {
  assert.deepEqual(bodyParts(manifest), [{ id: 'pelvis', label: 'Pelvis' }, { id: 'hand_r', label: 'Right wrist and hand' }, { id: 'calf_l', label: 'Left knee' }, { id: 'ball', label: 'Ball' }])
})

test('the phase at a time is the last one that started', () => {
  const phases = [{ name: 'ready', time: 0 }, { name: 'release', time: 1.2 }, { name: 'follow through', time: 1.8 }]
  assert.deepEqual([0, 1.19, 1.2, 2.4].map((t) => phaseAt(phases, t)), ['ready', 'ready', 'release', 'follow through'])
  assert.equal(phaseAt([], 1), null)
  assert.equal(phaseAt([{ name: 'late', time: 2 }], 1), null)
})

test('a filled form becomes the comment the API takes', () => {
  const built = buildComment({ versionId: 'v2', clip, kind: 'looks-wrong', body: '  The knee is stiff. ', tStart: 1.23456, tEnd: 1.6, bodyPart: 'calf_l', phase: 'release',
    cameraView: 'side', camera: { position: [1, 2, 3], target: [0, 1, 0] }, role: 'reviewer' })
  assert.deepEqual(built, { versionId: 'v2', clipId: 'netball_chest_pass', kind: 'looks-wrong', body: 'The knee is stiff.', tStart: 1.235, tEnd: 1.6,
    bodyPart: 'calf_l', phase: 'release', cameraView: 'side', camera: { position: [1, 2, 3], target: [0, 1, 0] } })
  // What was left empty is left out, not sent as empty text.
  assert.deepEqual(buildComment({ versionId: 'v2', clip, kind: 'question', body: 'Why?', tStart: 0, bodyPart: '', phase: null, role: 'author' }),
    { versionId: 'v2', clipId: 'netball_chest_pass', kind: 'question', body: 'Why?', tStart: 0 })
})

test('a form that cannot be a comment says why, in words', () => {
  const base = { versionId: 'v2', clip, kind: 'looks-wrong', body: 'x', tStart: 1, role: 'reviewer' }
  const cases = [
    [{ clip: null }, /takes no comment/], [{ kind: 'praise' }, /what kind/], [{ body: '  ' }, /Write what you see/],
    [{ body: 'x'.repeat(4001) }, /too long/], [{ tStart: 2.6 }, /outside/], [{ tStart: -1 }, /outside/], [{ tStart: NaN }, /outside/],
    [{ tEnd: 0.5 }, /after its start/], [{ tEnd: 3 }, /after its start/],
    [{ kind: 'approve', role: 'author' }, /Only a reviewer/], [{ kind: 'approve', role: 'owner' }, /Only a reviewer/],
  ]
  for (const [change, message] of cases) assert.throws(() => buildComment({ ...base, ...change }), message, JSON.stringify(change))
  assert.equal(buildComment({ ...base, kind: 'approve', body: '' }).body, '', 'an approval needs no text')
})

test('answers sit under their comment, and a comment never shows on another version\'s timeline', () => {
  const comments = [made('old', { versionId: 'v1', createdAt: 1 }), made('a'), made('a1', { parentId: 'a', kind: 'answer', author: person('Dev', 'author') }),
    made('other-clip', { clipId: 'Jog' }), made('older', { versionId: 'v0', createdAt: 0 })]
  assert.deepEqual(threads(comments).find((c) => c.id === 'a').answers.map((c) => c.id), ['a1'])
  const split = splitByVersion(comments, 'v2', 'netball_chest_pass')
  assert.deepEqual(split.here.map((c) => c.id), ['a'])
  assert.deepEqual(split.earlier.map((c) => [c.id, c.versionId]), [['old', 'v1'], ['older', 'v0']])
  assert.deepEqual(markers(split.here, 2.5).map((m) => m.id), ['a'], 'only this version is on the timeline')
})

test('a marker sits at its time, a range has a width, and nothing leaves the timeline', () => {
  const list = [made('point', { tStart: 0.5 }), made('range', { tStart: 1, tEnd: 2 }), made('end', { tStart: 2.52 })]
  const out = markers(threads(list), 2.5)
  assert.deepEqual(out.map((m) => [m.id, m.at, m.width]), [['point', 0.2, 0], ['range', 0.4, 0.4], ['end', 1, 0]])
  assert.equal(out[1].label, 'Looks wrong at 1.00 s to 2.00 s, by Erin')
  assert.deepEqual(markers(threads(list), 0), [])
  assert.equal(formatRange({ tStart: 0.5, tEnd: null }), '0.50 s')
})

test('approved means a reviewer approved this clip in this version, and nothing else', () => {
  const approve = (extra) => made(`ap-${Math.random()}`, { kind: 'approve', ...extra })
  assert.deepEqual(approvers([approve({})], 'v2', 'netball_chest_pass'), ['Erin'])
  const not = [approve({ versionId: 'v1' }), approve({ clipId: 'Jog' }), approve({ author: person('Dev', 'author') }), approve({ author: person('Marius', 'owner') }),
    made('talk', { kind: 'question', body: 'approve' }), approve({ parentId: 'x' })]
  assert.deepEqual(approvers(not, 'v2', 'netball_chest_pass'), [], 'another version, another clip, another role or another kind is not an approval')
  assert.equal(approvalText([]), 'No reviewer approved this animation in this version.')
  assert.equal(approvalText(['Erin']), 'Approved in this version by Erin.')
  assert.equal(approvalText(approvers([approve({}), approve({}), approve({ author: person('Sam') }), approve({ author: person('Lee') })], 'v2', 'netball_chest_pass')),
    'Approved in this version by Erin, Sam and Lee.')
})
