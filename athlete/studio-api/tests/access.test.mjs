// ACC-2 and ACC-3: nobody gets in without an invitation and a verified email, and each account
// has one role. ACC-5: each of these acts leaves a record.
import assert from 'node:assert/strict'
import test from 'node:test'

import { makeApp } from './helpers.mjs'

test('the health route answers without a token, and names no secret', async () => {
  const app = await makeApp()
  const health = await app.call('GET', '/api/health')
  assert.equal(health.status, 200)
  assert.deepEqual(Object.keys(health.body).sort(), ['ok', 'service'])
})

test('every other API route refuses a request with no token or a bad one', async () => {
  const app = await makeApp()
  for (const [method, path] of [['GET', '/api/me'], ['GET', '/api/versions'], ['GET', '/api/comments'], ['POST', '/api/comments'],
    ['GET', '/api/people'], ['POST', '/api/invitations'], ['PUT', '/api/versions'], ['GET', '/api/versions/abc/files/netball-athlete.glb']]) {
    assert.equal((await app.call(method, path)).status, 401, `${method} ${path} with no token`)
    assert.equal((await app.call(method, path, { token: 'not.a.token' })).status, 401, `${method} ${path} with a bad token`)
  }
})

test('a verified person with no invitation is refused, and no account is made', async () => {
  const app = await makeApp()
  const me = await app.call('GET', '/api/me', { token: await app.issuer.token('uid-stranger', 'stranger@example.org') })
  assert.equal(me.status, 403)
  assert.equal(me.body.error, 'not_invited')
  assert.equal(app.rows('SELECT * FROM members').length, 0)
})

test('an invitation is not redeemed by an address nobody verified', async () => {
  const app = await makeApp()
  app.invite('coach@example.org', 'reviewer')
  const token = await app.issuer.token('uid-thief', null, { email: 'coach@example.org', email_verified: false })
  const me = await app.call('GET', '/api/me', { token })
  assert.equal(me.status, 403)
  assert.equal(me.body.error, 'email_not_verified')
  assert.equal(app.rows('SELECT * FROM members').length, 0)
  // The place is still there for the person the address belongs to.
  const real = await app.call('GET', '/api/me', { token: await app.issuer.token('uid-coach', 'coach@example.org') })
  assert.equal(real.status, 200)
})

test('the first verified request redeems the invitation, whatever the case of the address', async () => {
  const app = await makeApp()
  app.invite('Coach@Example.org', 'reviewer')
  const token = await app.issuer.token('uid-coach', 'COACH@example.ORG', { name: 'Erin' })
  const me = await app.call('GET', '/api/me', { token })
  assert.equal(me.status, 200)
  assert.deepEqual(me.body, { uid: 'uid-coach', email: 'coach@example.org', name: 'Erin', role: 'reviewer' })
  const events = app.rows("SELECT action, actor_uid, subject FROM events WHERE action = 'member.joined'")
  assert.deepEqual(events.map((e) => ({ ...e })), [{ action: 'member.joined', actor_uid: 'uid-coach', subject: 'uid-coach' }])
  // A second request does not join again.
  await app.call('GET', '/api/me', { token })
  assert.equal(app.rows("SELECT * FROM events WHERE action = 'member.joined'").length, 1)
})

test('an invitation admits one account, not each account that later shows the address', async () => {
  const app = await makeApp()
  app.invite('coach@example.org', 'reviewer')
  assert.equal((await app.call('GET', '/api/me', { token: await app.issuer.token('uid-first', 'coach@example.org') })).status, 200)
  assert.equal((await app.call('GET', '/api/me', { token: await app.issuer.token('uid-second', 'coach@example.org') })).status, 403)
})

test('only the owner invites, and only into a known role', async () => {
  const app = await makeApp()
  const owner = await app.person('uid-owner', 'owner@example.org', 'owner')
  const author = await app.person('uid-author', 'author@example.org', 'author')
  const reviewer = await app.person('uid-coach', 'coach@example.org', 'reviewer')
  for (const token of [author, reviewer]) {
    const refused = await app.call('POST', '/api/invitations', { token, json: { email: 'friend@example.org', role: 'reviewer' } })
    assert.equal(refused.status, 403)
  }
  for (const json of [{ email: 'trainer@example.org', role: 'admin' }, { email: 'no-at-sign', role: 'reviewer' }, { role: 'reviewer' }, { email: 'a@b.org' }]) {
    assert.equal((await app.call('POST', '/api/invitations', { token: owner, json })).status, 400, JSON.stringify(json))
  }
  const made = await app.call('POST', '/api/invitations', { token: owner, json: { email: 'Trainer@Example.org', role: 'reviewer' } })
  assert.equal(made.status, 201)
  const joined = await app.call('GET', '/api/me', { token: await app.issuer.token('uid-trainer', 'trainer@example.org') })
  assert.equal(joined.body.role, 'reviewer')
  const invited = app.rows("SELECT actor_uid, subject FROM events WHERE action = 'invitation.created'")
  assert.deepEqual({ ...invited[0] }, { actor_uid: 'uid-owner', subject: 'trainer@example.org' })
})

