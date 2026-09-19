# Improving RAG Response Speed

## Task
Speed up responses when answering questions grounded in Lenny's Podcast
transcripts — the first working version felt slow, with a noticeable
delay before any text appeared.

## What I asked Claude
"The assistant takes a while to respond — the user just sees nothing
happening until the full answer shows up. How can I make this feel
faster?"

## What Claude suggested
Claude identified two separate issues contributing to the slowness:
1. The backend was waiting for the entire LLM response to finish
   generating before sending anything back to the frontend, instead of
   streaming tokens as they were produced.
2. The retrieval step was pulling a larger number of chunks than
   necessary (`top_k=10`), which added extra context for the model to
   process before it could start generating.

Claude suggested two changes: implementing Server-Sent Events (SSE) so
the backend could stream tokens to the frontend as soon as the LLM
produced them, and reducing `top_k` to 4-6 chunks, which is close to
what the reference architecture recommended.

## Correction / iteration
The first streaming implementation Claude provided sent raw text chunks
without a defined event format, which made it hard for the frontend to
distinguish between a status update (e.g. "retrieving transcripts...")
and an actual answer token. I asked Claude to restructure the stream
into typed JSON events (`{"type": "status", ...}` and
`{"type": "token", ...}`) so the frontend could handle each case
differently — showing a loading indicator for status events and
appending text for token events.

## Outcome
After both changes, the first token appeared noticeably faster, and the
typed event stream made the frontend UI easier to build correctly,
since it no longer had to guess what kind of message it was receiving.
