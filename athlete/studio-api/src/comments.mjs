// Comments (specification 4: FBK-1, FBK-2, FBK-4, FBK-6, SAFE-1, SAFE-4).
//
// A comment is made on one clip in one version at one time or time range. There is a route to
// add one and a route to read them. There is no route to change or delete one, and the database
// refuses both (migrations/0001). An answer is a new comment under the first.
import { event, json, readJson, refuse } from './http.mjs'
import { shownName } from './people.mjs'
import { visibleVersion } from './versions.mjs'

export const KINDS = ['looks-wrong', 'technique-wrong', 'question', 'approve']
export const CAMERA_VIEWS = ['front', 'side', 'back', 'quarter', 'free']
// The ball is not a bone, and a coach comments on it.
export const BALL = 'ball'
const BODY_LIMIT = 4000
const PER_VERSION_LIMIT = 5000
const FIELDS = ['versionId', 'clipId', 'tStart', 'tEnd', 'kind', 'body', 'bodyPart', 'phase', 'cameraView', 'camera', 'parentId']

const isTime = (value) => typeof value === 'number' && Number.isFinite(value) && value >= 0
const isPoint = (value) => Array.isArray(value) && value.length === 3 && value.every((n) => typeof n === 'number' && Number.isFinite(n))
const optional = (value) => value === undefined || value === null

function shown(row) {
  return {
    id: row.id, versionId: row.version_id, modelSha256: row.model_sha256, clipId: row.clip_id,
    tStart: row.t_start, tEnd: row.t_end, kind: row.kind, body: row.body,
    bodyPart: row.body_part, phase: row.phase, cameraView: row.camera_view,
    camera: row.camera ? JSON.parse(row.camera) : null, parentId: row.parent_id,
    author: { uid: row.author_uid, name: shownName({ name: row.author_name, email: row.author_email }), role: row.author_role },
    createdAt: row.created_at,
  }
}