test('the owner sees the people and the open invitations; nobody else does', async () => {
  const app = await makeApp()
  const owner = await app.person('uid-owner', 'owner@example.org', 'owner')
  const reviewer = await app.person('uid-coach', 'coach@example.org', 'reviewer')
  await app.call('POST', '/api/invitations', { token: owner, json: { email: 'trainer@example.org', role: 'reviewer' } })
  assert.equal((await app.call('GET', '/api/people', { token: reviewer })).status, 403)
  const people = await app.call('GET', '/api/people', { token: owner })
  assert.equal(people.status, 200)
  assert.deepEqual(people.body.members.map((m) => [m.email, m.role]).sort(), [['coach@example.org', 'reviewer'], ['owner@example.org', 'owner']])
  assert.deepEqual(people.body.invitations.map((i) => [i.email, i.role]), [['trainer@example.org', 'reviewer']])
})

test('a revoked invitation admits nobody', async () => {
  const app = await makeApp()
  const owner = await app.person('uid-owner', 'owner@example.org', 'owner')
  await app.call('POST', '/api/invitations', { token: owner, json: { email: 'trainer@example.org', role: 'reviewer' } })
  const revoked = await app.call('DELETE', '/api/invitations/trainer%40example.org', { token: owner })
  assert.equal(revoked.status, 200)
  assert.equal((await app.call('GET', '/api/me', { token: await app.issuer.token('uid-trainer', 'trainer@example.org') })).status, 403)
  assert.equal(app.rows("SELECT * FROM events WHERE action = 'invitation.revoked'").length, 1)
  assert.equal((await app.call('DELETE', '/api/invitations/nobody%40example.org', { token: owner })).status, 404)
})

test('only the owner revokes an invitation', async () => {
  const app = await makeApp()
  const owner = await app.person('uid-owner', 'owner@example.org', 'owner')
  const author = await app.person('uid-author', 'author@example.org', 'author')
  const reviewer = await app.person('uid-coach', 'coach@example.org', 'reviewer')
  await app.call('POST', '/api/invitations', { token: owner, json: { email: 'trainer@example.org', role: 'reviewer' } })
  for (const token of [author, reviewer]) {
    assert.equal((await app.call('DELETE', '/api/invitations/trainer%40example.org', { token })).status, 403)
  }
  assert.equal(app.rows("SELECT * FROM events WHERE action = 'invitation.revoked'").length, 0)
  // The invitation is still open: the trainer comes in.
  assert.equal((await app.call('GET', '/api/me', { token: await app.issuer.token('uid-trainer', 'trainer@example.org') })).status, 200)
})

test('an address that is already a member is not invited again', async () => {
  const app = await makeApp()
  const owner = await app.person('uid-owner', 'owner@example.org', 'owner')
  await app.person('uid-coach', 'coach@example.org', 'reviewer')
  // Such an invitation would stay open, for another account with that address to redeem.
  const refused = await app.call('POST', '/api/invitations', { token: owner, json: { email: 'Coach@example.org', role: 'author' } })
  assert.equal(refused.status, 409)
  assert.equal(refused.body.error, 'already_member')
  assert.equal(app.rows('SELECT * FROM invitations WHERE redeemed_at IS NULL AND revoked_at IS NULL').length, 0)
})

test('with two owners one can remove the other, and then the last one stays', async () => {
  const app = await makeApp()
  const first = await app.person('uid-owner-1', 'one@example.org', 'owner')
  await app.person('uid-owner-2', 'two@example.org', 'owner')
  assert.equal((await app.call('POST', '/api/people/uid-owner-2/remove', { token: first })).status, 200)
  const refused = await app.call('POST', '/api/people/uid-owner-1/remove', { token: first })
  assert.equal(refused.status, 409)
  assert.equal(refused.body.error, 'last_owner')
  // The refused removal left no record of a removal that did not happen.
  assert.deepEqual(app.rows("SELECT subject FROM events WHERE action = 'member.removed'").map((e) => e.subject), ['uid-owner-2'])
})

