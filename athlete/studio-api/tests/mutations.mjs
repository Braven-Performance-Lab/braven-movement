// Do the tests fail when a guard is taken out? Run by hand: `node tests/mutations.mjs`.
//
// Each entry removes one guard from the source. The run then reads the test runner's own summary
// line: a mutation is killed only when `fail` is above zero and the tests still ran. An exit
// code is not read, because a mutation that breaks the import also exits 1 and proves nothing.
//
// A string must occur exactly once in its file. One that stops being unique, or stops existing,
// is an error here and not a silent pass. This list is the guards somebody thought of: a guard
// with no entry is not covered by a green run.
import { spawnSync } from 'node:child_process'
import { readFileSync, readdirSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..')
const tests = readdirSync(path.join(root, 'tests')).filter((n) => n.endsWith('.test.mjs')).map((n) => path.join('tests', n))

const MUTATIONS = [
  ['a token is not required', 'src/worker.mjs', "if (!verified.ok) return json(401, { error: 'bad_token', reason: verified.reason })", ''],
  ['the algorithm is read from the token', 'src/firebase.mjs', "if (header.alg !== 'RS256')", "if (header.alg === 'none')"],
  ['the signature is not checked', 'src/firebase.mjs', "if (!(await crypto.subtle.verify('RSASSA-PKCS1-v1_5', key, signature, signed)))", 'if (false)'],
  ['any audience is accepted', 'src/firebase.mjs', '|| claims.aud !== projectId)', ')'],
  ['any issuer is accepted', 'src/firebase.mjs', 'if (claims.iss !== `https://securetoken.google.com/${projectId}`)', 'if (false)'],
  ['an expired token is accepted', 'src/firebase.mjs', 'claims.exp + leewaySeconds < seconds', 'false'],
  ['a token from the future is accepted', 'src/firebase.mjs', 'claims.iat - leewaySeconds > seconds', 'false'],
  ['an empty subject is accepted', 'src/firebase.mjs', '|| claims.sub.length === 0', ''],
  ['email_verified is read loosely', 'src/firebase.mjs', 'claims.email_verified === true', 'Boolean(claims.email_verified)'],
  ['unknown key ids refresh without limit', 'src/firebase.mjs', 'this.#now() - this.#lastMissRefreshAt >= KeyStore.MISS_REFRESH_GAP_MS', 'true'],
  ['an unverified address redeems an invitation', 'src/people.mjs', 'user.emailVerified ? cleanEmail(user.email) : null', 'cleanEmail(user.email)'],
  ['a removed member is still admitted', 'src/people.mjs', 'if (known && known.removed_at === null) return known', 'if (known) return known'],
  ['a redeemed invitation is redeemed again', 'src/people.mjs', "WHERE email = ? AND redeemed_at IS NULL AND revoked_at IS NULL').bind(email).first()\n  if (!invitation)", "WHERE email = ? AND revoked_at IS NULL').bind(email).first()\n  if (!invitation)"],
  ['anybody invites', 'src/people.mjs', "if (path === '/api/invitations' && method === 'POST') {\n    requireRole(member, 'owner')", "if (path === '/api/invitations' && method === 'POST') {"],
  ['anybody lists the people', 'src/people.mjs', "if (path === '/api/people' && method === 'GET') {\n    requireRole(member, 'owner')", "if (path === '/api/people' && method === 'GET') {"],
  ['anybody removes a person', 'src/people.mjs', "if (removal && method === 'POST') {\n    requireRole(member, 'owner')", "if (removal && method === 'POST') {"],
  ['any role is invited', 'src/people.mjs', 'if (!ROLES.includes(body.role))', 'if (false)'],
  ['the last owner is removed', 'src/people.mjs', "\n                  AND (role <> 'owner' OR (SELECT COUNT(*) FROM members WHERE role = 'owner' AND removed_at IS NULL) > 1)", ''],
  ['a refused removal is recorded as done', 'src/people.mjs', 'WHERE EXISTS (SELECT 1 FROM members WHERE uid = ? AND removed_at = ?)`', 'WHERE ? IS NOT NULL AND ? IS NOT NULL`'],
  ['anybody revokes an invitation', 'src/people.mjs', "if (invitation && method === 'DELETE') {\n    requireRole(member, 'owner')", "if (invitation && method === 'DELETE') {"],
  ['a member is invited again', 'src/people.mjs', "if (active) refuse(409, 'already_member')", ''],
  ['a change of name leaves no record', 'src/people.mjs', "        event(db, deps, member.uid, 'member.renamed', member.uid, { from: member.name, to: name }),\n", ''],
  ['a bad path in a removal is a server error', 'src/people.mjs', 'try { uid = decodeURIComponent(removal[1]) } catch { uid = null }', 'uid = decodeURIComponent(removal[1])'],
  ['a failed key fetch is repeated on each request', 'src/firebase.mjs', 'if (!(await this.#load())) this.#expiresAt = Math.max(this.#expiresAt, this.#now() + KeyStore.MISS_REFRESH_GAP_MS)', 'await this.#load()'],
  ['a second upload of one manifest fails', 'src/versions.mjs', '      if (first) return json(200, shown(first))\n', ''],
  ['a cut list does not say so', 'src/comments.mjs', 'truncated: rows.results.length > limit', 'truncated: false'],
  ['a cut list keeps the oldest', 'src/comments.mjs', 'ORDER BY c.created_at DESC, c.rowid DESC LIMIT ?', 'ORDER BY c.created_at, c.rowid LIMIT ?'],
  ['a reviewer sees a draft', 'src/versions.mjs', "if (row.state !== 'published' && member.role === 'reviewer') return null", ''],
  ['a reviewer lists drafts', 'src/versions.mjs', "const all = member.role !== 'reviewer'", 'const all = true'],
  ['a reviewer uploads a manifest', 'src/versions.mjs', "if (path === '/api/versions' && method === 'PUT') {\n    requireRole(member, 'author', 'owner')", "if (path === '/api/versions' && method === 'PUT') {"],
  ['a reviewer uploads a file', 'src/versions.mjs', "if (method === 'PUT') requireRole(member, 'author', 'owner')", ''],
  ['an author publishes', 'src/versions.mjs', "requireRole(member, 'owner')\n    const row = await visibleVersion(db, member, publish[1])", "requireRole(member, 'owner', 'author')\n    const row = await visibleVersion(db, member, publish[1])"],
  ['a version with a file missing is published', 'src/versions.mjs', "if (missing.length) refuse(409, 'files_missing', { missing })", ''],
  ['a published version takes a new file', 'src/versions.mjs', "if (row.state === 'published') refuse(409, 'already_published')\n    if (Number(", 'if (Number('],
  ['the bucket is not given the hash', 'src/versions.mjs', 'request.body, { sha256: entry.sha256, httpMetadata', 'request.body, { httpMetadata'],
  ['a master is served', 'src/versions.mjs', "const SERVED_ROLES = ['model', 'library']", "const SERVED_ROLES = ['model', 'library', 'master']"],
  ['another manifest format is accepted', 'src/versions.mjs', "manifest.format !== 'braven-athlete-manifest' || ", ''],
  ['a file name with a path is accepted', 'src/versions.mjs', '!FILE_NAME.test(name) || ', ''],
  ['a file is cached by shared caches', 'src/versions.mjs', "'private, max-age=31536000, immutable'", "'public, max-age=31536000, immutable'"],
  ['an author approves', 'src/comments.mjs', "if (member.role !== 'reviewer') refuse(403, 'only_a_reviewer_approves')", ''],
  ['a reviewer reads comments on a draft', 'src/comments.mjs', "if (member.role === 'reviewer') where.push(\"v.state = 'published'\")", ''],
  ['any kind is accepted', 'src/comments.mjs', "if (!KINDS.includes(input.kind)) bad('kind')", ''],
  ['a clip the version does not have is accepted', 'src/comments.mjs', "if (!clip) bad('clipId')", "if (!clip) return json(201, {})"],
  ['a time past the clip is accepted', 'src/comments.mjs', '|| input.tStart > end)', ')'],
  ['a range past the clip is accepted', 'src/comments.mjs', ' || input.tEnd > end))', '))'],
  ['any body part is accepted', 'src/comments.mjs', "input.bodyPart !== BALL && !bones.includes(input.bodyPart)) bad('bodyPart')", "false) bad('bodyPart')"],
  ['an unknown field is accepted', 'src/comments.mjs', "if (!FIELDS.includes(name)) refuse(400, 'unknown_field'", "if (false) refuse(400, 'unknown_field'"],
  ['an answer to an answer is accepted', 'src/comments.mjs', '|| parent.parent_id !== null', ''],
  ['an empty question is accepted', 'src/comments.mjs', "} else if (text.length === 0) {\n      bad('body')", "} else if (false) {\n      bad('body')"],
  ['a comment is written with no event', 'src/comments.mjs', "    event(db, deps, member.uid, 'comment.created', id, { versionId: row.version_id, clipId: row.clip_id, kind: row.kind }),\n", ''],
  ['a comment can be updated in SQL', 'migrations/0001-review-loop.sql', "CREATE TRIGGER IF NOT EXISTS comments_no_update BEFORE UPDATE ON comments\nBEGIN SELECT RAISE(ABORT, 'comments are append-only'); END;", ''],
  ['a comment can be deleted in SQL', 'migrations/0001-review-loop.sql', "CREATE TRIGGER IF NOT EXISTS comments_no_delete BEFORE DELETE ON comments\nBEGIN SELECT RAISE(ABORT, 'comments are append-only'); END;", ''],
  ['an event can be updated in SQL', 'migrations/0001-review-loop.sql', "CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events\nBEGIN SELECT RAISE(ABORT, 'events are append-only'); END;", ''],
  ['an event can be deleted in SQL', 'migrations/0001-review-loop.sql', "CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events\nBEGIN SELECT RAISE(ABORT, 'events are append-only'); END;", ''],
  ['a published version can change in SQL', 'migrations/0001-review-loop.sql', "CREATE TRIGGER IF NOT EXISTS versions_published_fixed BEFORE UPDATE ON versions\nWHEN OLD.state = 'published'\nBEGIN SELECT RAISE(ABORT, 'a published version does not change'); END;", ''],
  ['a version can be deleted in SQL', 'migrations/0001-review-loop.sql', "CREATE TRIGGER IF NOT EXISTS versions_never_deleted BEFORE DELETE ON versions\nBEGIN SELECT RAISE(ABORT, 'a version is never deleted'); END;", ''],
]

function summary() {
  const run = spawnSync(process.execPath, ['--test', '--test-reporter=spec', ...tests], { cwd: root, encoding: 'utf8' })
  const count = (name) => Number(new RegExp(`^ℹ ${name} (\\d+)$`, 'm').exec(run.stdout)?.[1] ?? NaN)
  return { tests: count('tests'), pass: count('pass'), fail: count('fail') }
}

const clean = summary()
if (!(clean.tests > 0) || clean.fail !== 0) throw new Error(`the unmutated tests must pass first: ${JSON.stringify(clean)}`)
console.log(`unmutated: ${JSON.stringify(clean)}`)

const survivors = []
for (const [name, file, find, replace] of MUTATIONS) {
  const target = path.join(root, file)
  const original = readFileSync(target, 'utf8')
  const source = original.replace(/\r\n/g, '\n')
  const occurrences = source.split(find).length - 1
  if (occurrences !== 1) throw new Error(`"${name}": the string occurs ${occurrences} times in ${file}, and must occur once`)
  let result
  try {
    writeFileSync(target, source.replace(find, replace))
    result = summary()
  } finally {
    writeFileSync(target, original)
  }
  // A whole test file that fails to load counts as one failed test, and the others still run.
  const killed = result.fail > 0 && result.tests >= clean.tests - result.fail
  console.log(`${killed ? 'killed  ' : 'SURVIVED'}  ${name}  ${JSON.stringify(result)}`)
  if (!killed) survivors.push(name)
}
console.log(`${MUTATIONS.length - survivors.length} of ${MUTATIONS.length} mutations killed`)
if (survivors.length) {
  console.log(`survived: ${survivors.join('; ')}`)
  process.exitCode = 1
}