async function create(request, env, deps, member) {
  const db = env.DB
  const input = await readJson(request)
  for (const name of Object.keys(input)) if (!FIELDS.includes(name)) refuse(400, 'unknown_field', { field: name })
  const bad = (field) => refuse(400, 'bad_comment', { field })

  const text = typeof input.body === 'string' ? input.body.trim() : optional(input.body) ? '' : bad('body')
  if (text.length > BODY_LIMIT) bad('body')

  let row
  if (!optional(input.parentId)) {
    // An answer takes its place from the comment it answers and gives none of its own.
    for (const name of FIELDS) if (!['parentId', 'body'].includes(name) && !optional(input[name])) bad(name)
    const parent = typeof input.parentId === 'string'
      ? await db.prepare('SELECT * FROM comments WHERE id = ?').bind(input.parentId).first() : null
    if (!parent || parent.parent_id !== null) bad('parentId')
    if (!(await visibleVersion(db, member, parent.version_id))) bad('parentId')
    if (text.length === 0) bad('body')
    row = {
      version_id: parent.version_id, model_sha256: parent.model_sha256, clip_id: parent.clip_id, t_start: parent.t_start, t_end: parent.t_end,
      kind: 'answer', body_part: null, phase: null, camera_view: null, camera: null, parent_id: parent.id,
    }
  } else {
    if (!KINDS.includes(input.kind)) bad('kind')
    const version = typeof input.versionId === 'string' ? await visibleVersion(db, member, input.versionId) : null
    if (!version) bad('versionId')
    const manifest = JSON.parse(version.manifest)
    const clip = manifest.clips.find((c) => c.id === input.clipId)
    if (!clip) bad('clipId')
    // A clip plays to its last frame, so one frame past the nominal length is inside it.
    const end = clip.seconds + 1 / (clip.fps > 0 ? clip.fps : 30)
    if (!isTime(input.tStart) || input.tStart > end) bad('tStart')
    if (!optional(input.tEnd) && (!isTime(input.tEnd) || input.tEnd <= input.tStart || input.tEnd > end)) bad('tEnd')
    const bones = Array.isArray(manifest.rig?.contractBones) ? manifest.rig.contractBones : []
    if (!optional(input.bodyPart) && input.bodyPart !== BALL && !bones.includes(input.bodyPart)) bad('bodyPart')
    if (!optional(input.phase) && (typeof input.phase !== 'string' || input.phase.trim().length < 1 || input.phase.length > 80)) bad('phase')
    if (!optional(input.cameraView) && !CAMERA_VIEWS.includes(input.cameraView)) bad('cameraView')
    if (!optional(input.camera) && !(isPoint(input.camera?.position) && isPoint(input.camera?.target))) bad('camera')
    if (input.kind === 'approve') {
      // SAFE-1: "approved" must mean a reviewer approved this version. An author cannot approve
      // the work, and a draft is not what a reviewer saw.
      if (member.role !== 'reviewer') refuse(403, 'only_a_reviewer_approves')
      if (version.state !== 'published') bad('versionId')
    } else if (text.length === 0) {
      bad('body')
    }
    row = {
      version_id: version.id, model_sha256: version.model_sha256, clip_id: clip.id, t_start: input.tStart, t_end: optional(input.tEnd) ? null : input.tEnd,
      kind: input.kind, body_part: input.bodyPart ?? null, phase: optional(input.phase) ? null : input.phase.trim(),
      camera_view: input.cameraView ?? null,
      camera: optional(input.camera) ? null : JSON.stringify({ position: input.camera.position, target: input.camera.target }),
      parent_id: null,
    }
  }

  const count = await db.prepare('SELECT COUNT(*) AS n FROM comments WHERE version_id = ?').bind(row.version_id).first()
  if (count.n >= PER_VERSION_LIMIT) refuse(409, 'too_many_comments', { limit: PER_VERSION_LIMIT })

  const id = deps.id()
  const at = deps.now()
  await db.batch([
    db.prepare(`INSERT INTO comments (id, version_id, model_sha256, clip_id, t_start, t_end, kind, body, body_part, phase,
                  camera_view, camera, parent_id, author_uid, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
      .bind(id, row.version_id, row.model_sha256, row.clip_id, row.t_start, row.t_end, row.kind, text, row.body_part, row.phase,
        row.camera_view, row.camera, row.parent_id, member.uid, at),
    event(db, deps, member.uid, 'comment.created', id, { versionId: row.version_id, clipId: row.clip_id, kind: row.kind }),
  ])
  return json(201, { id, createdAt: at })
}

async function list(request, env, member, limit = PER_VERSION_LIMIT) {
  const db = env.DB
  const query = new URL(request.url).searchParams
  const where = []
  const values = []
  const versionId = query.get('version')
  if (versionId !== null) {
    if (!(await visibleVersion(db, member, versionId))) refuse(404, 'no_such_version')
    where.push('c.version_id = ?')
    values.push(versionId)
  }
  const clipId = query.get('clip')
  if (clipId !== null) {
    where.push('c.clip_id = ?')
    values.push(clipId)
  }
  // ACC-3: a reviewer never sees a draft, so never a comment on one.
  if (member.role === 'reviewer') where.push("v.state = 'published'")
  const rows = await db.prepare(`SELECT c.*, m.name AS author_name, m.email AS author_email, m.role AS author_role
      FROM comments c JOIN versions v ON v.id = c.version_id JOIN members m ON m.uid = c.author_uid
      ${where.length ? `WHERE ${where.join(' AND ')}` : ''} ORDER BY c.created_at DESC, c.rowid DESC LIMIT ?`).bind(...values, limit + 1).all()
  // Read newest first, so that a list that is cut loses the oldest rows, and says that it is
  // cut. Shown oldest first.
  return json(200, { comments: rows.results.slice(0, limit).reverse().map(shown), truncated: rows.results.length > limit })
}

export async function commentRoutes(request, env, deps, member, method, path) {
  if (path !== '/api/comments') return null
  if (method === 'GET') return list(request, env, member, deps.listLimit)
  if (method === 'POST') return create(request, env, deps, member)
  return null
}
