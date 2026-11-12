// Signing in to hosted Studio, with the account a person has in Braven Tactics.
//
// Firebase's REST endpoints and no SDK, the way Tactics does it (braven-tactics
// src/contract/auth.ts): all this needs is a token and a way to refresh it. The sign-in is by a
// link sent to the person's address, which is also what proves the address is theirs.
//
// The security boundary is not here. The Studio API verifies each token against Google's keys
// and decides who may come in (athlete/studio-api). This module obtains and stores; it never
// decides.
//
// Kept in browser storage: the refresh token, the uid and the email. The ID token stays in
// memory: it lasts an hour.

export const SESSION_KEY = 'braven-studio.session.v1'
export const PENDING_EMAIL_KEY = 'braven-studio.signin.email'
const IDENTITY = 'https://identitytoolkit.googleapis.com/v1'
const SECURE_TOKEN = 'https://securetoken.googleapis.com/v1/token'
const REFRESH_MARGIN_MS = 5 * 60 * 1000

export class SignInError extends Error {
  constructor(code, message) { super(message); this.code = code }
}

const MESSAGES = {
  INVALID_EMAIL: 'That does not look like an email address.',
  INVALID_OOB_CODE: 'This sign-in link was used before or is too old. Ask for a new one.',
  EXPIRED_OOB_CODE: 'This sign-in link is too old. Ask for a new one.',
  INVALID_EMAIL_FOR_LINK: 'This link was sent to a different address. Type the address the mail came to.',
  USER_DISABLED: 'This account is switched off. Ask Braven to check it.',
  TOO_MANY_ATTEMPTS_TRY_LATER: 'Too many tries. Wait a few minutes, then try again.',
  QUOTA_EXCEEDED: 'Too many sign-in mails were sent today. Try again tomorrow.',
  TOKEN_EXPIRED: 'You were signed out. Sign in again.',
  INVALID_REFRESH_TOKEN: 'You were signed out. Sign in again.',
  USER_NOT_FOUND: 'You were signed out. Sign in again.',
}

export function createSession({ apiKey, storage, fetch: fetchImpl = (...a) => globalThis.fetch(...a), now = Date.now,
  identityBase = IDENTITY, tokenUrl = SECURE_TOKEN }) {
  let idToken = null
  let expiresAt = 0
  let refreshing = null

  const read = () => {
    try {
      const value = JSON.parse(storage.getItem(SESSION_KEY) || 'null')
      return value && typeof value.uid === 'string' && typeof value.refreshToken === 'string' ? value : null
    } catch { return null }
  }
  const forget = () => { idToken = null; expiresAt = 0; try { storage.removeItem(SESSION_KEY) } catch { /* nothing to remove */ } }

  async function post(url, body, form = false) {
    let response
    try {
      response = await fetchImpl(`${url}?key=${encodeURIComponent(apiKey)}`, {
        method: 'POST',
        headers: { 'content-type': form ? 'application/x-www-form-urlencoded' : 'application/json' },
        body: form ? new URLSearchParams(body).toString() : JSON.stringify(body),
      })
    } catch {
      throw new SignInError('offline', 'Studio could not reach the sign-in service. Check the connection, then try again.')
    }
    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
      // Firebase answers "CODE" or "CODE : more words".
      const code = String(data?.error?.message || 'unknown').split(/[ :]/)[0]
      throw new SignInError(code, MESSAGES[code] || 'Sign-in did not work. Try again.')
    }
    return data
  }

  const keep = (token, lifetimeSeconds) => { idToken = token; expiresAt = now() + Number(lifetimeSeconds) * 1000 }

  return {
    current() { const s = read(); return s ? { uid: s.uid, email: s.email ?? null } : null },

    pendingEmail() { try { return storage.getItem(PENDING_EMAIL_KEY) } catch { return null } },

    // Ask Firebase to mail a sign-in link that comes back to `continueUrl`.
    async sendLink(email, continueUrl) {
      const address = String(email || '').trim()
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(address)) throw new SignInError('INVALID_EMAIL', MESSAGES.INVALID_EMAIL)
      await post(`${identityBase}/accounts:sendOobCode`, { requestType: 'EMAIL_SIGNIN', email: address, continueUrl, canHandleCodeInApp: true })
      // Firebase needs the address again when the link is used, and the link does not carry it.
      try { storage.setItem(PENDING_EMAIL_KEY, address) } catch { /* the person types it again */ }
    },

    // -> the code in a sign-in link, or null when the address is not one.
    linkCode(href) {
      let url
      try { url = new URL(href) } catch { return null }
      return url.searchParams.get('mode') === 'signIn' ? url.searchParams.get('oobCode') : null
    },

    async completeLink(href, email) {
      const oobCode = this.linkCode(href)
      if (!oobCode) throw new SignInError('INVALID_OOB_CODE', MESSAGES.INVALID_OOB_CODE)
      const address = String(email || this.pendingEmail() || '').trim()
      if (!address) throw new SignInError('email_needed', 'Type the address the sign-in mail came to.')
      const data = await post(`${identityBase}/accounts:signInWithEmailLink`, { email: address, oobCode })
      storage.setItem(SESSION_KEY, JSON.stringify({ uid: data.localId, email: data.email ?? address, refreshToken: data.refreshToken }))
      try { storage.removeItem(PENDING_EMAIL_KEY) } catch { /* nothing to remove */ }
      keep(data.idToken, data.expiresIn)
      return this.current()
    },

    // -> an ID token good for at least five more minutes. Throws SignInError when the person
    // must sign in again; the stored session is then gone.
    async token() {
      const stored = read()
      if (!stored) { idToken = null; throw new SignInError('signed_out', 'Sign in to continue.') }
      if (idToken && now() < expiresAt - REFRESH_MARGIN_MS) return idToken
      // One refresh at a time: each use of a refresh token may replace it.
      refreshing ??= (async () => {
        try {
          const data = await post(tokenUrl, { grant_type: 'refresh_token', refresh_token: stored.refreshToken }, true)
          if (data.refresh_token && data.refresh_token !== stored.refreshToken) {
            storage.setItem(SESSION_KEY, JSON.stringify({ ...stored, refreshToken: data.refresh_token }))
          }
          keep(data.id_token, data.expires_in)
          return idToken
        } catch (error) {
          // No connection is not a reason to sign a person out.
          if (error.code !== 'offline') forget()
          throw error
        } finally {
          refreshing = null
        }
      })()
      return refreshing
    },

    signOut() { forget(); try { storage.removeItem(PENDING_EMAIL_KEY) } catch { /* nothing to remove */ } },
  }
}
