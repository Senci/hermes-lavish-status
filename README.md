# lavish-status

![lavish-status](docs/assets/cover.jpg)

Hermes Desktop status-bar badge for Lavish review pages that wait on you (a Hermes Desktop add-on for lavish-axi): a red
`N block` and an orange `N decide`, hidden when both are 0 or when the summary is stale.

- Data: `~/.hermes/lavish-kit/summary.json`, written every 5 s by the lavish-kit status writer (`hx-status.py`).
  Read-only; a file older than 30 s counts as stale and shows nothing.
- Backend: `GET /api/plugins/lavish-status/summary` returns `fresh`, `counts` (block, decide),
  `board_url` and the block/decide pages.
- Desktop: polls every 10 s. Click opens the sessions board URL in the browser; the tooltip lists the
  waiting page titles.
- Tests: `python3 -m unittest discover -s tests` in this directory.
- Build: `sh scripts/rebuild.sh` in this directory installs the pinned esbuild and [hermes-plugin-ui-kit](https://www.npmjs.com/package/hermes-plugin-ui-kit) into `.build/` and rebuilds `desktop/plugin.js`.
