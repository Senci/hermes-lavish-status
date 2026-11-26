// Lavish status: a status-bar badge for the Lavish review pages that wait on the operator, red for
// block and orange for decide, hidden when both are 0. Data comes from this package's backend
// (dashboard/plugin_api.py) through ctx.rest. Click opens the sessions board in the browser.
//
// Source of desktop/plugin.js. Build: `sh scripts/rebuild.sh`.

import { Codicon, STATUSBAR_AREAS, Tip } from '@hermes/plugin-sdk'
import { createElement as h } from 'react'

import { useBackend, useLiveQuery } from 'hermes-plugin-ui-kit/live.js'
import { TONE, ui } from 'hermes-plugin-ui-kit/theme.js'

const ID = 'lavish-status'
const POLL_MS = 10_000
const TONES = { block: TONE.red, decide: ui('orange') }
const ICONS = { block: 'error', decide: 'question' }

let api = null

function useSummary() {
  const { conn, profile } = useBackend()
  return useLiveQuery({
    queryKey: [ID, 'summary', conn, profile],
    queryFn: () => (api ? api.rest('/summary') : Promise.reject(new Error('lavish-status not loaded'))),
    placeholderData: (prev, prevQuery) => (prevQuery?.queryKey[2] === conn && prevQuery?.queryKey[3] === profile ? prev : undefined),
    pollMs: POLL_MS,
    staleTime: POLL_MS
  })
}

const openBoard = url => {
  if (url) void api?.os.openExternal(url)
}

function Badge() {
  const { data } = useSummary()
  if (!data || !data.fresh) return null
  const counts = data.counts || {}
  const shown = ['block', 'decide'].filter(k => counts[k] > 0)
  if (!shown.length) return null
  const pages = data.pages || []
  const label = h('div', { style: { display: 'grid', gap: 2 } },
    ...pages.map(p => h('div', { key: p.key }, `${p.attn}: ${p.title || p.key}`)))
  return h(Tip, { label },
    h('button', {
      type: 'button',
      'aria-label': `Lavish reviews waiting: ${shown.map(k => `${counts[k]} ${k}`).join(', ')}`,
      className: 'inline-flex h-full items-center gap-1.5 rounded-none px-1.5 text-[0.6875rem] tabular-nums transition-colors hover:bg-(--chrome-action-hover)',
      disabled: !data.board_url,
      onClick: () => openBoard(data.board_url)
    },
    ...shown.map(k => h('span', { key: k, className: 'inline-flex items-center gap-0.5', style: { color: TONES[k] } },
      h(Codicon, { name: ICONS[k], size: '0.7rem' }), `${counts[k]} ${k}`))))
}

export default {
  id: ID,
  name: 'Lavish Status',
  description: 'Status bar badge for the Lavish review pages that wait on you: red block count, orange decide count; click opens the sessions board.',
  register(ctx) {
    api = ctx
    ctx.onDispose(() => { api = null })
    ctx.registerMany([{ id: 'status', area: STATUSBAR_AREAS.right, order: 82, render: () => h(Badge) }])
  }
}
