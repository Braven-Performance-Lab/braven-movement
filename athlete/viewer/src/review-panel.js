// The comments of hosted Studio: the form, the list, and the markers on the timeline
// (specification 4: FBK-1, 2, 4, 5 and SAFE-1, SAFE-4). The rules are in comments.js; this file
// puts them on the page. Text from a person goes in with textContent, never as HTML.
import { CAMERA_VIEWS, KINDS, approvalText, approvers, bodyPartLabel, bodyParts, buildComment, commentableClip, formatRange, formatTime,
  kindLabel, markers, phaseAt, shortVersion, splitByVersion } from './comments.js'

const $ = (id) => document.getElementById(id)
const el = (tag, className, text) => {
  const node = document.createElement(tag)
  if (className) node.className = className
  if (text !== undefined) node.textContent = text
  return node
}
// "follow_through" -> "Follow through", as the phase buttons show it.
const phaseLabel = (name) => { const words = String(name).replaceAll('_', ' '); return words.charAt(0).toUpperCase() + words.slice(1) }
const when = (ms) => new Date(ms).toLocaleString(undefined, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })

// `app` is window.athleteStudio; `current()` is the catalog entry of the clip on screen;
// `notify(message, isError)` is Studio's own notification.
export function startReview(app, { current, notify, openReviewTab }) {
  const { api, me } = app.review
  const versionId = app.versionId
  const manifest = app.manifest
  let all = []          // every comment the person may see, all clips and versions
  let rangeStart = null // seconds, when the person marked the start of a range
  let shownKey = ''
  let selected = null

  $('comments').hidden = false
  $('version-line').textContent = `Version ${shortVersion(versionId)} · revision ${manifest.asset?.revision ?? '?'}`
  $('version-line').title = `The sha256 of this version's manifest: ${versionId}`

  for (const kind of KINDS) {
    const label = el('label', 'kind-option')
    const input = el('input')
    input.type = 'radio'; input.name = 'comment-kind'; input.value = kind.id
    // SAFE-1: an approval must be a reviewer's. The API refuses any other; the page does not offer it.
    if (kind.id === 'approve' && me.role !== 'reviewer') { input.disabled = true; label.title = 'Only a reviewer approves an animation.' }
    label.append(input, el('span', '', kind.label))
    label.dataset.hint = kind.hint
    $('comment-kinds').append(label)
  }
  $('comment-kinds').onchange = () => {
    const kind = KINDS.find((k) => k.id === pickedKind())
    $('comment-kind-hint').textContent = kind?.hint ?? ''
    $('comment-body').placeholder = kind?.id === 'approve' ? 'Optional: what makes it right?' : 'What do you see at this moment?'
  }
  $('comment-part').append(new Option('Whole body', ''), ...bodyParts(manifest).map((p) => new Option(p.label, p.id)))

  const pickedKind = () => document.querySelector('input[name="comment-kind"]:checked')?.value
  const clip = () => (app.state.driver === 'clips' ? commentableClip(manifest, app.state.clip, app.duration(), app.builtClips) : null)
  const viewName = () => (CAMERA_VIEWS[app.state.view] ? app.state.view : 'free')

  function fillPhases() {
    const phases = current()?.phases ?? []
    const now = phaseAt(phases, rangeStart ?? app.state.time)
    const keep = $('comment-phase').dataset.touched === app.state.clip ? $('comment-phase').value : now ?? ''
    $('comment-phase').replaceChildren(new Option('No phase', ''), ...phases.map((p) => new Option(phaseLabel(p.name), p.name)))
    $('comment-phase').value = keep
    $('comment-phase-row').hidden = !phases.length
  }
  $('comment-phase').onchange = () => { $('comment-phase').dataset.touched = app.state.clip }

  function drawMoment() {
    const time = app.state.time
    if (rangeStart !== null && time > rangeStart + 0.0005) $('comment-moment').textContent = `From ${formatTime(rangeStart)} to ${formatTime(time)}`
    else $('comment-moment').textContent = `At ${formatTime(rangeStart ?? time)}`
    $('comment-range').textContent = rangeStart === null ? 'Start a range here' : 'Back to one moment'
    $('comment-range-hint').hidden = rangeStart === null
    $('comment-view').textContent = `Camera: ${CAMERA_VIEWS[viewName()]}`
    // The phase offered is the one at the START of the comment: a range is named by where it begins.
    if ($('comment-phase').dataset.touched !== app.state.clip) $('comment-phase').value = phaseAt(current()?.phases, rangeStart ?? time) ?? ''
  }
  $('comment-range').onclick = () => { rangeStart = rangeStart === null ? app.state.time : null; drawMoment() }
  $('comment-body').onfocus = () => { if (app.state.playing) app.pause() }

  function commentRow(comment, { onTimeline }) {
    const row = el('article', `comment kind-${comment.kind}`)
    row.dataset.comment = comment.id
    const head = el('header')
    head.append(el('span', 'comment-kind', kindLabel(comment.kind)))
    if (onTimeline) {
      const jump = el('button', 'comment-time', formatRange(comment))
      jump.type = 'button'
      jump.title = 'Go to this moment'
      jump.onclick = () => { app.seek(comment.tStart); select(comment.id) }
      head.append(jump)
    } else head.append(el('span', 'comment-time', formatRange(comment)))
    row.append(head)
    if (comment.body) row.append(el('p', 'comment-body', comment.body))
    const marks = [comment.bodyPart && bodyPartLabel(comment.bodyPart), comment.phase && phaseLabel(comment.phase),
      comment.cameraView && `${CAMERA_VIEWS[comment.cameraView] ?? comment.cameraView} camera`].filter(Boolean)
    if (marks.length) row.append(el('p', 'comment-marks', marks.join(' · ')))
    row.append(el('p', 'comment-by', `${comment.author.name} · ${when(comment.createdAt)}${onTimeline ? '' : ` · version ${shortVersion(comment.versionId)}`}`))
    for (const answer of comment.answers) {
      const reply = el('div', 'comment-answer')
      reply.append(el('p', 'comment-body', answer.body), el('p', 'comment-by', `${answer.author.name} · ${when(answer.createdAt)}`))
      row.append(reply)
    }
    const form = el('form', 'answer-form')
    const input = el('input')
    input.type = 'text'; input.maxLength = 4000; input.placeholder = 'Answer'; input.setAttribute('aria-label', `Answer the comment at ${formatRange(comment)}`)
    const send = el('button', '', 'Answer')
    form.append(input, send)
    form.onsubmit = async (event) => {
      event.preventDefault()
      if (!input.value.trim()) return
      send.disabled = true
      try { await api.answer(comment.id, input.value.trim()); await load(); notify('Answer added.') } catch (error) { notify(error.message, true) } finally { send.disabled = false }
    }
    row.append(form)
    return row
  }

  function select(id) {
    selected = id
    for (const node of document.querySelectorAll('[data-comment]')) node.classList.toggle('selected', node.dataset.comment === id)
    for (const node of document.querySelectorAll('[data-marker]')) node.classList.toggle('selected', node.dataset.marker === id)
  }

  function draw() {
    const target = clip()
    shownKey = `${app.state.driver}/${app.state.clip}`
    $('comment-form').hidden = !target
    $('comment-unavailable').hidden = !!target
    if (!target) {
      $('comment-unavailable').textContent = app.state.driver === 'tactics'
        ? 'A live Tactics preview is not an animation of this version, so it takes no comment. Choose an animation from the library.'
        : 'Studio builds this movement from other animations, so it is not an animation of this version and takes no comment.'
    }
    const { here, earlier } = splitByVersion(all, versionId, app.state.clip)
    const names = approvers(all, versionId, app.state.clip)
    // A movement that takes no comment has no approval to show, and no list.
    $('approval-line').textContent = target ? approvalText(names) : ''
    $('comment-list-heading').hidden = !target && !here.length
    $('approval-line').classList.toggle('approved', names.length > 0)
    $('comment-list').replaceChildren(...here.map((c) => commentRow(c, { onTimeline: true })))
    $('comment-count').textContent = here.length ? `${here.length} on this version` : 'No comments on this version yet'
    $('earlier-comments').hidden = !earlier.length
    $('earlier-summary').textContent = `${earlier.length} on earlier versions`
    $('earlier-list').replaceChildren(...earlier.map((c) => commentRow(c, { onTimeline: false })))
    // FBK-5 and SAFE-4: the timeline shows the comments of the version on screen, and no other.
    const marks = app.state.driver === 'clips' && target ? markers(here, target.seconds) : []
    $('timeline-markers').replaceChildren(...marks.map((m) => {
      const mark = el('button', `marker kind-${m.kind}${m.width ? ' range' : ''}`)
      mark.type = 'button'
      mark.dataset.marker = m.id
      mark.style.setProperty('--at', m.at)
      mark.style.setProperty('--span', m.width)
      mark.title = m.label
      mark.setAttribute('aria-label', m.label)
      mark.onclick = () => {
        app.seek(here.find((c) => c.id === m.id).tStart)
        openReviewTab(); select(m.id)
        document.querySelector(`[data-comment="${m.id}"]`)?.scrollIntoView({ block: 'nearest' })
      }
      return mark
    }))
    $('review-tab-count').textContent = here.length || ''
    $('review-tab-count').hidden = !here.length
    fillPhases(); drawMoment(); select(selected)
  }

  async function load() {
    try {
      const result = await api.comments()
      all = result.comments
      $('comments-truncated').hidden = !result.truncated
      draw()
    } catch (error) {
      notify(`The comments could not be read. ${error.message}`, true)
    }
  }

  $('comment-form').onsubmit = async (event) => {
    event.preventDefault()
    const time = app.state.time
    const ranged = rangeStart !== null && time > rangeStart + 0.0005
    let comment
    try {
      comment = buildComment({
        versionId, clip: clip(), kind: pickedKind(), body: $('comment-body').value, role: me.role,
        tStart: ranged ? rangeStart : rangeStart ?? time, tEnd: ranged ? time : null,
        bodyPart: $('comment-part').value, phase: $('comment-phase').value, cameraView: viewName(), camera: app.captureSetup().camera,
      })
    } catch (error) {
      $('comment-error').textContent = error.message; $('comment-error').hidden = false
      return
    }
    $('comment-error').hidden = true
    $('comment-post').disabled = true
    try {
      const made = await api.addComment(comment)
      $('comment-body').value = ''
      $('comment-part').value = ''
      rangeStart = null
      document.querySelectorAll('input[name="comment-kind"]').forEach((input) => { input.checked = false })
      $('comment-kinds').onchange()
      delete $('comment-phase').dataset.touched
      await load()
      select(made.id)
      notify(comment.kind === 'approve' ? 'Approval recorded for this version.' : 'Comment added. The team can read it.')
    } catch (error) {
      $('comment-error').textContent = error.message; $('comment-error').hidden = false
    } finally {
      $('comment-post').disabled = false
    }
  }
  $('comments-refresh').onclick = load

  // The clip, the playhead and the camera change outside this file: follow them.
  function follow() {
    if (shownKey !== `${app.state.driver}/${app.state.clip}`) { rangeStart = null; selected = null; draw() } else drawMoment()
    requestAnimationFrame(follow)
  }
  load().then(() => requestAnimationFrame(follow))

  return { reload: load, approvedBy: (clipId) => approvers(all, versionId, clipId) }
}
