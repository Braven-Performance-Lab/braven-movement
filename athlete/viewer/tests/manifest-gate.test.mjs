import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { checkAthlete } from '../manifest-gate.mjs'

// The gate Studio's config runs before it serves an athlete. The folder is built by the host
// tests' own Folder helper (tests/test_athlete_manifest.py), so Studio and the validator's
// tests use one fixture: a small GLB, a library and a v1 manifest. Nothing here skips.
const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..')
const python = process.env.BRAVEN_PYTHON || 'python'

function folder() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'studio-gate-'))
  const make = spawnSync(python, ['-B', '-c',
    'import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); '
    + 'from test_athlete_manifest import Folder; Folder(Path(sys.argv[2])).write_v1()',
    path.join(repo, 'tests'), dir], { encoding: 'utf8' })
  assert.equal(make.status, 0, make.stderr)
  return dir
}

test('Studio accepts a folder that matches its manifest', () => {
  const dir = folder()
  try {
    const accepted = checkAthlete(dir)
    assert.equal(accepted.accepted, 'athlete-manifest.json')
    assert.match(accepted.model, /^[0-9a-f]{64}$/)
  } finally { fs.rmSync(dir, { recursive: true, force: true }) }
})

test('Studio refuses a library that changed after the manifest was written, and names the code', () => {
  const dir = folder()
  try {
    fs.writeFileSync(path.join(dir, 'movement-library.json'), '{}')
    assert.throws(() => checkAthlete(dir), /Studio refuses the athlete.*REFUSED file:/)
  } finally { fs.rmSync(dir, { recursive: true, force: true }) }
})

test('Studio refuses a build from before the format', () => {
  const dir = folder()
  try {
    fs.rmSync(path.join(dir, 'athlete-manifest.json'))
    assert.throws(() => checkAthlete(dir), /REFUSED format:/)
  } finally { fs.rmSync(dir, { recursive: true, force: true }) }
})

test('Studio says so when it cannot run the check at all', () => {
  assert.throws(() => checkAthlete(os.tmpdir(), { python: 'no-such-python-here' }), /could not run the athlete manifest check/)
})
