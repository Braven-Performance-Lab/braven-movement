// The sign-in screen of hosted Studio (specification 4: ACC-2). It covers the app until a
// person is signed in AND the Studio API admits them. There is no sign-up here: an address with
// no invitation is told so, and nothing of the athlete is loaded.
import { createSession } from './session.js'
import { afterAdmitError, createApi } from './review-api.js'

const $ = (id) => document.getElementById(id)

function show(stage, message = '', isError = false) {
  $('signin').hidden = false
  for (const name of ['ask', 'sent', 'confirm', 'busy', 'refused']) $(`signin-${name}`).hidden = name !== stage
  const note = $(`signin-${stage}-note`)
  if (note) { note.textContent = message; note.classList.toggle('error', isError); note.hidden = !message }
}

const roleLabel = { reviewer: 'Reviewer', author: 'Author', owner: 'Owner' }

// -> { session, api, me } once a person is signed in and admitted. Never rejects for a refusal a
// person can fix on this screen: it stays on the screen.
export function signIn() {
  let storage
  try { storage = window.localStorage } catch { storage = null }
  if (!storage) {
    show('refused', 'This browser does not let Studio keep a sign-in. Allow site data for this address, then reload.', true)
    return new Promise(() => {})
  }
  const session = createSession({
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY, storage,
    // A local development server stands in for the sign-in service: never set in a deploy.
    ...(import.meta.env.VITE_DEV_IDENTITY ? { identityBase: import.meta.env.VITE_DEV_IDENTITY, tokenUrl: `${import.meta.env.VITE_DEV_IDENTITY}/token` } : {}),
  })
  const api = createApi({ session })
  const home = `${location.origin}${location.pathname}`

  return new Promise((resolve) => {
    async function admit() {
      show('busy', 'Checking your access…')
      try {
        const me = await api.me()
        $('signin').hidden = true
        $('account').hidden = false
        $('account-name').textContent = me.name || me.email
        $('account-role').textContent = roleLabel[me.role] || me.role
        resolve({ session, api, me })
      } catch (error) {
        const next = afterAdmitError(error)
        if (next === 'sign-in') {
          session.signOut()
          show('ask', error.message, true)
        } else {
          // Refused, or a fault that says nothing about the person: they stay signed in.
          $('signin-refused-title').textContent = next === 'refused' ? 'You cannot come in yet' : 'Studio could not check your access'
          $('signin-refused-address').textContent = session.current()?.email || ''
          show('refused', next === 'refused' || error.code === 'offline' ? error.message : 'The Studio server has a fault. Your sign-in is kept. Try again in a minute.', true)
        }
      }
    }

    async function useLink(email) {
      show('busy', 'Signing you in…')
      try {
        await session.completeLink(location.href, email)
        // The code works one time. It leaves the address bar so that a reload does not try it again.
        history.replaceState(null, '', home)
        await admit()
      } catch (error) {
        if (error.code === 'email_needed' || error.code === 'INVALID_EMAIL_FOR_LINK') show('confirm', error.code === 'email_needed' ? '' : error.message, true)
        else { history.replaceState(null, '', home); show('ask', error.message, true) }
      }
    }

    $('signin-form').onsubmit = async (event) => {
      event.preventDefault()
      const email = $('signin-email').value
      $('signin-send').disabled = true
      try {
        await session.sendLink(email, home)
        $('signin-sent-address').textContent = email.trim()
        show('sent')
      } catch (error) {
        show('ask', error.message, true)
      } finally {
        $('signin-send').disabled = false
      }
    }
    $('signin-confirm-form').onsubmit = (event) => { event.preventDefault(); useLink($('signin-confirm-email').value) }
    $('signin-again').onclick = () => show('ask')
    $('signin-retry').onclick = admit
    for (const id of ['signin-other', 'sign-out']) $(id).onclick = () => { session.signOut(); location.assign(home) }

    if (session.linkCode(location.href)) useLink()
    else if (session.current()) admit()
    else show('ask')
  })
}
