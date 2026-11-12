import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { acceptAthlete, checkAthlete, copyAccepted, readAccepted } from '../manifest-gate.mjs'

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

test('Studio serves the checked manifest and the files it lists, and nothing else', () => {
  const dir = folder()
  try {
    const accepted = acceptAthlete(dir)
    assert.deepEqual([...accepted.entries.keys()].sort(),
      ['athlete-manifest.json', 'movement-library.json', 'netball-athlete.blend', 'netball-athlete.glb'])
    assert.ok(fs.existsSync(path.join(dir, 'manifest.json')), 'the legacy manifest is in the folder')
    assert.throws(() => readAccepted(accepted, 'manifest.json'), /not a file this athlete's manifest lists/)
    assert.equal(readAccepted(accepted, 'netball-athlete.blend').toString(), 'master')
  } finally { fs.rmSync(dir, { recursive: true, force: true }) }
})

test('Studio refuses to serve a file that changed after it checked the athlete', () => {
  const dir = folder()
  try {
    const accepted = acceptAthlete(dir)
    fs.writeFileSync(path.join(dir, 'netball-athlete.blend'), 'MASTER')
    assert.throws(() => readAccepted(accepted, 'netball-athlete.blend'), /changed after Studio checked/)
  } finally { fs.rmSync(dir, { recursive: true, force: true }) }
})

test('a build copies only the listed files, removes what an earlier build left, and checks every copy', () => {
  const dir = folder()
  const out = fs.mkdtempSync(path.join(os.tmpdir(), 'studio-dist-'))
  try {
    fs.writeFileSync(path.join(out, 'manifest.json'), '{"left":"by an earlier build"}')
    copyAccepted(acceptAthlete(dir), out)
    assert.deepEqual(fs.readdirSync(out).sort(),
      ['athlete-manifest.json', 'movement-library.json', 'netball-athlete.blend', 'netball-athlete.glb'])
    assert.equal(fs.readFileSync(path.join(out, 'netball-athlete.blend')).toString(), 'master')
  } finally { fs.rmSync(dir, { recursive: true, force: true }); fs.rmSync(out, { recursive: true, force: true }) }
})

test('a build refuses when the manifest changed between start-up and the copy', () => {
  const dir = folder()
  const out = fs.mkdtempSync(path.join(os.tmpdir(), 'studio-dist-'))
  try {
    const accepted = acceptAthlete(dir)
    const manifestPath = path.join(dir, 'athlete-manifest.json')
    const m = JSON.parse(fs.readFileSync(manifestPath, 'utf8')); m.kit.id = 'another-kit'
    fs.writeFileSync(manifestPath, JSON.stringify(m))
    assert.throws(() => copyAccepted(accepted, out), /manifest changed during the build/)
  } finally { fs.rmSync(dir, { recursive: true, force: true }); fs.rmSync(out, { recursive: true, force: true }) }
})

test('a build refuses a listed file that changed after start-up, even with the manifest unchanged', () => {
  const dir = folder()
  const out = fs.mkdtempSync(path.join(os.tmpdir(), 'studio-dist-'))
  try {
    const accepted = acceptAthlete(dir)
    fs.writeFileSync(path.join(dir, 'netball-athlete.blend'), 'MASTER')
    assert.throws(() => copyAccepted(accepted, out), /Studio refuses the athlete.*REFUSED file:/)
  } finally { fs.rmSync(dir, { recursive: true, force: true }); fs.rmSync(out, { recursive: true, force: true }) }
})

test('Studio says so when it cannot run the check at all', () => {
  assert.throws(() => checkAthlete(os.tmpdir(), { python: 'no-such-python-here' }), /could not run the athlete manifest check/)
})
