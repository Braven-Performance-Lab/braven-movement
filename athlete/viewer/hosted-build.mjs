// The two rules of a hosted Studio build, as functions a test calls (vite.config.mjs runs them).
//
// The hosted page is public, and a coach signs in on it. So a build must sign in through
// Firebase and nothing else, and its output folder must hold no athlete file: the athlete
// leaves through the Studio API only, behind the sign-in.
import fs from 'node:fs'
import path from 'node:path'

// `env` is everything the build can see: the shell AND the .env files vite reads. The stand-in
// for the sign-in service is for `vite dev` against the development API; a build that held it
// would send a coach's sign-in to an address that is not Firebase.
export function checkHostedBuild(env) {
  if (env.VITE_DEV_IDENTITY) {
    throw new Error('VITE_DEV_IDENTITY is set (in the shell or in a .env file): a hosted build must sign in through Firebase. Remove it.')
  }
  if (!env.VITE_FIREBASE_API_KEY) {
    throw new Error('Set VITE_FIREBASE_API_KEY to the Firebase web API key (the public one Braven Tactics ships).')
  }
  if (env.VITE_FIREBASE_API_KEY === 'development-stand-in') {
    throw new Error('VITE_FIREBASE_API_KEY holds the development stand-in, not the Firebase web API key.')
  }
}

const ATHLETE_FILE = /\.(glb|gltf|blend)$|^athlete-manifest\.json$|^movement-library\.json$/i

// Refuses an output folder with an athlete file in it, by what the file is and not by where a
// later change happens to copy it.
export function checkHostedOutput(dist) {
  if (fs.existsSync(path.join(dist, 'athlete-assets'))) {
    throw new Error(`${dist} holds athlete-assets: the athlete must leave through the API only.`)
  }
  const walk = (folder) => {
    for (const entry of fs.readdirSync(folder, { withFileTypes: true })) {
      const full = path.join(folder, entry.name)
      if (entry.isDirectory()) walk(full)
      else if (ATHLETE_FILE.test(entry.name)) throw new Error(`${dist} holds an athlete file (${path.relative(dist, full)}): the athlete must leave through the API only.`)
    }
  }
  walk(dist)
}
