// Do the review tests fail when a guard is taken out of the client? Run by hand:
// `node tests/review-mutations.mjs`.
//
// The same instrument as athlete/studio-api/tests/mutations.mjs: one guard out at a time, and
// the test runner's own summary line is read, never the exit code. A string must occur exactly
// once in its file. The list is the guards somebody thought of, and no more than that.
import { spawnSync } from 'node:child_process'
import { readFileSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..')

const MUTATIONS = [
  ['a file with other bytes is loaded', 'src/review-api.js', 'if (actual !== expectedSha256) {', 'if (false) {'],
  ['the manifest is not tied to the version id', 'src/review-api.js', "await file(versionId, 'athlete-manifest.json', versionId)", "await file(versionId, 'athlete-manifest.json', await sha256Hex(new Uint8Array()))"],
  ['a call goes out with no token', 'src/review-api.js', 'authorization: `Bearer ${token}`, ', ''],
  ['the ID token is written to storage', 'src/session.js', "refreshToken: data.refreshToken }))\n      try { storage.removeItem(PENDING_EMAIL_KEY)", "refreshToken: data.refreshToken, idToken: data.idToken }))\n      try { storage.removeItem(PENDING_EMAIL_KEY)"],
  ['a lost connection signs the person out', 'src/session.js', "if (error.code !== 'offline') forget()", 'forget()'],
  ['a refused refresh keeps the session', 'src/session.js', "if (error.code !== 'offline') forget()", ''],
  ['each waiting caller refreshes', 'src/session.js', 'refreshing ??= (async', 'refreshing = (async'],
  ['a replaced refresh token is dropped', 'src/session.js', 'if (data.refresh_token && data.refresh_token !== stored.refreshToken) {', 'if (false) {'],
  ['any link is a sign-in link', 'src/session.js', "url.searchParams.get('mode') === 'signIn' ? ", 'true ? '],
  ['the address of a link is guessed', 'src/session.js', "if (!address) throw new SignInError('email_needed'", "if (false) throw new SignInError('email_needed'"],
  ['an approval by an author counts', 'src/comments.js', " && c.author?.role === 'reviewer'", ''],
  ['an approval of another version counts', 'src/comments.js', "c.kind === 'approve' && c.versionId === versionId && ", "c.kind === 'approve' && "],
  ['an approval of another clip counts', 'src/comments.js', ' && c.clipId === clipId && c.parentId == null', ' && c.parentId == null'],
  ['a comment shows on another version', 'src/comments.js', 'here: forClip.filter((c) => c.versionId === versionId),', 'here: forClip,'],
  ['a sequence Studio builds takes a comment', 'src/comments.js', 'if (Math.abs(clip.seconds - playingSeconds) > frame) return null', ''],
  ['a clip the version does not have takes a comment', 'src/comments.js', 'if (!clip) return null', "if (!clip) return { id: clipId, seconds: playingSeconds, end: playingSeconds }"],
  ['an author can build an approval', 'src/comments.js', "if (kind === 'approve' && role !== 'reviewer')", 'if (false)'],
  ['a time past the clip is built', 'src/comments.js', ' && tStart <= clip.end))', '))'],
  ['an empty comment is built', 'src/comments.js', "if (kind !== 'approve' && !text)", 'if (false)'],
  ['a marker leaves the timeline', 'src/comments.js', 'const clamp = (value) => Math.min(1, Math.max(0, value))', 'const clamp = (value) => value'],
]

function summary() {
  const run = spawnSync(process.execPath, ['--test', '--test-reporter=spec', 'tests/review.test.mjs'], { cwd: root, encoding: 'utf8' })
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
  // All the tests still ran, and at least one failed: a file that no longer loads is not a kill.
  const killed = result.fail > 0 && result.tests === clean.tests
  console.log(`${killed ? 'killed  ' : 'SURVIVED'}  ${name}  ${JSON.stringify(result)}`)
  if (!killed) survivors.push(name)
}
console.log(`${MUTATIONS.length - survivors.length} of ${MUTATIONS.length} mutations killed`)
if (survivors.length) {
  console.log(`survived: ${survivors.join('; ')}`)
  process.exitCode = 1
}
