// Hosted Studio on this machine: the development API (dev-server.mjs) and the Studio page from
// vite in hosted mode, as one command. For development and screenshots only.
//
//   node athlete/studio-api/tools/dev-studio.mjs [--port 5399] [--api-port 5398]
//
// The athlete folder and the Tactics checkout come from BRAVEN_ATHLETE_OUTPUT and
// BRAVEN_TACTICS_PATH, or from athlete/viewer/.local/dev-inputs.json (not in git):
//   { "athleteOutput": "...", "tacticsPath": "..." }
// Port 5397 is the local Studio the owner reviews on; this takes 5399 unless told another.
import { spawn } from 'node:child_process'
import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const viewer = path.join(here, '..', '..', 'viewer')
const args = process.argv.slice(2)
const option = (name, fallback) => { const i = args.indexOf(`--${name}`); return i >= 0 ? args[i + 1] : fallback }
const port = option('port', '5399')
const apiPort = option('api-port', '5398')

const inputsFile = path.join(viewer, '.local', 'dev-inputs.json')
const inputs = existsSync(inputsFile) ? JSON.parse(readFileSync(inputsFile, 'utf8')) : {}
const athlete = process.env.BRAVEN_ATHLETE_OUTPUT || inputs.athleteOutput
const tactics = process.env.BRAVEN_TACTICS_PATH || inputs.tacticsPath
if (!athlete || !tactics) {
  console.error(`Set BRAVEN_ATHLETE_OUTPUT and BRAVEN_TACTICS_PATH, or write ${inputsFile}.`)
  process.exit(2)
}

const children = []
const start = (command, commandArgs, options) => {
  const child = spawn(command, commandArgs, { stdio: 'inherit', ...options })
  children.push(child)
  child.on('exit', (code) => { for (const other of children) if (other !== child) other.kill(); process.exit(code ?? 0) })
}
const stop = () => { for (const child of children) child.kill(); process.exit(0) }
process.on('SIGINT', stop)
process.on('SIGTERM', stop)

start(process.execPath, [path.join(here, 'dev-server.mjs'), '--athlete', athlete, '--port', apiPort])
start(process.execPath, [path.join(viewer, 'node_modules', 'vite', 'bin', 'vite.js'), '--host', '127.0.0.1', '--port', port, '--strictPort'], {
  cwd: viewer,
  env: {
    ...process.env, BRAVEN_STUDIO_HOSTED: '1', BRAVEN_TACTICS_PATH: tactics, BRAVEN_STUDIO_API: `http://127.0.0.1:${apiPort}`,
    // The stand-in for the sign-in service, through vite's proxy. vite.config.mjs refuses a BUILD that holds it.
    VITE_DEV_IDENTITY: '/dev-identity', VITE_FIREBASE_API_KEY: 'development-stand-in',
  },
})
