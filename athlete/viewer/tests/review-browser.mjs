/**
 * The review loop in a real browser, against hosted Studio on this machine.
 *
 * Start a FRESH development server first, then run this:
 *   node athlete/studio-api/tools/dev-studio.mjs --port 5399
 *   node tests/review-browser.mjs
 *
 * It uses the Tactics checkout's puppeteer-core and local Chrome, as tests/studio-browser.mjs
 * does. The sign-in service and the API are the development stand-ins (dev-server.mjs): this
 * proves the page, not Firebase, D1 or R2. Screenshots and screens.json go to the ignored
 * verification/review/. screens.json names the commit, and is written only from a clean tree.
 */
import { createRequire } from 'node:module'
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'

const require = createRequire(path.join(process.env.BRAVEN_TACTICS_PATH || 'F:/Repositories/braven-tactics-netball-athlete', 'package.json'))
const puppeteer = require('puppeteer-core')
const url = process.env.STUDIO_URL || 'http://127.0.0.1:5399/'
const out = path.resolve('verification/review')
fs.rmSync(out, { recursive: true, force: true })
fs.mkdirSync(out, { recursive: true })

const browser = await puppeteer.launch({
  executablePath: process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  headless: true, defaultViewport: { width: 1440, height: 900 },
})
const page = await browser.newPage()
const errors = []
const requests = []
const checks = []
const shots = []
page.on('pageerror', (error) => errors.push(String(error)))
page.on('request', (request) => requests.push({ method: request.method(), url: request.url(), body: request.postData() }))

const check = (name, value) => { assert(value, name); checks.push(name) }
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))
const text = (selector) => page.$eval(selector, (el) => el.textContent)
const visible = (selector) => page.$eval(selector, (el) => !el.hidden && el.getClientRects().length > 0)
const shot = async (file, screen) => { await page.screenshot({ path: path.join(out, `${file}.png`) }); shots.push({ file: `${file}.png`, screen }) }
const asked = (part) => requests.filter((r) => r.url.includes(part))

async function askForLink(email) {
  await page.waitForSelector('#signin-email', { visible: true })
  await page.$eval('#signin-email', (el) => { el.value = '' })
  await page.type('#signin-email', email)
  await page.click('#signin-send')
  await page.waitForSelector('#signin-sent:not([hidden])')
}
async function followLink(email) {
  const { link } = await (await fetch(`${url}dev-identity/last-link?email=${encodeURIComponent(email)}`)).json()
  await page.goto(link)
}
async function signInAs(email) {
  await askForLink(email)
  await followLink(email)
  await page.waitForFunction(() => !!window.bravenStudio, { timeout: 60000 })
  await page.click('[data-tab="review"]')
  await page.waitForFunction(() => document.getElementById('comment-count').textContent !== '' && !document.getElementById('comments').hidden)
}
async function post({ kind, body, at, to, part }) {
  await page.evaluate((t) => window.athleteStudio.seek(t), at)
  await wait(80)
  if (to) { await page.click('#comment-range'); await page.evaluate((t) => window.athleteStudio.seek(t), to); await wait(80) }
  await page.click(`input[name="comment-kind"][value="${kind}"]`)
  if (body) await page.type('#comment-body', body)
  if (part) await page.select('#comment-part', part)
  const before = await page.$$eval('#comment-list .comment', (els) => els.length)
  await page.click('#comment-post')
  await page.waitForFunction((n) => document.querySelectorAll('#comment-list .comment').length === n + 1, {}, before)
  await page.$eval('#notification', (el) => { el.hidden = true })
}