test('a path that is not valid text is not found, and is not a server error', async () => {
  const app = await makeApp()
  const owner = await app.person('uid-owner', 'owner@example.org', 'owner')
  assert.equal((await app.call('POST', '/api/people/%E0/remove', { token: owner })).status, 404)
  assert.equal((await app.call('DELETE', '/api/invitations/%E0', { token: owner })).status, 404)
})

test('a removed person is refused at once, with a token that is still valid', async () => {
  const app = await makeApp()
  const owner = await app.person('uid-owner', 'owner@example.org', 'owner')
  const reviewer = await app.person('uid-coach', 'coach@example.org', 'reviewer')
  assert.equal((await app.call('POST', '/api/people/uid-coach/remove', { token: reviewer })).status, 403)
  const removed = await app.call('POST', '/api/people/uid-coach/remove', { token: owner })
  assert.equal(removed.status, 200)
  const after = await app.call('GET', '/api/me', { token: reviewer })
  assert.equal(after.status, 403)
  assert.equal(after.body.error, 'removed')
  assert.equal(app.rows("SELECT * FROM events WHERE action = 'member.removed' AND subject = 'uid-coach'").length, 1)
  // The record of the person stays: a comment of theirs still has an author.
  assert.equal(app.rows("SELECT * FROM members WHERE uid = 'uid-coach'").length, 1)
})

test('a removed person comes back only through a new invitation', async () => {
  const app = await makeApp()
  const owner = await app.person('uid-owner', 'owner@example.org', 'owner')
  const reviewer = await app.person('uid-coach', 'coach@example.org', 'reviewer')
  await app.call('POST', '/api/people/uid-coach/remove', { token: owner })
  await app.call('POST', '/api/invitations', { token: owner, json: { email: 'coach@example.org', role: 'author' } })
  const back = await app.call('GET', '/api/me', { token: reviewer })
  assert.equal(back.status, 200)
  assert.equal(back.body.role, 'author')
})

test('the last owner cannot be removed', async () => {
  const app = await makeApp()
  const owner = await app.person('uid-owner', 'owner@example.org', 'owner')
  const refused = await app.call('POST', '/api/people/uid-owner/remove', { token: owner })
  assert.equal(refused.status, 409)
  assert.equal((await app.call('GET', '/api/me', { token: owner })).status, 200)
})

test('a person sets the name others see, and only their own', async () => {
  const app = await makeApp()
  const reviewer = await app.person('uid-coach', 'coach@example.org', 'reviewer')
  assert.equal((await app.call('PATCH', '/api/me', { token: reviewer, json: { name: '   ' } })).status, 400)
  assert.equal((await app.call('PATCH', '/api/me', { token: reviewer, json: { name: 'x'.repeat(81) } })).status, 400)
  const named = await app.call('PATCH', '/api/me', { token: reviewer, json: { name: ' Erin Burger ' } })
  assert.equal(named.status, 200)
  assert.equal((await app.call('GET', '/api/me', { token: reviewer })).body.name, 'Erin Burger')
})

test('a change of name is recorded, because the name shows beside each comment', async () => {
  const app = await makeApp()
  const reviewer = await app.person('uid-coach', 'coach@example.org', 'reviewer')
  await app.call('PATCH', '/api/me', { token: reviewer, json: { name: 'Erin' } })
  await app.call('PATCH', '/api/me', { token: reviewer, json: { name: 'Somebody Else' } })
  // The same name again is not a change.
  await app.call('PATCH', '/api/me', { token: reviewer, json: { name: 'Somebody Else' } })
  const renames = app.rows("SELECT actor_uid, subject, detail FROM events WHERE action = 'member.renamed' ORDER BY rowid")
  assert.deepEqual(renames.map((e) => [e.actor_uid, e.subject, JSON.parse(e.detail)]), [
    ['uid-coach', 'uid-coach', { from: null, to: 'Erin' }],
    ['uid-coach', 'uid-coach', { from: 'Erin', to: 'Somebody Else' }],
  ])
})

test('a path outside /api/ goes to the Studio page, and an unknown API path does not', async () => {
  const app = await makeApp()
  const page = await app.call('GET', '/')
  assert.equal(page.status, 200)
  assert.equal(page.body, 'the Studio page')
  const reviewer = await app.person('uid-coach', 'coach@example.org', 'reviewer')
  assert.equal((await app.call('GET', '/api/nothing-here', { token: reviewer })).status, 404)
})

test('the record of events cannot be changed or deleted', async () => {
  const app = await makeApp()
  await app.person('uid-coach', 'coach@example.org', 'reviewer')
  assert.throws(() => app.sqlite.exec("UPDATE events SET actor_uid = 'somebody-else'"), /append-only/)
  assert.throws(() => app.sqlite.exec('DELETE FROM events'), /append-only/)
})
