import { defineConfig } from 'vite'
import path from 'node:path'
import fs from 'node:fs'
import { fileURLToPath } from 'node:url'
import { createHash } from 'node:crypto'
import { acceptAthlete, copyAccepted, readAccepted } from './manifest-gate.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const tactics = path.resolve(process.env.BRAVEN_TACTICS_PATH || path.join(here, '../../../../braven-tactics-netball-athlete'))
// Two builds of one app. Local Studio (the default) serves or copies the checked athlete folder.
// Hosted Studio (BRAVEN_STUDIO_HOSTED=1) holds NO athlete: a signed-in person gets the published
// version through the Studio API (src/athlete-source.js, athlete/studio-api), so its output
// folder is safe to serve to anybody.
const hosted = process.env.BRAVEN_STUDIO_HOSTED === '1'
const assets = process.env.BRAVEN_ATHLETE_OUTPUT
if (!hosted && (!assets || !fs.existsSync(path.join(assets, 'netball-athlete.glb')))) {
  throw new Error('Set BRAVEN_ATHLETE_OUTPUT to the directory containing netball-athlete.glb.')
}
if (!fs.existsSync(path.join(tactics, 'src/engine/skinned.ts'))) throw new Error('Set BRAVEN_TACTICS_PATH to the Tactics checkout.')
// Refuse before anything is served: the model, library, clips and rig must match the manifest.
// Studio then serves only the manifest and the files it lists (manifest-gate.mjs).
const accepted = hosted ? null : acceptAthlete(assets)
function assetMiddleware(req, res, next) {
  const name = (req.url || '').split('?')[0].replace(/^\/athlete-assets\//, '')
  if (!req.url?.startsWith('/athlete-assets/')) return next()
  const entry = accepted.entries.get(name)
  if (!entry) { res.statusCode = 404; res.end('Not a file this athlete\'s manifest lists'); return }
  let data
  try { data = readAccepted(accepted, name) } catch (e) { res.statusCode = 409; res.end(e.message); return }
  res.setHeader('Content-Type', entry.type)
  // The generated model can also be loaded by a separate local Tactics instance.
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Cache-Control', 'no-cache')
  res.setHeader('Content-Length', data.length)
  res.end(data)
}
function buildReceipt(dist, extra) {
  const files={}
  for(const name of ['index.html',...fs.readdirSync(path.join(dist,'assets')).sort().map(n=>'assets/'+n)]) {
    files[name]=createHash('sha256').update(fs.readFileSync(path.join(dist,name))).digest('hex')
  }
  fs.writeFileSync(path.join(dist,'studio-build.json'),JSON.stringify({app:'braven-studio',schemaVersion:1,
    buildId:createHash('sha256').update(JSON.stringify({files,...extra})).digest('hex'),builtAt:new Date().toISOString(),...extra,files},null,2))
}
export default defineConfig(({ command }) => {
  // The local stand-in for the sign-in service is for `vite dev` against the development API
  // only. A build that held it would send a coach's sign-in to an address that is not Firebase.
  if (hosted && command === 'build') {
    if (process.env.VITE_DEV_IDENTITY) throw new Error('VITE_DEV_IDENTITY is set: a hosted build must sign in through Firebase. Unset it.')
    if (!process.env.VITE_FIREBASE_API_KEY) throw new Error('Set VITE_FIREBASE_API_KEY to the Firebase web API key (the public one Braven Tactics ships).')
  }
  return {
    resolve: { alias: { '@tactics': path.join(tactics, 'src'), '@': path.join(tactics, 'src') }, dedupe: ['three'] },
    define: { 'import.meta.env.VITE_STUDIO_MODE': JSON.stringify(hosted ? 'hosted' : 'local') },
    build: { outDir: hosted ? 'dist-hosted' : 'dist' },
    server: { fs: { allow: [here, tactics] },
      // In development the Studio API is a local server (athlete/studio-api/tools/dev-server.mjs).
      ...(hosted ? { proxy: { '/api': process.env.BRAVEN_STUDIO_API || 'http://127.0.0.1:5398', '/dev-identity': process.env.BRAVEN_STUDIO_API || 'http://127.0.0.1:5398' } } : {}) },
    plugins: [{ name: 'athlete-assets', configureServer(server) { if (!hosted) server.middlewares.use(assetMiddleware) },
      closeBundle() {
        if (hosted) {
          const dist = path.join(here, 'dist-hosted')
          // The hosted page is public. It must hold no athlete file, whatever a later change copies.
          if (fs.existsSync(path.join(dist, 'athlete-assets'))) throw new Error('dist-hosted holds athlete-assets: the athlete must leave through the API only.')
          buildReceipt(dist, { mode: 'hosted' })
          return
        }
        const destination = path.join(here, 'dist/athlete-assets')
        copyAccepted(accepted, destination)
        buildReceipt(path.dirname(destination), { assetSha256: accepted.modelSha256 })
      } }],
  }
})
