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
  already_invited: 'This address has an open invitation already.',
  already_member: 'This address is a member already. To change the role, remove the person, then invite the address again.',
  last_owner: 'This is the last owner. Studio must keep one owner.',
  bad_email: 'That does not look like an email address.',
  no_open_invitation: 'That invitation is not open any more. Refresh the list.',
  no_such_member: 'That person is not a member any more. Refresh the list.',
  files_missing: 'This version is not complete: a file is missing. Upload it again.',
  already_published: 'This version is published already. A published version does not change.',
  bad_manifest: 'The server does not accept this manifest. Run the manifest check on the athlete folder.',
}

// What the sign-in screen does after the server did not admit the person:
//   'refused'  the person is signed in and may not come in (no invitation, removed);
//   'sign-in'  the sign-in itself is not good any more, so the person signs in again;
//   'retry'    a server fault or no connection. That says nothing about the person.
export function afterAdmitError(error) {
  if (error?.status === 403) return 'refused'
  if (error?.status === 401) return 'sign-in'
  if (error?.code === 'offline' || error?.status >= 500) return 'retry'
  // A SignInError has no status: the session could not give a token.
  if (error?.status === undefined && typeof error?.code === 'string') return 'sign-in'
  return 'retry'
}

const hex = (buffer) => Array.from(new Uint8Array(buffer), (b) => b.toString(16).padStart(2, '0')).join('')
export const sha256Hex = async (bytes) => hex(await crypto.subtle.digest('SHA-256', bytes))

export function createApi({ session, fetch: fetchImpl = (...a) => globalThis.fetch(...a), base = '/api' }) {
  async function request(method, path, { json, bytes, raw = false } = {}) {
    const token = await session.token()
    let response
    try {
      response = await fetchImpl(base + path, {
        method,
        headers: { authorization: `Bearer ${token}`, ...(json !== undefined ? { 'content-type': 'application/json' } : {}) },
        ...(json !== undefined ? { body: JSON.stringify(json) } : bytes !== undefined ? { body: bytes } : {}),
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
    // The owner's calls. The server checks the role; the page only decides what to offer.
    people: () => request('GET', '/people'),
    invite: (email, role) => request('POST', '/invitations', { json: { email, role } }),
    revoke: (email) => request('DELETE', `/invitations/${encodeURIComponent(email)}`),
    remove: (uid) => request('POST', `/people/${encodeURIComponent(uid)}/remove`),
    publish: (versionId) => request('POST', `/versions/${versionId}/publish`),
    // A version goes up as its manifest, then each file. The server and its bucket check them.
    createVersion: (manifestBytes) => request('PUT', '/versions', { bytes: manifestBytes }),
    async putFile(versionId, name, bytes) {
      try {
        return await request('PUT', `/versions/${versionId}/files/${encodeURIComponent(name)}`, { bytes })
      } catch (error) {
        if (error.code === 'wrong_bytes' || error.code === 'wrong_size') {
          throw new ApiError(error.status, error.code, `${name} is not the file the manifest names. The server did not keep it.`)
        }
        throw error
      }
    },
    addComment: (comment) => request('POST', '/comments', { json: comment }),
    answer: (parentId, body) => request('POST', '/comments', { json: { parentId, body } }),
  }
}
