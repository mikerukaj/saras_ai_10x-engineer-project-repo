// REPL driver for PromptLab's frontend, driven with a real headless
// Chromium browser (no windowing system needed - unlike an Electron app,
// a plain web page needs no xvfb).
//
// Requires the `playwright` npm package AND a downloaded Chromium build
// to be reachable - see SKILL.md's Prerequisites. This project's own
// package.json does not depend on playwright (it's agent tooling, not
// app code), so point PLAYWRIGHT_MODULE at wherever you installed it if
// it's not hoisted somewhere Node's default resolution finds it, e.g.:
//   PLAYWRIGHT_MODULE=/path/to/node_modules/playwright/index.mjs node driver.mjs
//
// Designed for agents: run it under tmux, `send-keys` commands one line
// at a time, `capture-pane` to read output.
//
// Commands use Playwright's own selector engines directly (text=Foo,
// button:has-text("Foo"), css, etc.) - this is a plain DOM page with no
// BrowserView/coordinate weirdness, so there's no need to hand-roll
// evaluate()-based clicking the way an Electron driver would.

import * as fs from 'node:fs'
import * as path from 'node:path'
import * as readline from 'node:readline'

const modulePath = process.env.PLAYWRIGHT_MODULE || 'playwright'
const { chromium } = await import(modulePath)

const SHOT_DIR = process.env.SCREENSHOT_DIR || '/tmp/promptlab-shots'
fs.mkdirSync(SHOT_DIR, { recursive: true })

let browser = null
let page = null
const consoleErrors = []

const COMMANDS = {
  async launch() {
    if (browser) return console.log('already launched')
    browser = await chromium.launch({ args: ['--no-sandbox'] })
    page = await browser.newPage()
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text())
    })
    page.on('pageerror', (err) => consoleErrors.push('pageerror: ' + err.message))
    console.log('launched')
  },

  async nav(url) {
    if (!page) return console.log('ERROR: launch first')
    await page.goto(url, { waitUntil: 'networkidle' })
    console.log('nav ->', page.url())
  },

  async 'wait-for'(selector) {
    if (!page) return console.log('ERROR: launch first')
    try {
      await page.waitForSelector(selector, { timeout: 10_000 })
      console.log('found:', selector)
    } catch {
      console.log('TIMEOUT:', selector)
    }
  },

  async click(selector) {
    if (!page) return console.log('ERROR: launch first')
    try {
      await page.click(selector, { timeout: 10_000 })
      console.log('click', selector, '-> OK')
    } catch (e) {
      console.log('click', selector, '-> ERROR:', e.message.split('\n')[0])
    }
  },

  // fill <selector> <text...> - selector is the first token, the rest
  // of the line (rejoined) is the value, since values often contain
  // spaces.
  async fill(rest) {
    if (!page) return console.log('ERROR: launch first')
    const [selector, ...valueParts] = rest.split(' ')
    const value = valueParts.join(' ')
    try {
      await page.fill(selector, value, { timeout: 10_000 })
      console.log('fill', selector, '=', JSON.stringify(value))
    } catch (e) {
      console.log('fill', selector, '-> ERROR:', e.message.split('\n')[0])
    }
  },

  async press(key) {
    if (!page) return console.log('ERROR: launch first')
    await page.keyboard.press(key)
    console.log('press', key)
  },

  async screenshot(name) {
    if (!page) return console.log('ERROR: launch first')
    const file = path.join(SHOT_DIR, (name || `ss-${Date.now()}`) + '.png')
    await page.screenshot({ path: file, fullPage: true })
    console.log('screenshot:', file)
  },

  async text(selector) {
    if (!page) return console.log('ERROR: launch first')
    const value = await page
      .locator(selector || 'body')
      .first()
      .innerText()
      .catch((e) => 'ERROR: ' + e.message.split('\n')[0])
    console.log(value)
  },

  async eval(expr) {
    if (!page) return console.log('ERROR: launch first')
    try {
      console.log(JSON.stringify(await page.evaluate(expr)))
    } catch (e) {
      console.log('ERROR:', e.message.split('\n')[0])
    }
  },

  url() {
    console.log(page ? page.url() : '(no page)')
  },

  console() {
    console.log(JSON.stringify(consoleErrors, null, 2))
  },

  async quit() {
    if (browser) await browser.close().catch(() => {})
    browser = null
    page = null
  },

  help() {
    console.log('commands:', Object.keys(COMMANDS).join(', '))
  },
}

const stdin = fs.createReadStream(null, { fd: fs.openSync('/dev/stdin', 'r') })
const rl = readline.createInterface({ input: stdin, output: process.stdout, prompt: 'driver> ' })

rl.on('line', async (line) => {
  const trimmed = line.trim()
  const spaceIndex = trimmed.indexOf(' ')
  const cmd = spaceIndex === -1 ? trimmed : trimmed.slice(0, spaceIndex)
  const arg = spaceIndex === -1 ? '' : trimmed.slice(spaceIndex + 1)
  if (!cmd) return rl.prompt()
  const fn = COMMANDS[cmd]
  if (!fn) {
    console.log('unknown:', cmd, '- try: help')
    return rl.prompt()
  }
  try {
    await fn(arg)
  } catch (e) {
    console.log('ERROR:', e.message)
  }
  if (cmd === 'quit') {
    rl.close()
    process.exit(0)
  }
  rl.prompt()
})
rl.on('close', async () => {
  await COMMANDS.quit()
  process.exit(0)
})

console.log('promptlab driver - "help" for commands, "launch" to start')
rl.prompt()
