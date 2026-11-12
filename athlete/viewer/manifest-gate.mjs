import path from 'node:path'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

// Braven Studio serves an athlete only if its folder matches athlete-manifest.json. The check
// is the reference validator in athlete/athlete_manifest.py, run as a process, so Studio,
// the host tests and Tactics' mirror (tools/athlete-manifest.mjs there) refuse the same sets
// with the same codes. A refusal stops the dev server and the build before anything is served.
const here = path.dirname(fileURLToPath(import.meta.url))
const VALIDATOR = path.resolve(here, '..', 'athlete_manifest.py')
export const STUDIO_FAMILY = 'braven-athlete-v6'

export function checkAthlete(folder, { python = process.env.BRAVEN_PYTHON || 'python' } = {}) {
  const run = spawnSync(python, ['-B', VALIDATOR, 'check', folder, '--family', STUDIO_FAMILY], { encoding: 'utf8' })
  if (run.error) throw new Error(`Studio could not run the athlete manifest check: ${run.error.message}`)
  if (run.status !== 0) {
    const reason = (run.stderr || '').trim().split('\n').pop() || `exit ${run.status}`
    throw new Error(`Studio refuses the athlete in ${folder}. ${reason}`)
  }
  return JSON.parse(run.stdout.trim().split('\n').pop())
}
