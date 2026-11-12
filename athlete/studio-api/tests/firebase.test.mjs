// The token check is the boundary: past it a uid decides who a person is. Each refusal is named
// and each has a token built to hit it.
import assert from 'node:assert/strict'
import test from 'node:test'
import { webcrypto } from 'node:crypto'

import { verifyIdToken } from '../src/firebase.mjs'
import { makeIssuer, PROJECT } from './helpers.mjs'

const NOW = Date.UTC(2026, 10, 12, 12)
const seconds = Math.floor(NOW / 1000)
const good = { aud: PROJECT, iss: `https://securetoken.google.com/${PROJECT}`, sub: 'uid-1', iat: seconds - 5, exp: seconds + 600 }

async function check(claims, signOptions) {
  const issuer = await makeIssuer({ now: () => NOW })
  const token = await issuer.sign(claims, signOptions)
  return verifyIdToken(token, { projectId: PROJECT, keys: issuer.keys, now: () => NOW })
}

test('a token from the project is accepted, with its verified email', async () => {
  const result = await check({ ...good, email: 'Coach@Example.org', email_verified: true, name: 'Coach' })
  assert.deepEqual(result, { ok: true, user: { uid: 'uid-1', name: 'Coach', email: 'Coach@Example.org', emailVerified: true } })
})

test('email_verified is true only when the claim is exactly true', async () => {
  for (const value of [undefined, false, 'true', 1]) {
    const result = await check({ ...good, email: 'a@b.org', email_verified: value })
    assert.equal(result.user.emailVerified, false, String(value))
  }
})

const refusals = [
  ['wrong_audience', { ...good, aud: 'another-project' }],
  ['wrong_issuer', { ...good, iss: 'https://securetoken.google.com/another-project' }],
  ['expired', { ...good, exp: seconds - 61 }],
  ['not_yet_valid', { ...good, iat: seconds + 61 }],
  ['no_subject', { ...good, sub: '' }],
  ['expired', { ...good, exp: 'later' }],
]
for (const [reason, claims] of refusals) {
  test(`refuses a token: ${reason} (${JSON.stringify(claims).slice(0, 60)})`, async () => {
    assert.deepEqual(await check(claims), { ok: false, reason })
  })
}

test('a clock that is 60 seconds out is tolerated, and no more', async () => {
  assert.equal((await check({ ...good, exp: seconds - 59 })).ok, true)
  assert.equal((await check({ ...good, iat: seconds + 59 })).ok, true)
})

test('the algorithm is asserted, never read from the token', async () => {
  for (const alg of ['none', 'HS256', 'RS512']) {
    assert.deepEqual(await check(good, { header: { alg } }), { ok: false, reason: 'unsupported_algorithm' })
  }
})

test('a key id nobody published is refused', async () => {
  assert.deepEqual(await check(good, { header: { kid: 'somebody-elses-key' } }), { ok: false, reason: 'unknown_key' })
})

test('a token signed by another key under our key id is refused', async () => {
  const other = await webcrypto.subtle.generateKey(
    { name: 'RSASSA-PKCS1-v1_5', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' }, true, ['sign', 'verify'])
  assert.deepEqual(await check(good, { key: other.privateKey }), { ok: false, reason: 'bad_signature' })
})

test('changed claims under the original signature are refused', async () => {
  const issuer = await makeIssuer({ now: () => NOW })
  const [head, , signature] = (await issuer.sign(good)).split('.')
  const forged = Buffer.from(JSON.stringify({ ...good, sub: 'the-owner' })).toString('base64url')
  const result = await verifyIdToken(`${head}.${forged}.${signature}`, { projectId: PROJECT, keys: issuer.keys, now: () => NOW })
  assert.deepEqual(result, { ok: false, reason: 'bad_signature' })
})

test('text that is not a token is malformed', async () => {
  const issuer = await makeIssuer({ now: () => NOW })
  for (const token of ['', 'abc', 'a.b', 'a.b.c.d', '!!.!!.!!']) {
    assert.deepEqual(await verifyIdToken(token, { projectId: PROJECT, keys: issuer.keys, now: () => NOW }), { ok: false, reason: 'malformed' }, token)
  }
})

test('unknown key ids send the Worker to the key server once a minute at most', async () => {
  let clock = NOW
  const issuer = await makeIssuer({ now: () => clock })
  const options = { projectId: PROJECT, keys: issuer.keys, now: () => clock }
  await verifyIdToken(await issuer.sign(good), options)
  assert.equal(issuer.fetchCount(), 1)
  for (let i = 0; i < 5; i += 1) await verifyIdToken(await issuer.sign(good, { header: { kid: `random-${i}` } }), options)
  assert.equal(issuer.fetchCount(), 2, 'five unknown key ids made one more fetch, not five')
  clock += 61_000
  await verifyIdToken(await issuer.sign({ ...good, exp: seconds + 900 }, { header: { kid: 'random-again' } }), options)
  assert.equal(issuer.fetchCount(), 3)
})
