// The owner's part of the review loop without a page: the calls that invite, remove and publish,
// the upload of a version, what happens after a failed admission, and the guards of the hosted
// build (specification 4, phase A: ACC-1, ACC-2, ACC-3).
import assert from 'node:assert/strict'
import test from 'node:test'
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { SignInError } from '../src/session.js'
import { ApiError, afterAdmitError, createApi } from '../src/review-api.js'
import { planUpload } from '../src/version-upload.js'
import { checkHostedBuild, checkHostedOutput } from '../hosted-build.mjs'

const answer = (status, body) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } })
const signedIn = { token: async () => 'ID-TOKEN' }

test('the owner\'s calls go to the routes the API has', async () => {
  const seen = []
  const fetch = async (url, init) => { seen.push([init.method, url, init.body ?? null]); return answer(200, { ok: true }) }
  const client = createApi({ session: signedIn, fetch })
  await client.people()
  await client.invite('Trainer@Example.org', 'reviewer')
  await client.revoke('trainer+netball@example.org')
  await client.remove('uid/with slash')
  await client.publish('a'.repeat(64))
  assert.deepEqual(seen, [
    ['GET', '/api/people', null],
    ['POST', '/api/invitations', JSON.stringify({ email: 'Trainer@Example.org', role: 'reviewer' })],
    ['DELETE', '/api/invitations/trainer%2Bnetball%40example.org', null],
    ['POST', '/api/people/uid%2Fwith%20slash/remove', null],
    ['POST', `/api/versions/${'a'.repeat(64)}/publish`, null],
  ])
})

test('a version goes up as its manifest, then each file under the id the server gave', async () => {
  const seen = []
  const fetch = async (url, init) => {
    seen.push([init.method, url, init.body, init.headers.authorization])
    return answer(201, url === '/api/versions' ? { id: 'f'.repeat(64), state: 'draft' } : { ok: true })
  }
  const client = createApi({ session: signedIn, fetch })
  const manifestBytes = new TextEncoder().encode('{"manifest":true}')
  const model = new Uint8Array([1, 2, 3])
  const made = await client.createVersion(manifestBytes)
  await client.putFile(made.id, 'netball-athlete.glb', model)
  assert.deepEqual(seen, [
    ['PUT', '/api/versions', manifestBytes, 'Bearer ID-TOKEN'],
    ['PUT', `/api/versions/${'f'.repeat(64)}/files/netball-athlete.glb`, model, 'Bearer ID-TOKEN'],
  ])
})

test('a refused upload says which file and why', async () => {
  const fetch = async () => answer(422, { error: 'wrong_bytes', expected: 'a'.repeat(64) })
  const client = createApi({ session: signedIn, fetch })
  await assert.rejects(client.putFile('f'.repeat(64), 'netball-athlete.glb', new Uint8Array([1])),
    (e) => e.code === 'wrong_bytes' && /is not the file the manifest names/.test(e.message))
})

test('after a failed admission the person is signed out only when the sign-in itself is bad', () => {
  assert.equal(afterAdmitError(new ApiError(403, 'not_invited', 'x')), 'refused')
  assert.equal(afterAdmitError(new ApiError(401, 'bad_token', 'x')), 'sign-in')
  // A server fault or a lost connection says nothing about the person: they try again.
  for (const error of [new ApiError(500, 'internal', 'x'), new ApiError(502, 'http_502', 'x'), new ApiError(0, 'offline', 'x'), new Error('unknown')]) {
    assert.equal(afterAdmitError(error), 'retry', error.message)
  }
  // The session says "sign in again" by itself when a refresh was refused.
  assert.equal(afterAdmitError(new SignInError('TOKEN_EXPIRED', 'x')), 'sign-in')
  assert.equal(afterAdmitError(new SignInError('signed_out', 'x')), 'sign-in')
  assert.equal(afterAdmitError(new SignInError('offline', 'x')), 'retry')
})

// ---- the upload of a version from the browser

const picked = (name, text) => {
  const bytes = new TextEncoder().encode(text)
  return { name, size: bytes.length, arrayBuffer: async () => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) }
}
const manifestText = (glb = 'glb', library = '{}') => JSON.stringify({
  format: 'braven-athlete-manifest', formatVersion: 1, asset: { revision: 10 },
  files: {
    'netball-athlete.glb': { role: 'model', bytes: glb.length, sha256: 'a'.repeat(64) },
    'movement-library.json': { role: 'library', bytes: library.length, sha256: 'b'.repeat(64) },
    'netball-athlete.blend': { role: 'master', bytes: 9, sha256: 'c'.repeat(64) },
  },
})

test('an upload takes the manifest and the two files Studio plays, and leaves the masters', async () => {
  const files = [picked('netball-athlete.blend', 'the master'), picked('movement-library.json', '{}'), picked('athlete-manifest.json', manifestText()),
    picked('netball-athlete.glb', 'glb'), picked('notes.txt', 'x')]
  const plan = await planUpload(files)
  assert.equal(plan.revision, 10)
  assert.equal(new TextDecoder().decode(plan.manifestBytes), manifestText())
  assert.deepEqual(plan.files.map((f) => [f.name, f.role, f.file.name]),
    [['netball-athlete.glb', 'model', 'netball-athlete.glb'], ['movement-library.json', 'library', 'movement-library.json']])
})

