// The owner's screen of hosted Studio: who may come in, and which athlete version reviewers see
// (specification 4: ACC-2, ACC-3, and ruling 12.6 that a person publishes each version).
//
// The Studio API checks the role on each call. This file only decides what to offer: an owner
// gets people and versions, an author gets versions and the upload, a reviewer gets nothing.
// Text from a person goes in with textContent, never as HTML.
import { shortVersion } from './comments.js'
import { planUpload, sendUpload } from './version-upload.js'

const $ = (id) => document.getElementById(id)
const el = (tag, className, text) => {
  const node = document.createElement(tag)
  if (className) node.className = className
  if (text !== undefined) node.textContent = text
  return node
}
const day = (ms) => new Date(ms).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
const roleLabel = { reviewer: 'Reviewer', author: 'Author', owner: 'Owner' }

export function startTeam(app, { notify }) {
  const { api, me } = app.review
  if (me.role === 'reviewer') return
  const owner = me.role === 'owner'
  $('team-open').hidden = false
  $('team-open').textContent = owner ? 'Team' : 'Versions'
  $('team-title').textContent = owner ? 'Team and versions' : 'Athlete versions'
  $('team-people').hidden = !owner

  const fail = (error) => { $('team-error').textContent = error.message; $('team-error').hidden = false }
  const clear = () => { $('team-error').hidden = true }

  // An act that cannot be undone takes two presses: the first one says what the second does.
  function twoStep(label, confirmLabel, act) {
    const button = el('button', '', label)
    button.type = 'button'
    let armed = false
    let timer
    const disarm = () => { armed = false; button.textContent = label; button.classList.remove('armed') }
    button.onclick = async () => {
      if (!armed) {
        armed = true
        button.textContent = confirmLabel
        button.classList.add('armed')
        clearTimeout(timer)
        timer = setTimeout(disarm, 6000)
        return
      }
      clearTimeout(timer)
      button.disabled = true
      clear()
      try { await act() } catch (error) { fail(error); disarm() } finally { button.disabled = false }
    }
    return button
  }

  function row(title, detail, action) {
    const item = el('li')
    const words = el('div', 'team-words')
    words.append(el('strong', '', title), el('span', '', detail))
    item.append(words)
    if (action) item.append(action)
    return item
  }

  async function load() {
    clear()
    try {
      const { current, versions } = await api.versions()
      $('version-list').replaceChildren(...(versions.length ? versions.map((v) => {
        const published = v.state === 'published'
        const where = v.id === app.versionId ? ' · on your screen now' : ''
        const detail = published
          ? `Published ${day(v.publishedAt)}${v.id === current ? ' · the version reviewers see' : ' · an earlier version'}${where}`
          : `Draft · uploaded ${day(v.createdAt)} · reviewers do not see it`
        const title = `Revision ${v.revision ?? '?'} · ${shortVersion(v.id)}`
        const publish = !published && owner ? twoStep('Publish', 'Press again to publish', async () => {
          await api.publish(v.id)
          await load()
          notify('Version published. Reviewers get it the next time they open Studio. Reload to see it.')
        }) : null
        const item = row(title, detail, publish)
        item.dataset.version = v.id
        item.dataset.state = v.state
        return item
      }) : [el('li', 'team-empty', 'No version is uploaded yet.')]))

      if (!owner) return
      const { members, invitations } = await api.people()
      $('invitation-list').replaceChildren(...(invitations.length ? invitations.map((i) => {
        const item = row(i.email, `${roleLabel[i.role]} · invited ${day(i.createdAt)} · not signed in yet`,
          twoStep('Revoke', 'Press again to revoke', async () => { await api.revoke(i.email); await load() }))
        item.dataset.invitation = i.email
        return item
      }) : [el('li', 'team-empty', 'No invitation is open.')]))
      $('member-list').replaceChildren(...members.map((m) => {
        const gone = m.removedAt !== null
        const detail = `${m.email} · ${roleLabel[m.role]}${gone ? ` · removed ${day(m.removedAt)}` : ` · joined ${day(m.joinedAt)}`}`
        const remove = gone || m.uid === me.uid ? null
          : twoStep('Remove', 'Press again to remove', async () => { await api.remove(m.uid); await load() })
        // A person with no name yet is shown by the address, one time.
        const shown = m.name ? detail : detail.slice(`${m.email} · `.length)
        const item = row(m.name || m.email, m.uid === me.uid ? `${shown} · you` : shown, remove)
        item.dataset.member = m.email
        item.classList.toggle('removed', gone)
        return item
      }))
    } catch (error) {
      fail(error)
    }
  }

  $('invite-form').onsubmit = async (event) => {
    event.preventDefault()
    clear()
    $('invite-send').disabled = true
    try {
      const made = await api.invite($('invite-email').value, $('invite-role').value)
      $('invite-email').value = ''
      await load()
      notify(`${made.email} is invited as ${roleLabel[made.role].toLowerCase()}. Tell them the Studio address.`)
    } catch (error) {
      fail(error)
    } finally {
      $('invite-send').disabled = false
    }
  }

  $('version-choose').onclick = () => $('version-files').click()
  $('version-files').onchange = async () => {
    clear()
    const progress = (text) => { $('version-progress').textContent = text; $('version-progress').hidden = false }
    $('version-choose').disabled = true
    try {
      const plan = await planUpload($('version-files').files)
      const version = await sendUpload(api, plan, progress)
      progress(`Revision ${version.revision ?? '?'} is uploaded as a draft (${shortVersion(version.id)}). ${owner ? 'Publish it in the list above when you are ready.' : 'The owner publishes it.'}`)
      await load()
    } catch (error) {
      $('version-progress').hidden = true
      fail(error)
    } finally {
      $('version-choose').disabled = false
      $('version-files').value = ''
    }
  }

  $('team-open').onclick = () => { $('team-dialog').showModal(); load() }
  $('team-close').onclick = () => $('team-dialog').close()
}
