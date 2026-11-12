// What a comment is on the Studio screen (specification 4: FBK-1, 2, 4, 5 and SAFE-1, SAFE-4).
//
// No DOM and no network here, so that each rule is a function a test can call. The Studio API
// checks a comment again when it arrives (athlete/studio-api/src/comments.mjs): this module
// makes the mistake visible to the person before that, and the two lists below must stay equal
// to the API's.

export const KINDS = [
  { id: 'looks-wrong', label: 'Looks wrong', hint: 'The picture is wrong: a joint, a foot, the ball.' },
  { id: 'technique-wrong', label: 'Technique is wrong', hint: 'A player must not do it this way.' },
  { id: 'question', label: 'Question', hint: 'You want an answer before you judge it.' },
  { id: 'approve', label: 'Approve', hint: 'This animation is right in this version.' },
]
export const kindLabel = (id) => (id === 'answer' ? 'Answer' : KINDS.find((k) => k.id === id)?.label ?? id)

export const CAMERA_VIEWS = { front: 'Front', side: 'Side', back: 'Back', quarter: '¾ view', free: 'Own angle' }

// The rig's contract bones a coach would name, in the words a coach uses. `ball` is not a bone.
const PART_LABELS = {
  Head: 'Head', neck_01: 'Neck', spine_03: 'Chest', spine_02: 'Mid spine', spine_01: 'Lower spine', pelvis: 'Pelvis',
  upperarm_l: 'Left shoulder', lowerarm_l: 'Left elbow', hand_l: 'Left wrist and hand',
  upperarm_r: 'Right shoulder', lowerarm_r: 'Right elbow', hand_r: 'Right wrist and hand',
  thigh_l: 'Left hip', calf_l: 'Left knee', foot_l: 'Left ankle and foot',
  thigh_r: 'Right hip', calf_r: 'Right knee', foot_r: 'Right ankle and foot',
}
export const BALL = 'ball'

// -> [{ id, label }] for the picker: the parts this version's rig has, then the ball.
export function bodyParts(manifest) {
  const bones = Array.isArray(manifest?.rig?.contractBones) ? manifest.rig.contractBones : []
  return [...Object.keys(PART_LABELS).filter((id) => bones.includes(id)).map((id) => ({ id, label: PART_LABELS[id] })), { id: BALL, label: 'Ball' }]
}
export const bodyPartLabel = (id) => (id === BALL ? 'Ball' : PART_LABELS[id] ?? id)

export function formatTime(seconds) {
  return `${(Math.round(Number(seconds) * 100) / 100).toFixed(2)} s`
}
export const formatRange = (comment) => (comment.tEnd == null ? formatTime(comment.tStart) : `${formatTime(comment.tStart)} to ${formatTime(comment.tEnd)}`)

// The phase the clip is in at `time`: the last one that started at or before it.
export function phaseAt(phases, time) {
  let found = null
  for (const phase of Array.isArray(phases) ? phases : []) {
    if (typeof phase?.time === 'number' && phase.time <= time + 1e-6 && (!found || phase.time >= found.time)) found = phase
  }
  return found?.name ?? null
}

// The clip as the VERSION describes it. A comment is made on that, so a movement Studio builds
// by itself takes no comment. `builtClips` names the ones Studio builds under a clip's own name
// and at its own length (the receive-and-pass sequence, preview-motion.js): the name and the
// length agree with the version, and the movement on screen is not the version's.
export function commentableClip(manifest, clipId, playingSeconds, builtClips = []) {
  const clip = (manifest?.clips ?? []).find((c) => c.id === clipId)
  if (!clip || builtClips.includes(clipId)) return null
  const frame = 1 / (clip.fps > 0 ? clip.fps : 30)
  if (Math.abs(clip.seconds - playingSeconds) > frame) return null
  return { id: clip.id, seconds: clip.seconds, end: clip.seconds + frame }
}

// What the person filled in -> the body of POST /api/comments. Throws an Error a person can read.
export function buildComment({ versionId, clip, kind, body, tStart, tEnd, bodyPart, phase, cameraView, camera, role }) {
  if (!clip) throw new Error('This movement is not an animation of the published version, so it takes no comment.')
  if (!KINDS.some((k) => k.id === kind)) throw new Error('Choose what kind of comment this is.')
  if (kind === 'approve' && role !== 'reviewer') throw new Error('Only a reviewer approves an animation.')
  const text = String(body ?? '').trim()
  if (kind !== 'approve' && !text) throw new Error('Write what you see.')
  if (text.length > 4000) throw new Error('The comment is too long. Keep it under 4000 characters.')
  if (!(Number.isFinite(tStart) && tStart >= 0 && tStart <= clip.end)) throw new Error('The time is outside this animation.')
  if (tEnd != null && !(Number.isFinite(tEnd) && tEnd > tStart && tEnd <= clip.end)) throw new Error('The end of the range must be after its start, inside the animation.')
  const round = (t) => Math.round(t * 1000) / 1000
  return {
    versionId, clipId: clip.id, kind, body: text, tStart: round(tStart),
    ...(tEnd != null ? { tEnd: round(tEnd) } : {}),
    ...(bodyPart ? { bodyPart } : {}), ...(phase ? { phase } : {}),
    ...(cameraView ? { cameraView } : {}), ...(camera ? { camera } : {}),
  }
}

// Comments with their answers under them, oldest first.
export function threads(comments) {
  const top = comments.filter((c) => c.parentId == null).map((c) => ({ ...c, answers: [] }))
  const byId = new Map(top.map((c) => [c.id, c]))
  for (const answer of comments) if (answer.parentId != null) byId.get(answer.parentId)?.answers.push(answer)
  return top
}

// SAFE-4: a comment shows on the timeline of the version it was made on, and nowhere else.
// -> { here: threads on this version, earlier: threads on other versions, newest first }
export function splitByVersion(comments, versionId, clipId) {
  const forClip = threads(comments.filter((c) => c.clipId === clipId))
  return {
    here: forClip.filter((c) => c.versionId === versionId),
    earlier: forClip.filter((c) => c.versionId !== versionId).sort((a, b) => b.createdAt - a.createdAt),
  }
}

// Where each comment sits on the timeline, as fractions of the clip. A range has a width.
export function markers(threadsHere, seconds) {
  if (!(seconds > 0)) return []
  const clamp = (value) => Math.min(1, Math.max(0, value))
  return threadsHere.map((c) => ({
    id: c.id, kind: c.kind, at: clamp(c.tStart / seconds),
    width: c.tEnd == null ? 0 : clamp(c.tEnd / seconds) - clamp(c.tStart / seconds),
    label: `${kindLabel(c.kind)} at ${formatRange(c)}, by ${c.author.name}`,
  }))
}

// SAFE-1: an animation is "approved" only when a reviewer approved it in THIS version. An
// approval of another version, or by somebody who is not a reviewer, says nothing here.
// -> the names of the reviewers who approved, without repeats; empty means not approved.
export function approvers(comments, versionId, clipId) {
  const names = []
  for (const c of comments) {
    if (c.kind === 'approve' && c.versionId === versionId && c.clipId === clipId && c.parentId == null && c.author?.role === 'reviewer'
      && !names.includes(c.author.name)) names.push(c.author.name)
  }
  return names
}

export function approvalText(names) {
  if (!names.length) return 'No reviewer approved this animation in this version.'
  return `Approved in this version by ${names.length === 1 ? names[0] : `${names.slice(0, -1).join(', ')} and ${names.at(-1)}`}.`
}

export const shortVersion = (id) => String(id).slice(0, 8)
