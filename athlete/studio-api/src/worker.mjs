// The Braven Studio Worker: the Studio page, and under /api/ the review loop of specification 4,
// phase A.
//
// The order of a request is the security of it:
//   1. a path outside /api/ is the page, which holds no athlete and no comment;
//   2. /api/health answers anybody;
//   3. each other route needs a Firebase ID token that verifies (firebase.mjs),
//   4. from a person who is a member or holds an open invitation (people.mjs),
//   5. and then the route checks the role.
// The page and the API are one origin, so the API sends no CORS header and reads no cookie: the
// bearer token is the only credential.
import { KeyStore, verifyIdToken } from './firebase.mjs'
import { Refusal, json } from './http.mjs'
import { admit, peopleRoutes } from './people.mjs'
import { versionRoutes } from './versions.mjs'
import { commentRoutes } from './comments.mjs'

const bearer = (request) => /^Bearer\s+(\S+)$/i.exec(request.headers.get('authorization') ?? '')?.[1] ?? null

export async function handle(request, env, deps) {
  const url = new URL(request.url)
  const path = url.pathname
  const method = request.method
  if (path !== '/api' && !path.startsWith('/api/')) return env.ASSETS.fetch(request)

  try {
    if (path === '/api/health' && method === 'GET') return json(200, { ok: true, service: 'braven-studio-api' })

    const token = bearer(request)
    if (!token) return json(401, { error: 'no_token' })
    const verified = await verifyIdToken(token, { projectId: env.FIREBASE_PROJECT_ID, keys: deps.keys, now: deps.now })
    if (!verified.ok) return json(401, { error: 'bad_token', reason: verified.reason })

    const member = await admit(env.DB, deps, verified.user)
    for (const routes of [peopleRoutes, versionRoutes, commentRoutes]) {
      const response = await routes(request, env, deps, member, method, path)
      if (response) return response
    }
    return json(404, { error: 'no_such_route' })
  } catch (error) {
    if (error instanceof Refusal) return json(error.status, { error: error.error, ...error.detail })
    // The cause goes to the Worker log. The caller learns only that it failed.
    console.error('studio-api', method, path, error)
    return json(500, { error: 'internal' })
  }
}

const keys = new KeyStore()

export default {
  fetch: (request, env) => handle(request, env, { keys, now: Date.now, id: () => crypto.randomUUID() }),
}
