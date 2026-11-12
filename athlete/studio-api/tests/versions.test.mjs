// ACC-1 and ACC-3: Studio serves an athlete version named by the hash of its manifest. A
// reviewer never sees one that is not published, and only a person with the owner role publishes.
import assert from 'node:assert/strict'
import test from 'node:test'

import { athleteVersion, makeApp, sha256 } from './helpers.mjs'

async function team() {
  const app = await makeApp()
  const owner = await app.person('uid-owner', 'owner@example.org', 'owner')
  const author = await app.person('uid-author', 'author@example.org', 'author')
  const reviewer = await app.person('uid-coach', 'coach@example.org', 'reviewer')
  return { app, owner, author, reviewer }
}

test('a version is named by the sha256 of its manifest bytes', async () => {
  const { app, author } = await team()
  const v = athleteVersion()
  const made = await app.call('PUT', '/api/versions', { token: author, bytes: v.manifest })
  assert.equal(made.status, 201)
  assert.equal(made.body.id, sha256(v.manifest))
  assert.equal(made.body.state, 'draft')
  assert.equal(made.body.modelSha256, v.modelSha256)
  assert.equal(made.body.revision, 9)
  // The same manifest again is the same version, not a second one.
  assert.equal((await app.call('PUT', '/api/versions', { token: author, bytes: v.manifest })).status, 200)
  assert.equal(app.rows('SELECT * FROM versions').length, 1)
})

test('two uploads of one manifest at one moment make one version, and neither fails', async () => {
  const { app, author } = await team()
  const v = athleteVersion()
  // Hold each upload at the bucket until the two are there. Each one then looked for the
  // version before the other recorded it, which is the overlap this test is about.
  const put = app.bucket.put.bind(app.bucket)
  let arrived = 0
  let release
  const together = new Promise((resolve) => { release = resolve })
  app.bucket.put = async (...args) => {
    arrived += 1
    if (arrived === 2) release()
    await together
    return put(...args)
  }
  const both = await Promise.all([1, 2].map(() => app.call('PUT', '/api/versions', { token: author, bytes: v.manifest })))
  assert.equal(arrived, 2, 'the two uploads did overlap')
  assert.deepEqual(both.map((r) => r.status).sort(), [200, 201])
  assert.deepEqual(both.map((r) => r.body.id), [v.id, v.id])
  assert.equal(app.rows('SELECT * FROM versions').length, 1)
  assert.equal(app.rows("SELECT * FROM events WHERE action = 'version.created'").length, 1)
})

test('a reviewer cannot upload a version or a file', async () => {
  const { app, author, reviewer } = await team()
  const v = athleteVersion()
  assert.equal((await app.call('PUT', '/api/versions', { token: reviewer, bytes: v.manifest })).status, 403)
  await app.call('PUT', '/api/versions', { token: author, bytes: v.manifest })
  const put = await app.call('PUT', `/api/versions/${v.id}/files/netball-athlete.glb`, { token: reviewer, bytes: v.files['netball-athlete.glb'] })
  assert.equal(put.status, 403)
})

test('a manifest of another format, or with no model, is refused', async () => {
  const { app, author } = await team()
  const good = JSON.parse(athleteVersion().manifest)
  const cases = {
    'not JSON': Buffer.from('{'),
    'another format': Buffer.from(JSON.stringify({ ...good, format: 'something-else' })),
    'a later format version': Buffer.from(JSON.stringify({ ...good, formatVersion: 2 })),
    'no model': Buffer.from(JSON.stringify({ ...good, files: { 'movement-library.json': good.files['movement-library.json'] } })),
    'two models': Buffer.from(JSON.stringify({ ...good, files: { ...good.files, 'second.glb': good.files['netball-athlete.glb'] } })),
    'a file name with a path': Buffer.from(JSON.stringify({ ...good, files: { ...good.files, '../x.glb': { role: 'master', bytes: 1, sha256: 'a'.repeat(64) } } })),
    'a hash that is not a sha256': Buffer.from(JSON.stringify({ ...good, files: { ...good.files, 'netball-athlete.glb': { role: 'model', bytes: 3, sha256: 'XYZ' } } })),
    'no clips': Buffer.from(JSON.stringify({ ...good, clips: [] })),
  }
  for (const [name, bytes] of Object.entries(cases)) {
    const refused = await app.call('PUT', '/api/versions', { token: author, bytes })
    assert.equal(refused.status, 400, name)
    assert.equal(refused.body.error, 'bad_manifest', name)
  }
  assert.equal(app.rows('SELECT * FROM versions').length, 0)
})

test('file bytes that do not match the manifest are refused and not stored', async () => {
  const { app, author } = await team()
  const v = athleteVersion()
  await app.call('PUT', '/api/versions', { token: author, bytes: v.manifest })
  const sameLength = Buffer.from(v.files['netball-athlete.glb']).fill(0x41)
  const wrongBytes = await app.call('PUT', `/api/versions/${v.id}/files/netball-athlete.glb`, { token: author, bytes: sameLength })
  assert.equal(wrongBytes.status, 422)
  const wrongSize = await app.call('PUT', `/api/versions/${v.id}/files/netball-athlete.glb`, { token: author, bytes: Buffer.from('short') })
  assert.equal(wrongSize.status, 422)
  assert.equal(app.bucket.objects.size, 1, 'only the manifest is in the bucket')
})

test('only the model, the library and the manifest are held; a master is refused', async () => {
  const { app, author } = await team()
  const v = athleteVersion()
  await app.call('PUT', '/api/versions', { token: author, bytes: v.manifest })
  const master = await app.call('PUT', `/api/versions/${v.id}/files/netball-athlete.blend`, { token: author, bytes: v.files['netball-athlete.blend'] })
  assert.equal(master.status, 404)
  const unknown = await app.call('PUT', `/api/versions/${v.id}/files/extra.bin`, { token: author, bytes: Buffer.from('x') })
  assert.equal(unknown.status, 404)
})