test('an upload that cannot work says why before a byte is sent', async () => {
  const good = [picked('athlete-manifest.json', manifestText()), picked('netball-athlete.glb', 'glb'), picked('movement-library.json', '{}')]
  await assert.rejects(planUpload(good.slice(1)), /no athlete-manifest\.json/)
  await assert.rejects(planUpload([]), /no athlete-manifest\.json/)
  await assert.rejects(planUpload([good[0], good[2]]), /netball-athlete\.glb is not among the files/)
  await assert.rejects(planUpload([good[0], picked('netball-athlete.glb', 'longer glb'), good[2]]), /netball-athlete\.glb has 10 bytes, and the manifest says 3/)
  await assert.rejects(planUpload([picked('athlete-manifest.json', '{'), good[1], good[2]]), /not a Braven athlete manifest/)
  await assert.rejects(planUpload([picked('athlete-manifest.json', '{"format":"other"}'), good[1], good[2]]), /not a Braven athlete manifest/)
  // The same files under another format name: the name is what is read, not the shape.
  await assert.rejects(planUpload([picked('athlete-manifest.json', manifestText().replace('braven-athlete-manifest', 'another-manifest')), good[1], good[2]]), /not a Braven athlete manifest/)
  await assert.rejects(planUpload([picked('athlete-manifest.json', '{"format":"braven-athlete-manifest","formatVersion":1,"files":{}}'), good[1], good[2]]), /names no model/)
})

test('an upload reads the chosen folder itself, never a subfolder', async () => {
  const inFolder = (relative, text) => ({ ...picked(relative.split('/').at(-1), text), webkitRelativePath: relative })
  const older = manifestText('old').replace('"revision":10', '"revision":8')
  // A folder picker lists the files of every subfolder too, in no promised order. A backup
  // with an earlier manifest must not go up in the place of the folder's own.
  const files = [
    inFolder('09-gait-v2/backup/athlete-manifest.json', older), inFolder('09-gait-v2/backup/netball-athlete.glb', 'old'),
    inFolder('09-gait-v2/athlete-manifest.json', manifestText()), inFolder('09-gait-v2/netball-athlete.glb', 'glb'),
    inFolder('09-gait-v2/movement-library.json', '{}'), inFolder('09-gait-v2/verification/movement-library.json', '{"old":1}'),
  ]
  for (const order of [files, [...files].reverse()]) {
    const plan = await planUpload(order)
    assert.equal(plan.revision, 10)
    assert.deepEqual(plan.files.map((f) => f.file.webkitRelativePath), ['09-gait-v2/netball-athlete.glb', '09-gait-v2/movement-library.json'])
  }
  // The parent of the athlete folder: the manifest is one level too deep, and that is said.
  const parent = files.map((f) => ({ ...f, webkitRelativePath: `candidates/${f.webkitRelativePath}` }))
  await assert.rejects(planUpload(parent), /no athlete-manifest\.json in the folder itself.*Choose the athlete folder, not a folder above it/s)
  // Two files of one name at the top level cannot both be the one the manifest names.
  await assert.rejects(planUpload([picked('athlete-manifest.json', manifestText()), picked('netball-athlete.glb', 'glb'), picked('netball-athlete.glb', 'glb'), picked('movement-library.json', '{}')]),
    /netball-athlete\.glb is there more than one time/)
})

// ---- the hosted build

test('a hosted build signs in through Firebase and nothing else', () => {
  const key = { VITE_FIREBASE_API_KEY: 'public-web-key' }
  assert.doesNotThrow(() => checkHostedBuild(key))
  assert.throws(() => checkHostedBuild({}), /VITE_FIREBASE_API_KEY/)
  assert.throws(() => checkHostedBuild({ VITE_FIREBASE_API_KEY: '' }), /VITE_FIREBASE_API_KEY/)
  // Wherever the stand-in address comes from: the shell, or a .env file that vite reads.
  assert.throws(() => checkHostedBuild({ ...key, VITE_DEV_IDENTITY: '/dev-identity' }), /VITE_DEV_IDENTITY/)
  assert.throws(() => checkHostedBuild({ VITE_FIREBASE_API_KEY: 'development-stand-in' }), /stand-in/)
})

test('a hosted build folder that holds an athlete file is refused', () => {
  const fresh = () => {
    const dir = mkdtempSync(path.join(tmpdir(), 'studio-hosted-'))
    mkdirSync(path.join(dir, 'assets'))
    writeFileSync(path.join(dir, 'index.html'), '<html>')
    writeFileSync(path.join(dir, 'assets', 'index-abc.js'), 'js')
    return dir
  }
  const clean = fresh()
  assert.doesNotThrow(() => checkHostedOutput(clean))
  mkdirSync(path.join(clean, 'athlete-assets'))
  assert.throws(() => checkHostedOutput(clean), /athlete-assets/)
  rmSync(clean, { recursive: true, force: true })
  // By what the file is, wherever a later change puts it.
  for (const name of ['model.glb', 'master.blend', 'athlete-manifest.json', 'movement-library.json']) {
    const dir = fresh()
    writeFileSync(path.join(dir, 'assets', name), 'x')
    assert.throws(() => checkHostedOutput(dir), /holds an athlete file/, name)
    rmSync(dir, { recursive: true, force: true })
  }
})
