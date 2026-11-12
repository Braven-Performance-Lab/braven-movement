// FBK-1, 2, 4, 6 and SAFE-4: a comment belongs to one animation in one version at one time, has
// a kind, and is kept for ever. SAFE-1: an approval counts only when a reviewer made it.
import assert from 'node:assert/strict'
import test from 'node:test'

import { makeApp } from './helpers.mjs'

async function team() {
  const app = await makeApp()
  const owner = await app.person('uid-owner', 'owner@example.org', 'owner')
  const author = await app.person('uid-author', 'author@example.org', 'author')
  const reviewer = await app.person('uid-coach', 'coach@example.org', 'reviewer')
  await app.call('PATCH', '/api/me', { token: reviewer, json: { name: 'Erin' } })
  const v = await app.version({ authorToken: author, ownerToken: owner })
  const comment = (extra = {}) => ({ versionId: v.id, clipId: 'netball_chest_pass', tStart: 1.25, kind: 'looks-wrong', body: 'The left knee is stiff here.', ...extra })
  return { app, owner, author, reviewer, v, comment }
}

test('a comment keeps its animation, its version, its time and who made it', async () => {
  const { app, reviewer, v, comment } = await team()
  const made = await app.call('POST', '/api/comments', { token: reviewer, json: comment({
    tEnd: 1.6, bodyPart: 'calf_l', phase: 'Release', cameraView: 'side',
    camera: { position: [1, 1.5, 3], target: [0, 1, 0] },
  }) })
  assert.equal(made.status, 201)
  const list = await app.call('GET', `/api/comments?version=${v.id}&clip=netball_chest_pass`, { token: reviewer })
  assert.equal(list.status, 200)
  assert.deepEqual(list.body.comments, [{
    id: made.body.id, versionId: v.id, modelSha256: v.modelSha256, clipId: 'netball_chest_pass', tStart: 1.25, tEnd: 1.6,
    kind: 'looks-wrong', body: 'The left knee is stiff here.', bodyPart: 'calf_l', phase: 'Release', cameraView: 'side',
    camera: { position: [1, 1.5, 3], target: [0, 1, 0] }, parentId: null,
    author: { uid: 'uid-coach', name: 'Erin', role: 'reviewer' }, createdAt: app.now(),
  }])
  const event = app.rows("SELECT actor_uid, subject FROM events WHERE action = 'comment.created'")
  assert.deepEqual({ ...event[0] }, { actor_uid: 'uid-coach', subject: made.body.id })
})

test('the optional marks can be left out', async () => {
  const { app, reviewer, comment } = await team()
  const made = await app.call('POST', '/api/comments', { token: reviewer, json: comment() })
  assert.equal(made.status, 201)
  const [row] = app.rows('SELECT t_end, body_part, phase, camera_view, camera FROM comments')
  assert.deepEqual({ ...row }, { t_end: null, body_part: null, phase: null, camera_view: null, camera: null })
})

test('the four kinds are accepted and no other', async () => {
  const { app, reviewer, comment } = await team()
  for (const kind of ['looks-wrong', 'technique-wrong', 'question', 'approve']) {
    assert.equal((await app.call('POST', '/api/comments', { token: reviewer, json: comment({ kind }) })).status, 201, kind)
  }
  for (const kind of ['praise', '', undefined, 'answer']) {
    assert.equal((await app.call('POST', '/api/comments', { token: reviewer, json: comment({ kind }) })).status, 400, String(kind))
  }
})

