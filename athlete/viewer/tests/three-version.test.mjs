import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import * as THREE from 'three'
import { RENDERER_SETTINGS } from '../src/render-settings.js'

// The viewer runs on three.js r187 (Main's goal, 13 November 2026; THREE-R187.md).
// These read the version three.js reports and the settings the page uses, not the
// text of the source: a pin in package.json alone can disagree with what is installed.
const viewer = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const json = name => JSON.parse(fs.readFileSync(path.join(viewer, name), 'utf8'))

test('package.json pins three.js at exactly 0.187.0', () => {
  assert.equal(json('package.json').dependencies.three, '0.187.0')
})

test('the lock file installs three.js 0.187.0', () => {
  assert.equal(json('package-lock.json').packages['node_modules/three'].version, '0.187.0')
})

test('the installed three.js reports revision 187', () => {
  assert.equal(THREE.REVISION, '187')
})

test('the renderer uses PCFShadowMap, which r182 made soft, not the deprecated PCFSoftShadowMap', () => {
  assert.equal(RENDERER_SETTINGS.shadowMapType, THREE.PCFShadowMap)
  assert.notEqual(RENDERER_SETTINGS.shadowMapType, THREE.PCFSoftShadowMap)
})

test('the other renderer settings are the ones the owner has seen', () => {
  assert.equal(RENDERER_SETTINGS.toneMapping, THREE.ACESFilmicToneMapping)
  assert.equal(RENDERER_SETTINGS.toneMappingExposure, 1.0)
  assert.equal(RENDERER_SETTINGS.maxPixelRatio, 2)
  assert.deepEqual(RENDERER_SETTINGS.contextAttributes, { antialias: true, preserveDrawingBuffer: true })
})
