// Verifying a Firebase ID token: the one part of sign-in that must not be got wrong.
//
// Braven Studio and Braven Tactics trust the same Firebase project, so the uid in a token is the
// same person in the two products (specification 4, ACC-4). This is the check Tactics makes
// (braven-tactics api/src/firebase.ts, read at c8e329d), ported to plain JavaScript and kept
// equal to it on purpose: a difference between the two would mean a token one product accepts
// and the other refuses. It reads fewer claims, because Studio takes roles from its own table.
//
// A Firebase ID token is an RS256 JWT. It is valid when, and only when:
//   - `alg` is exactly RS256: asserted, never read from the token, and never `none`;
//   - the signature verifies against a Google public key that the header's `kid` names;
//   - `aud` is our project id and `iss` is https://securetoken.google.com/<project>, so a token
//     made for another Firebase project is not ours to trust;
//   - `exp` is in the future and `iat` is not;
//   - `sub` is a non-empty string, because that is the uid everything hangs on.
//
// The fetch is a parameter so the tests verify a real signature and never reach Google.

const JWKS_URL = 'https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com'

function fromBase64Url(input) {
  const padded = input.replace(/-/g, '+').replace(/_/g, '/')
  const binary = atob(padded + '='.repeat((4 - (padded.length % 4)) % 4))
  return Uint8Array.from(binary, (c) => c.charCodeAt(0))
}

function decodeJson(part) {
  try {
    const value = JSON.parse(new TextDecoder().decode(fromBase64Url(part)))
    return value && typeof value === 'object' ? value : null
  } catch {
    return null
  }
}

// Google's signing keys, cached for as long as Google says. Google rotates them, and a Worker
// instance can live long enough to see that, so a key id we do not know may send us to look
// again: once a minute at most, or a stream of random key ids is a stream of outbound requests.
export class KeyStore {
  static MISS_REFRESH_GAP_MS = 60_000
  #keys = new Map()
  #expiresAt = 0
  #lastMissRefreshAt = 0
  #fetch
  #url
  #now

  constructor(fetchImpl = (...args) => globalThis.fetch(...args), url = JWKS_URL, now = Date.now) {
    this.#fetch = fetchImpl
    this.#url = url
    this.#now = now
  }

  async get(kid) {
    if (this.#now() >= this.#expiresAt) await this.#refresh()
    if (!this.#keys.has(kid) && this.#now() - this.#lastMissRefreshAt >= KeyStore.MISS_REFRESH_GAP_MS) {
      this.#lastMissRefreshAt = this.#now()
      await this.#refresh()
    }
    return this.#keys.get(kid) ?? null
  }

  async #refresh() {
    let res
    try {
      res = await this.#fetch(this.#url)
    } catch {
      return
    }
    if (!res.ok) return
    const body = await res.json().catch(() => null)
    if (!body || !Array.isArray(body.keys)) return
    const next = new Map()
    for (const jwk of body.keys) {
      if (!jwk || jwk.kty !== 'RSA' || !jwk.kid) continue
      try {
        next.set(jwk.kid, await crypto.subtle.importKey(
          'jwk', { kty: 'RSA', n: jwk.n, e: jwk.e, alg: 'RS256', ext: true },
          { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['verify']))
      } catch {
        // A key we cannot import is a key we do not trust.
      }
    }
    if (next.size === 0) return
    this.#keys = next
    const maxAge = /max-age=(\d+)/.exec(res.headers.get('cache-control') ?? '')?.[1]
    this.#expiresAt = this.#now() + (maxAge ? Number(maxAge) * 1000 : 60 * 60 * 1000)
  }
}

// -> { ok: true, user: { uid, name?, email?, emailVerified } } or { ok: false, reason }
export async function verifyIdToken(token, { projectId, keys, now = Date.now, leewaySeconds = 60 }) {
  const seconds = now() / 1000
  const parts = String(token).split('.')
  if (parts.length !== 3) return { ok: false, reason: 'malformed' }
  const header = decodeJson(parts[0])
  const claims = decodeJson(parts[1])
  if (!header || !claims) return { ok: false, reason: 'malformed' }

  if (header.alg !== 'RS256') return { ok: false, reason: 'unsupported_algorithm' }
  if (typeof header.kid !== 'string') return { ok: false, reason: 'unknown_key' }
  const key = await keys.get(header.kid)
  if (!key) return { ok: false, reason: 'unknown_key' }

  let signature
  try {
    signature = fromBase64Url(parts[2])
  } catch {
    return { ok: false, reason: 'malformed' }
  }
  const signed = new TextEncoder().encode(`${parts[0]}.${parts[1]}`)
  if (!(await crypto.subtle.verify('RSASSA-PKCS1-v1_5', key, signature, signed))) return { ok: false, reason: 'bad_signature' }

  if (typeof projectId !== 'string' || projectId.length === 0 || claims.aud !== projectId) return { ok: false, reason: 'wrong_audience' }
  if (claims.iss !== `https://securetoken.google.com/${projectId}`) return { ok: false, reason: 'wrong_issuer' }
  if (typeof claims.exp !== 'number' || claims.exp + leewaySeconds < seconds) return { ok: false, reason: 'expired' }
  if (typeof claims.iat !== 'number' || claims.iat - leewaySeconds > seconds) return { ok: false, reason: 'not_yet_valid' }
  if (typeof claims.sub !== 'string' || claims.sub.length === 0) return { ok: false, reason: 'no_subject' }

  return {
    ok: true,
    user: {
      uid: claims.sub,
      ...(typeof claims.name === 'string' ? { name: claims.name } : {}),
      ...(typeof claims.email === 'string' ? { email: claims.email } : {}),
      emailVerified: claims.email_verified === true,
    },
  }
}
