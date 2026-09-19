# Artifact Viewer — Build Order Correction

## Task
Add the side-panel Artifact Viewer that renders generated Markdown/HTML
next to the chat, similar to Claude Artifacts.

## Initial approach
Initially asked Claude to build the artifact viewer at the same time as
the core RAG/chat functionality, planning to build both halves of the
app in parallel to save time: "Let's build the chat interface and the
artifact viewer panel together."

## Correction
Partway through, I realized the artifact viewer had nothing real to
render yet, since the RAG pipeline wasn't generating actual grounded
content — so Claude and I were testing the viewer against placeholder
Markdown strings that didn't reflect what the real LLM output would
look like (e.g. real output included citation markers and headers that
the placeholder text didn't have).

I redirected Claude: "Let's pause the artifact viewer and finish the
ingestion and retrieval pipeline first, so we have real generated
content to test the viewer against instead of fake data."

## Outcome
Once the RAG pipeline and the Ship 30/30 skill were producing real
Markdown and HTML output, going back to the artifact viewer was faster
and caught real formatting issues — for example, the sandboxed iframe
initially stripped out inline styles in the generated HTML snippets,
which hadn't shown up when testing against the earlier placeholder
content. Building the viewer second, against real output, surfaced that
problem immediately instead of leaving it hidden until later.