test('a comment that cannot be placed is refused', async () => {
  const { app, reviewer, comment } = await team()
  const bad = {
    'no version': { versionId: undefined },
    'a version nobody uploaded': { versionId: 'f'.repeat(64) },
    'a clip this version does not have': { clipId: 'Moonwalk' },
    'no time': { tStart: undefined },
    'a time that is text': { tStart: '1.25' },
    'a negative time': { tStart: -0.1 },
    'a time that is not finite': { tStart: 1e400 },
    'a time past the end of the clip': { tStart: 2.75 },
    'a range that ends before it starts': { tStart: 1.5, tEnd: 1.0 },
    'a range that ends past the clip': { tStart: 1.5, tEnd: 9 },
    'a body part the rig does not have': { bodyPart: 'tail' },
    'a camera view that is not one': { cameraView: 'underneath' },
    'a camera with two numbers': { camera: { position: [1, 2], target: [0, 0, 0] } },
    'a camera with text in it': { camera: { position: [1, 2, 'x'], target: [0, 0, 0] } },
    'no body on a question': { body: '   ' },
    'a body that is too long': { body: 'x'.repeat(4001) },
    'a phase name that is too long': { phase: 'p'.repeat(81) },
    'a field the API does not know': { authorUid: 'uid-owner' },
  }
  for (const [name, change] of Object.entries(bad)) {
    const refused = await app.call('POST', '/api/comments', { token: reviewer, json: comment(change) })
    assert.equal(refused.status, 400, `${name}: ${JSON.stringify(refused.body)}`)
  }
  assert.equal(app.rows('SELECT * FROM comments').length, 0)
})

test('a time just past the nominal end is accepted: a clip plays to its last frame', async () => {
  const { app, reviewer, comment } = await team()
  // 2.5 s at 30 frames a second: one frame of tolerance.
  assert.equal((await app.call('POST', '/api/comments', { token: reviewer, json: comment({ tStart: 2.52 }) })).status, 201)
})

test('an approval needs no text', async () => {
  const { app, reviewer, comment } = await team()
  assert.equal((await app.call('POST', '/api/comments', { token: reviewer, json: comment({ kind: 'approve', body: '' }) })).status, 201)
})

test('only a reviewer approves: an author cannot approve the work, and nor can the owner', async () => {
  const { app, owner, author, comment } = await team()
  for (const token of [author, owner]) {
    const refused = await app.call('POST', '/api/comments', { token, json: comment({ kind: 'approve' }) })
    assert.equal(refused.status, 403)
    assert.equal(refused.body.error, 'only_a_reviewer_approves')
  }
  assert.equal(app.rows("SELECT * FROM comments WHERE kind = 'approve'").length, 0)
})

test('nobody comments on a draft as a reviewer, and nobody approves a draft', async () => {
  const { app, author, reviewer, comment } = await team()
  const draft = await app.version({ authorToken: author, publish: false, revision: 10, glb: 'draft glb' })
  const hidden = await app.call('POST', '/api/comments', { token: reviewer, json: comment({ versionId: draft.id }) })
  assert.equal(hidden.status, 400)
  // An author may leave a note on a draft; a reviewer does not see it.
  assert.equal((await app.call('POST', '/api/comments', { token: author, json: comment({ versionId: draft.id, kind: 'question' }) })).status, 201)
  const seen = await app.call('GET', '/api/comments?clip=netball_chest_pass', { token: reviewer })
  assert.deepEqual(seen.body.comments, [])
  assert.equal((await app.call('GET', `/api/comments?version=${draft.id}`, { token: reviewer })).status, 404)
})

test('everybody on the team reads the comments of everybody else', async () => {
  const { app, owner, author, reviewer, v, comment } = await team()
  await app.call('POST', '/api/comments', { token: reviewer, json: comment() })
  await app.call('POST', '/api/comments', { token: author, json: comment({ kind: 'question', body: 'Which frame?' }) })
  for (const token of [owner, author, reviewer]) {
    const list = await app.call('GET', `/api/comments?version=${v.id}`, { token })
    assert.deepEqual(list.body.comments.map((c) => c.author.uid), ['uid-coach', 'uid-author'])
  }
})

