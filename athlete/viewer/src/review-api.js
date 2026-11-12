// The Studio API as the Studio page calls it (athlete/studio-api). One origin: the page and the
// API are served by the same Worker, so the address is a path.

export class ApiError extends Error {
  constructor(status, code, message) { super(message); this.status = status; this.code = code }
}

const MESSAGES = {
  not_invited: 'This address has no invitation to Braven Studio. Ask Braven for one, then sign in again.',
  email_not_verified: 'Your address is not confirmed. Sign in with the link from the sign-in mail.',
  removed: 'Your access to Braven Studio was removed. Ask Braven if that is a mistake.',
  only_a_reviewer_approves: 'Only a reviewer approves an animation.',
  role_not_allowed: 'Your role does not allow that.',
  too_many_comments: 'This version has too many comments to add one more.',
}

const hex = (buffer) => Array.from(new Uint8Array(buffer), (b) => b.toString(16).padStart(2, '0')).join('')
export const sha256Hex = async (bytes) => hex(await crypto.subtle.digest('SHA-256', bytes))

export function createApi({ session, fetch: fetchImpl = (...a) => globalThis.fetch(...a), base = '/api' }) {
  async function request(method, path, { json, raw = false } = {}) {
    const token = await session.token()
    let response
    try {
      response = await fetchImpl(base + path, {
        method,
        headers: { authorization: `Bearer ${token}`, ...(json !== undefined ? { 'content-type': 'application/json' } : {}) },
        ...(json !== undefined ? { body: JSON.stringify(json) } : {}),
      })
    } catch {
      throw new ApiError(0, 'offline', 'Studio could not reach its server. Check the connection, then try again.')
    }
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      const code = body.error || `http_${response.status}`
      throw new ApiError(response.status, code, MESSAGES[code] || (response.status === 401 ? 'Your sign-in is no longer good. Sign in again.'
        : `The server refused that (${code}${body.field ? `: ${body.field}` : ''}).`))
    }
    return raw ? response : response.json()
  }

  // A file of a version, checked against the hash it must have. Bytes that do not match are
  // never handed on: a model that is not the published one is not shown as if it were.
  async function file(versionId, name, expectedSha256, onProgress) {
    const response = await request('GET', `/versions/${versionId}/files/${encodeURIComponent(name)}`, { raw: true })
    const total = Number(response.headers.get('content-length')) || 0
    const chunks = []
    let loaded = 0
    if (response.body?.getReader) {
      const reader = response.body.getReader()
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        chunks.push(value)
        loaded += value.byteLength
        onProgress?.(loaded, total)
      }
    } else {
      chunks.push(new Uint8Array(await response.arrayBuffer()))
      loaded = chunks[0].byteLength
    }
    const bytes = new Uint8Array(loaded)
    let offset = 0
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength }
    const actual = await sha256Hex(bytes)
    if (actual !== expectedSha256) {
      throw new ApiError(0, 'wrong_bytes', `${name} is not the file this version names. Studio did not load it. Reload the page; if this stays, tell Braven.`)
    }
    return bytes
  }

  return {
    me: () => request('GET', '/me'),
    setName: (name) => request('PATCH', '/me', { json: { name } }),
    versions: () => request('GET', '/versions'),
    file,
    // The manifest IS the version: its sha256 is the version id.
    async manifest(versionId) {
      const bytes = await file(versionId, 'athlete-manifest.json', versionId)
      return JSON.parse(new TextDecoder().decode(bytes))
    },
    comments: ({ versionId, clipId } = {}) => {
      const query = new URLSearchParams()
      if (versionId) query.set('version', versionId)
      if (clipId) query.set('clip', clipId)
      return request('GET', `/comments?${query}`)
    },
    addComment: (comment) => request('POST', '/comments', { json: comment }),
    answer: (parentId, body) => request('POST', '/comments', { json: { parentId, body } }),
  }
}
