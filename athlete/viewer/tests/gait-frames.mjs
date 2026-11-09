/** Save every authored frame of a locomotion clip from the live Studio canvas.
 *
 *   STUDIO_URL=http://127.0.0.1:5398/ node tests/gait-frames.mjs <clip> <fps> <outDir>
 *
 * The clip is paused and seeked to each frame time (no screen recording), so
 * frame N of the PNG sequence is frame N of the clip. Views: side and front.
 */
import {createRequire} from 'node:module'
import fs from 'node:fs'
import path from 'node:path'
const [clip, fps, outDir] = [process.argv[2], Number(process.argv[3] || 60), path.resolve(process.argv[4] || 'verification/gait-frames')]
const require = createRequire((process.env.BRAVEN_TACTICS_PATH || 'F:/Repositories/braven-tactics-netball-athlete') + '/package.json')
const browser = await require('puppeteer-core').launch({executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true, defaultViewport: {width: 1400, height: 1000}})
try {
  const page = await browser.newPage(), errors = []
  page.on('pageerror', e => errors.push(String(e)))
  await page.goto(process.env.STUDIO_URL || 'http://127.0.0.1:5397/', {waitUntil: 'networkidle0'})
  await page.waitForFunction(() => window.athleteStudio)
  await page.select('#clip', clip)
  const info = await page.evaluate(() => { const a = window.athleteStudio; a.pause(); return {duration: a.duration(), hash: a.assetHash, revision: a.assetRevision} })
  const frames = Math.round(info.duration * fps)
  const canvas = await page.$('canvas')
  for (const view of ['side', 'front']) {
    await page.click('#' + view)
    const dir = path.join(outDir, `${clip}-${view}`); fs.mkdirSync(dir, {recursive: true})
    for (let i = 0; i < frames; i++) {
      await page.evaluate(t => { const a = window.athleteStudio; a.pause(); a.seek(t); a.renderer.render(a.scene, a.camera) }, i / fps)
      await canvas.screenshot({path: path.join(dir, `${String(i).padStart(3, '0')}.png`)})
    }
  }
  if (errors.length) throw new Error(errors.join('\n'))
  console.log(JSON.stringify({clip, frames, ...info, outDir}))
} finally { await browser.close() }
