// The small things each route needs: a refusal that carries its status, a JSON answer, and a
// body read with a size limit.

export class Refusal extends Error {
  constructor(status, error, detail = {}) {
    super(error)
    this.status = status
    this.error = error
    this.detail = detail
  }
}

export const refuse = (status, error, detail) => { throw new Refusal(status, error, detail) }

const HEADERS = { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', 'x-content-type-options': 'nosniff' }

export const json = (status, body) => new Response(JSON.stringify(body), { status, headers: HEADERS })

// Reads at most `limit` bytes. The declared length is refused first, and the stream is counted
// too, because a declared length is only what the caller says.
export async function readBytes(request, limit) {
  const declared = Number(request.headers.get('content-length'))
  if (Number.isFinite(declared) && declared > limit) refuse(413, 'body_too_large', { limit })
  if (!request.body) return new Uint8Array()
  const reader = request.body.getReader()
  const chunks = []
  let size = 0
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    size += value.byteLength
    if (size > limit) {
      await reader.cancel().catch(() => {})
      refuse(413, 'body_too_large', { limit })
    }
    chunks.push(value)
  }
  const out = new Uint8Array(size)
  let offset = 0
  for (const chunk of chunks) { out.set(chunk, offset); offset += chunk.byteLength }
  return out
}

export async function readJson(request, limit = 64 * 1024) {
  const bytes = await readBytes(request, limit)
  let value
  try {
    value = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes))
  } catch {
    refuse(400, 'bad_json')
  }
  if (!value || typeof value !== 'object' || Array.isArray(value)) refuse(400, 'bad_json')
  return value
}

export async function sha256Hex(bytes) {
  const digest = await crypto.subtle.digest('SHA-256', bytes)
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, '0')).join('')
}

// One row in `events`, as a statement to put in the same batch as the act it records, so that
// an act and its record are written together or not at all.
export const event = (db, deps, actorUid, action, subject, detail) => db
  .prepare('INSERT INTO events (id, at, actor_uid, action, subject, detail) VALUES (?, ?, ?, ?, ?, ?)')
  .bind(deps.id(), deps.now(), actorUid, action, String(subject), detail === undefined ? null : JSON.stringify(detail))