try {
  // ---- nobody is signed in
  await page.goto(url, { waitUntil: 'networkidle0' })
  check('With nobody signed in, the sign-in screen covers Studio', await visible('#signin-ask'))
  check('Before sign-in no athlete and no comment is asked for', asked('/api/').length === 0 && asked('athlete-assets').length === 0
    && await page.evaluate(() => window.athleteStudio === undefined))
  check('There is no sign-up and no password field', await page.$$eval('#signin input', (els) => els.every((el) => el.type === 'email')))
  await shot('01-sign-in', 'Sign-in: the address the invitation was sent to')

  // ---- an address with no invitation
  await askForLink('stranger@example.org')
  check('The person is told where the link went', (await text('#signin-sent-address')) === 'stranger@example.org')
  await shot('02-sign-in-link-sent', 'Sign-in: the link is on its way')
  await followLink('stranger@example.org')
  await page.waitForSelector('#signin-refused:not([hidden])')
  check('An address with no invitation is refused in words, and Studio does not load',
    /no invitation/.test(await text('#signin-refused-note')) && await page.evaluate(() => window.athleteStudio === undefined)
    && asked('/api/versions').length === 0)
  check('The sign-in code leaves the address bar', !page.url().includes('oobCode'))
  await shot('03-not-invited', 'Sign-in: an address with no invitation')
  await page.click('#signin-other')
  await page.waitForSelector('#signin-ask:not([hidden])')
  check('Using another address forgets the refused sign-in', await page.evaluate(() => localStorage.getItem('braven-studio.session.v1') === null))

  // ---- a reviewer
  await signInAs('coach@braven.test')
  check('The reviewer is in, with name and role in the header', (await text('#account-name')) === 'Coach (development)' && (await text('#account-role')) === 'Reviewer')
  check('The published version came through the API, named by its hash, and nothing came from a static folder',
    await page.evaluate(() => /^[0-9a-f]{64}$/.test(window.athleteStudio.versionId) && window.athleteStudio.bones.size === 70)
    && asked('athlete-assets').length === 0 && asked('/files/athlete-manifest.json').length === 1)
  check('The ID token is not kept in browser storage', await page.evaluate(() => !Object.values(localStorage).some((v) => /eyJ[A-Za-z0-9_-]+\.eyJ/.test(v))))
  check('Hosted Studio offers no download the version does not serve', (await page.$$('a[download]')).length === 0)
  check('Hosted Studio fits the desktop width', await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
  check('This run starts on a fresh server', (await text('#comment-count')) === 'No comments on this version yet')
  check('Nothing is shown as approved before a reviewer approves it',
    (await text('#approval-line')) === 'No reviewer approved this animation in this version.' && !(await page.$eval('#approval-line', (el) => el.classList.contains('approved'))))
  await shot('04-review-no-comments', 'Review tab: an animation with no comments, not approved')

  await post({ kind: 'looks-wrong', body: 'The left knee stays straight when she steps. It must bend into the step.', at: 0.62, part: 'calf_l' })
  const sent = JSON.parse(asked('/api/comments').filter((r) => r.method === 'POST').at(-1).body)
  check('A comment carries the version, the animation, the time, the kind, the body part, the phase and the camera view',
    sent.versionId === await page.evaluate(() => window.athleteStudio.versionId) && sent.clipId === 'netball_chest_pass' && sent.tStart === 0.62
    && sent.kind === 'looks-wrong' && sent.bodyPart === 'calf_l' && typeof sent.phase === 'string' && sent.cameraView === 'quarter'
    && sent.camera.position.length === 3)
  await post({ kind: 'question', body: 'Is the ball this far from the chest through the whole drive?', at: 0.85, to: 1.15, part: 'ball' })
  const ranged = JSON.parse(asked('/api/comments').filter((r) => r.method === 'POST').at(-1).body)
  check('A range is sent with its start and its end', ranged.tStart === 0.85 && ranged.tEnd === 1.15)
  await post({ kind: 'technique-wrong', body: 'The fingers point down at release. They must follow the ball.', at: 1.22, part: 'hand_r' })
  check('The form is empty again after a comment', await page.evaluate(() => document.getElementById('comment-body').value === ''
    && document.getElementById('comment-part').value === '' && !document.querySelector('input[name="comment-kind"]:checked')))

  const marks = await page.$$eval('#timeline-markers .marker', (els) => els.map((el) => ({ range: el.classList.contains('range'), label: el.title,
    centre: el.getBoundingClientRect().left + (el.classList.contains('range') ? 0 : el.getBoundingClientRect().width / 2) })))
  const track = await page.$eval('#timeline', (el) => { const r = el.getBoundingClientRect(); return { left: r.left, width: r.width, max: Number(el.max) } })
  const expected = (t) => track.left + 8 + (track.width - 16) * (t / track.max)
  check('Each comment is a marker on the timeline at its time, and a range has a width',
    marks.length === 3 && marks[1].range && !marks[0].range && [0.62, 0.85, 1.22].every((t, i) => Math.abs(marks[i].centre - expected(t)) < 2))
  check('The Review tab counts the comments on this version', (await text('#review-tab-count')) === '3')
  await page.evaluate(() => window.athleteStudio.seek(0.3))
  await page.click('[data-tab="animate"]')
  await page.click('#timeline-markers .marker')
  check('A marker goes to its moment and opens its comment', await page.evaluate(() => Math.abs(window.athleteStudio.state.time - 0.62) < 0.002
    && !document.getElementById('panel-review').hidden && document.querySelector('#comment-list .comment').classList.contains('selected')))
  await shot('05-comment-form-and-markers', 'Review tab: the comment form, with three comments marked on the timeline')
  await page.$eval('#comment-list', (el) => el.scrollIntoView({ block: 'start' }))
  await shot('06-comment-list', 'Review tab: the comments of this version, each with an answer field')

  // ---- a movement that is not an animation of the version
  await page.evaluate(() => window.athleteStudio.selectClip('Receive_pass'))
  await page.evaluate(() => window.athleteStudio.pause())
  await page.click('[data-tab="review"]')
  await page.waitForSelector('#comment-unavailable:not([hidden])')
  check('A sequence Studio builds takes no comment, shows no marker and makes no statement about approval',
    !(await visible('#comment-form')) && (await page.$$('#timeline-markers .marker')).length === 0 && (await text('#approval-line')) === '')
  await page.$eval('#comments', (el) => el.scrollIntoView({ block: 'start' }))
  await shot('07-no-comment-on-a-built-sequence', 'Review tab: a movement Studio builds takes no comment')

  // ---- an approval
  await page.evaluate(() => window.athleteStudio.selectClip('netball_chest_pass'))
  await page.evaluate(() => window.athleteStudio.pause())
  await page.click('[data-tab="review"]')
  await page.waitForSelector('#comment-form:not([hidden])')
  await post({ kind: 'approve', at: 1.5 })
  check('After a reviewer approves, the animation shows as approved in this version, by name',
    (await text('#approval-line')) === 'Approved in this version by Coach (development).' && await page.$eval('#approval-line', (el) => el.classList.contains('approved')))
  await page.evaluate(() => window.athleteStudio.selectClip('netball_bounce_pass'))
  await page.evaluate(() => window.athleteStudio.pause())
  // The panel follows the clip on the next frame.
  await page.waitForFunction(() => document.querySelectorAll('#timeline-markers .marker').length === 0)
  check('The approval of one animation says nothing about another', (await text('#approval-line')) === 'No reviewer approved this animation in this version.')
  await page.evaluate(() => window.athleteStudio.selectClip('netball_chest_pass'))
  await page.evaluate(() => window.athleteStudio.pause())
  await page.click('[data-tab="review"]')
  await page.$eval('.inspector', (el) => { el.scrollTop = 0 })
  await shot('08-approved', 'Review tab: approved in this version, by the reviewer who approved')

  // ---- an author reads and answers
  await page.click('#sign-out')
  await page.waitForSelector('#signin-ask:not([hidden])')
  check('Sign-out forgets the session', await page.evaluate(() => localStorage.getItem('braven-studio.session.v1') === null))
  await signInAs('author@braven.test')
  check('An author reads the reviewer\'s comments', (await page.$$('#comment-list .comment')).length === 4)
  check('A restored setup keeps the name of its camera view', await page.evaluate(() => window.athleteStudio.state.view === 'quarter'
    && document.getElementById('three-quarter').classList.contains('selected')))
  await page.mouse.move(700, 400); await page.mouse.down(); await page.mouse.move(760, 410, { steps: 4 }); await page.mouse.up()
  check('A camera the person moved is their own angle', await page.evaluate(() => window.athleteStudio.state.view === 'free')
    && (await text('#comment-view')) === 'Camera: Own angle')
  await page.click('#three-quarter')
  check('An author is not offered an approval', await page.$eval('input[name="comment-kind"][value="approve"]', (el) => el.disabled))
  await page.type('#comment-list .comment .answer-form input', 'Thank you. The knee is fixed in the next version.')
  await page.click('#comment-list .comment .answer-form button')
  await page.waitForSelector('#comment-list .comment .comment-answer')
  check('An answer shows under the comment it answers, with its author',
    /Author \(development\)/.test(await text('#comment-list .comment .comment-answer .comment-by')) && (await page.$$('#timeline-markers .marker')).length === 4)
  check('The first comment is as the reviewer wrote it', (await text('#comment-list .comment p.comment-body')) === 'The left knee stays straight when she steps. It must bend into the step.')
  await page.$eval('#notification', (el) => { el.hidden = true })
  await page.$eval('#comment-list', (el) => el.scrollIntoView({ block: 'start' }))
  await shot('09-author-answer', 'Review tab as an author: the answer under the reviewer\'s comment')
  await page.click('#sign-out')
  await page.waitForSelector('#signin-ask:not([hidden])')

  // ---- a phone
  await page.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true })
  await page.goto(url, { waitUntil: 'networkidle0' })
  check('The sign-in screen fits a phone', await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
  await shot('10-phone-sign-in', 'Phone: sign-in')
  await signInAs('coach@braven.test')
  check('Hosted Studio fits a phone', await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
  check('On a phone each marker is at least 24 px to touch', await page.$$eval('#timeline-markers .marker', (els) => els.every((el) => {
    const r = el.getBoundingClientRect(); const pad = 9; return r.width + pad * 2 >= 24 && r.height + pad * 2 >= 24
  })))
  await page.$eval('#stage', (el) => el.scrollIntoView({ block: 'start' }))
  await shot('11-phone-stage', 'Phone: the animation and the timeline with comment markers')
  await page.$eval('#comment-form', (el) => el.scrollIntoView({ block: 'start' }))
  await shot('12-phone-comment-form', 'Phone: the comment form')

  check('No error was thrown on the page', errors.length === 0)
} finally {
  await browser.close()
}

const git = (...args) => execFileSync('git', args, { encoding: 'utf8' }).trim()
fs.writeFileSync(path.join(out, 'checks.json'), JSON.stringify({ url, checks, errors }, null, 2))
if (git('status', '--porcelain')) {
  console.log(`${checks.length} checks passed. The working tree has changes, so screens.json was NOT written: commit, then run again.`)
} else {
  fs.writeFileSync(path.join(out, 'screens.json'), JSON.stringify({ commit: git('rev-parse', 'HEAD'), shots }, null, 2))
  console.log(`${checks.length} checks passed, ${shots.length} screenshots, commit ${git('rev-parse', '--short', 'HEAD')}.`)
}
