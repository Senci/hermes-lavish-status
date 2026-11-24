// desktop/src/index.js
import { Codicon, STATUSBAR_AREAS, Tip } from "@hermes/plugin-sdk";
import { createElement as h } from "react";

// .build/node_modules/hermes-plugin-ui-kit/src/live.js
import { atom, host, queryClient, useQuery, useValue } from "@hermes/plugin-sdk";
var POLL_FLOOR_MS = 15e3;
var LIVE_SAFETY_MS = 6e4;
function useBackend() {
  return { conn: useValue(host.state.connectionId) ?? "", profile: useValue(host.state.profile) ?? "" };
}
function useLiveQuery({ live = false, pollMs = POLL_FLOOR_MS, liveMs = LIVE_SAFETY_MS, ...query }) {
  return useQuery({ ...query, refetchInterval: live ? liveMs : pollMs });
}

// .build/node_modules/hermes-plugin-ui-kit/src/theme.js
var ui = (name) => `var(--ui-${name})`;
var TONE = {
  text: ui("text-primary"),
  muted: ui("text-tertiary"),
  secondary: ui("text-secondary"),
  faint: ui("text-quaternary"),
  accent: ui("accent"),
  green: ui("green"),
  red: ui("red"),
  yellow: ui("yellow"),
  blue: ui("blue"),
  purple: ui("purple")
};
var muted = { color: TONE.muted };

// desktop/src/index.js
var ID = "lavish-status";
var POLL_MS = 1e4;
var TONES = { block: TONE.red, decide: ui("orange") };
var ICONS = { block: "error", decide: "question" };
var api = null;
function useSummary() {
  const { conn, profile } = useBackend();
  return useLiveQuery({
    queryKey: [ID, "summary", conn, profile],
    queryFn: () => api ? api.rest("/summary") : Promise.reject(new Error("lavish-status not loaded")),
    placeholderData: (prev, prevQuery) => prevQuery?.queryKey[2] === conn && prevQuery?.queryKey[3] === profile ? prev : void 0,
    pollMs: POLL_MS,
    staleTime: POLL_MS
  });
}
var openBoard = (url) => {
  if (url) void window.hermesDesktop?.openExternal?.(url);
};
function Badge() {
  const { data } = useSummary();
  if (!data || !data.fresh) return null;
  const counts = data.counts || {};
  const shown = ["block", "decide"].filter((k) => counts[k] > 0);
  if (!shown.length) return null;
  const pages = data.pages || [];
  const label = h(
    "div",
    { style: { display: "grid", gap: 2 } },
    ...pages.map((p) => h("div", { key: p.key }, `${p.attn}: ${p.title || p.key}`))
  );
  return h(
    Tip,
    { label },
    h(
      "button",
      {
        type: "button",
        "aria-label": `Lavish reviews waiting: ${shown.map((k) => `${counts[k]} ${k}`).join(", ")}`,
        className: "inline-flex h-full items-center gap-1.5 rounded-none px-1.5 text-[0.6875rem] tabular-nums transition-colors hover:bg-(--chrome-action-hover)",
        disabled: !data.board_url,
        onClick: () => openBoard(data.board_url)
      },
      ...shown.map((k) => h(
        "span",
        { key: k, className: "inline-flex items-center gap-0.5", style: { color: TONES[k] } },
        h(Codicon, { name: ICONS[k], size: "0.7rem" }),
        `${counts[k]} ${k}`
      ))
    )
  );
}
var index_default = {
  id: ID,
  name: "Lavish Status",
  description: "Status bar badge for the Lavish review pages that wait on you: red block count, orange decide count; click opens the sessions board.",
  register(ctx) {
    api = ctx;
    ctx.onDispose(() => {
      api = null;
    });
    ctx.registerMany([{ id: "status", area: STATUSBAR_AREAS.right, order: 82, render: () => h(Badge) }]);
  }
};
export {
  index_default as default
};