test('only the owner publishes: an author is refused', async () => {
  const { app, owner, author, reviewer } = await team()
  const v = await app.version({ authorToken: author, publish: false })
  for (const token of [author, reviewer]) {
    assert.equal((await app.call('POST', `/api/versions/${v.id}/publish`, { token })).status, 403)
  }
  const done = await app.call('POST', `/api/versions/${v.id}/publish`, { token: owner })
  assert.equal(done.status, 200)
  assert.equal(done.body.state, 'published')
  const event = app.rows("SELECT actor_uid, subject FROM events WHERE action = 'version.published'")
  assert.deepEqual({ ...event[0] }, { actor_uid: 'uid-owner', subject: v.id })
})

test('a version with a file missing cannot be published', async () => {
  const { app, owner, author } = await team()
  const v = athleteVersion()
  await app.call('PUT', '/api/versions', { token: author, bytes: v.manifest })
  await app.call('PUT', `/api/versions/${v.id}/files/netball-athlete.glb`, { token: author, bytes: v.files['netball-athlete.glb'] })
  const refused = await app.call('POST', `/api/versions/${v.id}/publish`, { token: owner })
  assert.equal(refused.status, 409)
  assert.deepEqual(refused.body.missing, ['movement-library.json'])
})

test('a reviewer does not see a draft: not in the list, not its manifest, not its files', async () => {
  const { app, author, reviewer } = await team()
  const v = await app.version({ authorToken: author, publish: false })
  assert.deepEqual((await app.call('GET', '/api/versions', { token: reviewer })).body, { current: null, versions: [] })
  for (const name of ['athlete-manifest.json', 'netball-athlete.glb', 'movement-library.json']) {
    assert.equal((await app.call('GET', `/api/versions/${v.id}/files/${name}`, { token: reviewer })).status, 404, name)
  }
  // The author sees the draft, to check it before the owner publishes it.
  const list = await app.call('GET', '/api/versions', { token: author })
  assert.deepEqual(list.body.versions.map((x) => [x.id, x.state]), [[v.id, 'draft']])
  assert.equal(list.body.current, null)
  assert.equal((await app.call('GET', `/api/versions/${v.id}/files/netball-athlete.glb`, { token: author })).status, 200)
})

test('a published version is served to a reviewer with the bytes that were uploaded', async () => {
  const { app, owner, author, reviewer } = await team()
  const v = await app.version({ authorToken: author, ownerToken: owner })
  const list = await app.call('GET', '/api/versions', { token: reviewer })
  assert.equal(list.body.current, v.id)
  assert.deepEqual(list.body.versions.map((x) => [x.id, x.state, x.revision, x.modelSha256]), [[v.id, 'published', 9, v.modelSha256]])
  for (const [name, bytes] of [['athlete-manifest.json', v.manifest], ['netball-athlete.glb', v.files['netball-athlete.glb']], ['movement-library.json', v.files['movement-library.json']]]) {
    const got = await app.call('GET', `/api/versions/${v.id}/files/${name}`, { token: reviewer })
    assert.equal(got.status, 200, name)
    assert.equal(sha256(Buffer.from(await got.response.arrayBuffer())), sha256(bytes), name)
    assert.match(got.response.headers.get('cache-control'), /private/)
    assert.match(got.response.headers.get('cache-control'), /immutable/)
  }
  assert.equal((await app.call('GET', `/api/versions/${v.id}/files/netball-athlete.blend`, { token: reviewer })).status, 404)
})

test('a published file is never served without a token', async () => {
  const { app, owner, author } = await team()
  const v = await app.version({ authorToken: author, ownerToken: owner })
  assert.equal((await app.call('GET', `/api/versions/${v.id}/files/netball-athlete.glb`)).status, 401)
})

test('a published version cannot change: no new file, no second publication, no row change', async () => {
  const { app, owner, author } = await team()
  const v = await app.version({ authorToken: author, ownerToken: owner })
  const put = await app.call('PUT', `/api/versions/${v.id}/files/netball-athlete.glb`, { token: author, bytes: v.files['netball-athlete.glb'] })
  assert.equal(put.status, 409)
  assert.equal((await app.call('POST', `/api/versions/${v.id}/publish`, { token: owner })).status, 409)
  assert.throws(() => app.sqlite.exec("UPDATE versions SET state = 'draft'"), /published version/)
  assert.throws(() => app.sqlite.exec('DELETE FROM versions'), /never deleted/)
})

test('the current version is the one published last, and the earlier one stays', async () => {
  const { app, owner, author, reviewer } = await team()
  const first = await app.version({ authorToken: author, ownerToken: owner })
  app.advance(60_000)
  const second = await app.version({ authorToken: author, ownerToken: owner, revision: 10, glb: 'glb bytes of revision 10' })
  const list = await app.call('GET', '/api/versions', { token: reviewer })
  assert.equal(list.body.current, second.id)
  assert.deepEqual(list.body.versions.map((x) => x.id), [second.id, first.id])
  assert.equal((await app.call('GET', `/api/versions/${first.id}/files/netball-athlete.glb`, { token: reviewer })).status, 200)
})

test('a version id that is not a sha256 is not looked up', async () => {
  const { app, reviewer } = await team()
  assert.equal((await app.call('GET', '/api/versions/..%2F..%2Fsecret/files/netball-athlete.glb', { token: reviewer })).status, 404)
  assert.equal((await app.call('GET', `/api/versions/${'a'.repeat(64)}/files/netball-athlete.glb`, { token: reviewer })).status, 404)
})
