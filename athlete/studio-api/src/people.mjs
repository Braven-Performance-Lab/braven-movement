// Who may come in, and as what (specification 4: ACC-2, ACC-3).
//
// Firebase proves who a person is. It does not decide whether they may use Studio: the Firebase
// project makes an account for any address that asks. So the gate is here. A verified token is
// admitted only when its uid is a member, or its verified email has an open invitation, which
// the first request then redeems.
import { event, json, readJson, refuse } from './http.mjs'

export const ROLES = ['reviewer', 'author', 'owner']

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const cleanEmail = (value) => (typeof value === 'string' && value.length <= 254 && EMAIL.test(value.trim()) ? value.trim().toLowerCase() : null)

const memberOf = (db, uid) => db.prepare('SELECT uid, email, name, role, joined_at, removed_at FROM members WHERE uid = ?').bind(uid).first()

// -> the member row of this verified user, or a 403. `user` is what verifyIdToken returned.
export async function admit(db, deps, user) {
  const known = await memberOf(db, user.uid)
  if (known && known.removed_at === null) return known

  // An address nobody verified redeems nothing: anybody can register with another person's
  // address. The answer does not say whether an invitation exists.
  const email = user.emailVerified ? cleanEmail(user.email) : null
  if (!email) refuse(403, known ? 'removed' : 'email_not_verified')

  const invitation = await db
    .prepare('SELECT id, role FROM invitations WHERE email = ? AND redeemed_at IS NULL AND revoked_at IS NULL').bind(email).first()
  if (!invitation) refuse(403, known ? 'removed' : 'not_invited')

  // One batch, and each write checks that the invitation is still open, so two accounts that
  // show the same address at the same moment cannot both redeem it.
  const open = 'EXISTS (SELECT 1 FROM invitations WHERE id = ? AND redeemed_at IS NULL AND revoked_at IS NULL)'
  const at = deps.now()
  await db.batch([
    db.prepare(`INSERT INTO members (uid, email, name, role, joined_at, removed_at)
                SELECT ?, ?, ?, ?, ?, NULL WHERE ${open}
                ON CONFLICT (uid) DO UPDATE SET email = excluded.email, role = excluded.role, joined_at = excluded.joined_at,
                  removed_at = NULL, name = COALESCE(members.name, excluded.name)`)
      .bind(user.uid, email, user.name ?? null, invitation.role, at, invitation.id),
    db.prepare(`INSERT INTO events (id, at, actor_uid, action, subject, detail) SELECT ?, ?, ?, 'member.joined', ?, ? WHERE ${open}`)
      .bind(deps.id(), at, user.uid, user.uid, JSON.stringify({ email, role: invitation.role, invitation: invitation.id }), invitation.id),
    db.prepare('UPDATE invitations SET redeemed_at = ?, redeemed_by = ? WHERE id = ? AND redeemed_at IS NULL AND revoked_at IS NULL')
      .bind(at, user.uid, invitation.id),
  ])
  const joined = await memberOf(db, user.uid)
  if (!joined || joined.removed_at !== null) refuse(403, known ? 'removed' : 'not_invited')
  return joined
}

export const requireRole = (member, ...roles) => { if (!roles.includes(member.role)) refuse(403, 'role_not_allowed', { needs: roles }) }

// The name other people see beside a comment. Never the whole address.
export const shownName = (row) => row.name || String(row.email).split('@')[0]

const me = (member) => ({ uid: member.uid, email: member.email, name: member.name, role: member.role })

export async function peopleRoutes(request, env, deps, member, method, path) {
  const db = env.DB

  if (path === '/api/me' && method === 'GET') return json(200, me(member))

  if (path === '/api/me' && method === 'PATCH') {
    const body = await readJson(request)
    const name = typeof body.name === 'string' ? body.name.trim() : ''
    if (name.length < 1 || name.length > 80) refuse(400, 'bad_name')
    await db.prepare('UPDATE members SET name = ? WHERE uid = ?').bind(name, member.uid).run()
    return json(200, me({ ...member, name }))
  }

  if (path === '/api/people' && method === 'GET') {
    requireRole(member, 'owner')
    const members = await db.prepare('SELECT uid, email, name, role, joined_at, removed_at FROM members ORDER BY joined_at, uid').all()
    const invitations = await db
      .prepare('SELECT email, role, invited_by, created_at FROM invitations WHERE redeemed_at IS NULL AND revoked_at IS NULL ORDER BY created_at, id').all()
    return json(200, {
      members: members.results.map((m) => ({ uid: m.uid, email: m.email, name: m.name, role: m.role, joinedAt: m.joined_at, removedAt: m.removed_at })),
      invitations: invitations.results.map((i) => ({ email: i.email, role: i.role, invitedBy: i.invited_by, createdAt: i.created_at })),
    })
  }

  if (path === '/api/invitations' && method === 'POST') {
    requireRole(member, 'owner')
    const body = await readJson(request)
    const email = cleanEmail(body.email)
    if (!email) refuse(400, 'bad_email')
    if (!ROLES.includes(body.role)) refuse(400, 'bad_role', { roles: ROLES })
    const open = await db.prepare('SELECT id FROM invitations WHERE email = ? AND redeemed_at IS NULL AND revoked_at IS NULL').bind(email).first()
    if (open) refuse(409, 'already_invited')
    await db.batch([
      db.prepare('INSERT INTO invitations (email, role, invited_by, created_at) VALUES (?, ?, ?, ?)').bind(email, body.role, member.uid, deps.now()),
      event(db, deps, member.uid, 'invitation.created', email, { role: body.role }),
    ])
    return json(201, { email, role: body.role })
  }

  const invitation = /^\/api\/invitations\/([^/]+)$/.exec(path)
  if (invitation && method === 'DELETE') {
    requireRole(member, 'owner')
    let email = null
    try { email = cleanEmail(decodeURIComponent(invitation[1])) } catch { email = null }
    const open = email && await db.prepare('SELECT id FROM invitations WHERE email = ? AND redeemed_at IS NULL AND revoked_at IS NULL').bind(email).first()
    if (!open) refuse(404, 'no_open_invitation')
    await db.batch([
      db.prepare('UPDATE invitations SET revoked_at = ? WHERE id = ? AND redeemed_at IS NULL AND revoked_at IS NULL').bind(deps.now(), open.id),
      event(db, deps, member.uid, 'invitation.revoked', email),
    ])
    return json(200, { email, revoked: true })
  }

  const removal = /^\/api\/people\/([^/]+)\/remove$/.exec(path)
  if (removal && method === 'POST') {
    requireRole(member, 'owner')
    const target = await memberOf(db, decodeURIComponent(removal[1]))
    if (!target || target.removed_at !== null) refuse(404, 'no_such_member')
    if (target.role === 'owner') {
      const owners = await db.prepare("SELECT COUNT(*) AS n FROM members WHERE role = 'owner' AND removed_at IS NULL").first()
      if (owners.n <= 1) refuse(409, 'last_owner')
    }
    await db.batch([
      db.prepare('UPDATE members SET removed_at = ? WHERE uid = ? AND removed_at IS NULL').bind(deps.now(), target.uid),
      event(db, deps, member.uid, 'member.removed', target.uid, { email: target.email, role: target.role }),
    ])
    return json(200, { uid: target.uid, removed: true })
  }

  return null
}