test('an answer is a new comment under the first one, on the same clip and version', async () => {
  const { app, author, reviewer, v, comment } = await team()
  const first = await app.call('POST', '/api/comments', { token: reviewer, json: comment() })
  const answer = await app.call('POST', '/api/comments', { token: author, json: { parentId: first.body.id, body: 'Fixed in the next version.' } })
  assert.equal(answer.status, 201)
  const list = await app.call('GET', `/api/comments?version=${v.id}`, { token: reviewer })
  const [, reply] = list.body.comments
  assert.equal(reply.parentId, first.body.id)
  assert.equal(reply.kind, 'answer')
  assert.deepEqual([reply.versionId, reply.clipId, reply.tStart], [v.id, 'netball_chest_pass', 1.25])
  // The first comment is as it was.
  assert.equal(list.body.comments[0].body, 'The left knee is stiff here.')
  // An answer to an answer, to nothing, or with no text is refused.
  assert.equal((await app.call('POST', '/api/comments', { token: author, json: { parentId: answer.body.id, body: 'More.' } })).status, 400)
  assert.equal((await app.call('POST', '/api/comments', { token: author, json: { parentId: 'no-such-comment', body: 'More.' } })).status, 400)
  assert.equal((await app.call('POST', '/api/comments', { token: author, json: { parentId: first.body.id, body: '' } })).status, 400)
})

test('there is no way to edit or delete a comment: not by a route, not by SQL', async () => {
  const { app, owner, reviewer, comment } = await team()
  const made = await app.call('POST', '/api/comments', { token: reviewer, json: comment() })
  for (const method of ['PUT', 'PATCH', 'DELETE']) {
    for (const token of [reviewer, owner]) {
      const refused = await app.call(method, `/api/comments/${made.body.id}`, { token, json: { body: 'changed' } })
      assert.ok([404, 405].includes(refused.status), `${method} gave ${refused.status}`)
    }
  }
  assert.throws(() => app.sqlite.exec("UPDATE comments SET body = 'changed'"), /append-only/)
  assert.throws(() => app.sqlite.exec('DELETE FROM comments'), /append-only/)
  assert.equal(app.rows('SELECT body FROM comments')[0].body, 'The left knee is stiff here.')
})

test('a comment stays on the version it was made on when a later version is published', async () => {
  const { app, owner, author, reviewer, v, comment } = await team()
  const made = await app.call('POST', '/api/comments', { token: reviewer, json: comment() })
  app.advance(60_000)
  const next = await app.version({ authorToken: author, ownerToken: owner, revision: 10, glb: 'glb bytes of revision 10' })
  const onNew = await app.call('GET', `/api/comments?version=${next.id}&clip=netball_chest_pass`, { token: reviewer })
  assert.deepEqual(onNew.body.comments, [], 'the new version starts with no comments')
  const onOld = await app.call('GET', `/api/comments?version=${v.id}&clip=netball_chest_pass`, { token: reviewer })
  assert.deepEqual(onOld.body.comments.map((c) => c.id), [made.body.id])
  // With no version named, the clip's whole history comes back, each comment with its version.
  const history = await app.call('GET', '/api/comments?clip=netball_chest_pass', { token: reviewer })
  assert.deepEqual(history.body.comments.map((c) => [c.id, c.versionId]), [[made.body.id, v.id]])
})

test('a removed person leaves their comments behind, with their name', async () => {
  const { app, owner, reviewer, v, comment } = await team()
  await app.call('POST', '/api/comments', { token: reviewer, json: comment() })
  await app.call('POST', '/api/people/uid-coach/remove', { token: owner })
  const list = await app.call('GET', `/api/comments?version=${v.id}`, { token: owner })
  assert.deepEqual(list.body.comments.map((c) => c.author.name), ['Erin'])
})

test('a body that is not JSON, or is too large, is refused before anything is read from it', async () => {
  const { app, reviewer } = await team()
  assert.equal((await app.call('POST', '/api/comments', { token: reviewer, bytes: Buffer.from('{not json') })).status, 400)
  assert.equal((await app.call('POST', '/api/comments', { token: reviewer, bytes: Buffer.alloc(70_000, 0x20) })).status, 413)
})
