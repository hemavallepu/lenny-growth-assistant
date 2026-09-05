# Design Spec — The Lenny Growth Assistant

## Layout
Two-pane, dual-column layout modeled on Claude's Artifacts UX:

- **Left pane (always visible)**: chat — session context, message history,
  streaming assistant bubbles, mode toggle (Grounded Q&A / Ship 30-30),
  provider badge (click to switch local ↔ cloud).
- **Right pane (collapsible)**: artifact viewer — opens automatically when
  the model emits an ` ```artifact:markdown ``` ` or ` ```artifact:html ``` `
  fenced block. Closed by default to keep the chat focused for plain Q&A.

## State Transitions
1. **Idle** → user types a question → **Sending** (input disabled, streaming
   bubble appended).
2. **Streaming** → tokens append live to the assistant bubble.
3. On stream end: if the response contains an artifact block, the bubble
   collapses to a short pointer ("Response rendered in the artifact pane →")
   and the right pane opens with the rendered content.
4. **No-context state**: if retrieval score is below threshold, the
   assistant bubble shows the fixed refusal message — no artifact, no
   streaming delay (short-circuited server-side).

## Responsive Behavior
- **Desktop (≥1024px)**: side-by-side panes, artifact pane at 45% width.
- **Tablet/mobile (<1024px)**: artifact pane becomes a full-screen overlay
  triggered by the same toggle, chat pane goes full width when closed.
  (Not yet implemented in the vanilla-JS prototype — flagged as a
  known gap, see README "Not yet done".)

## Visual Language
- Neutral, low-chrome UI — dark slate accents, light gray assistant bubbles,
  dark user bubbles (mirrors familiar chat UX so evaluators focus on
  functionality, not novelty).
- Mode and provider controls are pill-shaped toggle buttons, always visible
  above the message list so the evaluator can see the demo state at a glance.
