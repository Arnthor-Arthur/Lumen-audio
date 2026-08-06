# Decisions

A short, honest record of how you approached this. Bullet points are fine — this doesn't
need to be long, it needs to be real. It's the backbone of our conversation.

## Assumptions

The brief is deliberately under-specified. What did you assume, and why?
(e.g. who the user is, what "grounded" should mean, how strict the refusal should be.)

- The user is a Lumen Audio customer asking support-style questions, so answers should be
  short, direct, and in a support-agent tone rather than a verbose explanation.
- "Grounded" means the model may only use text retrieved from `data/`, never outside
  knowledge. Enforced via a strict system prompt plus a refusal-detection guardrail on
  the output, not just an instruction.
- Given six short, single-topic articles (~200–400 words each), one chunk per document is
  enough, there's no real gain from splitting further, and it keeps retrieval and citation
  simple (chunk == source file).
- "Strict" refusal: I chose to err toward declining over inferring. E.g. "Do you ship to
  the US?" retrieves `shipping.md` ("ships to the EU and UK only") but the model declines
  rather than inferring "no." That's a real tradeoff, not a bug negative inference is
  exactly the kind of small leap that turns into a hallucination on a less clear-cut
  question, and the brief explicitly rewards declining over guessing.

## What I built and prioritised

What did you build first, and what does the working slice do?

- Built the full path end-to-end first (index → retrieve → generate → guardrail) rather
  than one piece in depth, since a thin working slice beats a polished dead end.
- Startup: embed each of the 6 articles once with `llm.embed()`, store as a normalized
  numpy matrix for cosine similarity.
- `/ask`: embed the question, cosine-similarity search, take the best chunk (+ a second
  only if its score is within 0.05 of the best, for questions spanning two policies).
- Guardrail 1 (retrieval): if the best similarity is below a threshold (0.25, tuned by
  manually checking scores against in/out-of-KB questions), skip the LLM entirely and
  return the refusal — cheap and deterministic.
- Guardrail 2 (generation): the system prompt requires the model to reply with an exact
  refusal sentence if the retrieved context doesn't answer the question; the handler
  checks for that sentence and forces `sources: []` even if retrieval fired. This catches
  topically-close-but-not-actually-answering chunks (e.g. a "student discount" question
  is nearest to `refunds.md` by embedding similarity but doesn't answer it).
- Verified manually: covered questions (returns, warranty+faulty combined, order
  cancellation) return correct grounded answers with citations; out-of-KB and
  adjacent-but-uncovered questions (capital of France, student discount) decline with
  empty sources; empty question returns 400.

## What I cut, and why

What did you consciously leave out given the ~2-hour timebox?

- No persistent vector store — in-memory numpy is explicitly fine per the brief and the KB
  is tiny (6 chunks), so anything heavier would be premature.
- No sub-document chunking/overlap logic not worth it at this KB size; would matter once
  articles get longer or more numerous.
- `sources` is all chunks passed to the LLM as context, not necessarily all chunks the
  final answer actually drew from e.g. a two-chunk answer cites both even if one only
  contributed peripheral detail. Precise attribution would need per-sentence source
  tracking, out of scope for the timebox.
- No retries/backoff on the OpenAI calls, no caching of repeated questions, no rate
  limiting on `/ask`.
- No automated test suite beyond the provided `smoke_test.py` — I ran additional manual
  edge cases (multi-doc question, adjacent-but-uncovered, unrelated topic, empty input)
  but didn't write them up as pytest cases.

## How I'd know it works

How would you evaluate this — beyond "it ran"? What would you measure?

- A small labeled eval set per KB article (a handful of paraphrased questions per doc)
  checking: correct source(s) cited, answer consistent with the source text, and no
  hallucinated details not present in the article.
- A set of deliberately out-of-KB and adjacent-but-uncovered questions (like "ship to the
  US?" or "student discount?") checking the refusal rate and empty `sources`.
- Precision/recall on citations specifically — since the response contract is graded on
  `sources`, false-positive citations (grounded-looking answer, wrong or extra source) are
  as important to catch as false refusals.
- Threshold sensitivity: rerun the eval set while sweeping `SIM_THRESHOLD` to see how
  refusal rate trades off against false-decline rate, rather than trusting one hand-picked
  value.

## With more time / to take it to production

What are the next things you'd do, and what would change to run this for real
(multiple clients, real volume, reliability, cost)?

- Real vector store (pgvector/Pinecone/etc.) once the KB grows beyond "fits in memory,"
  plus a proper ingestion pipeline (chunking with overlap, re-embed on doc change) instead
  of load-everything-at-import.
- Per-chunk source attribution in the answer (which specific chunk each sentence came
  from) instead of citing every chunk passed into context.
- Replace the single fixed similarity threshold with a calibrated one (or a small
  reranker) validated against a real eval set, since 0.25 was hand-tuned against six
  documents and won't generalize.
- Multi-tenancy: today the KB and embeddings are global process state; a real deployment
  needs per-client KBs, index isolation, and auth on `/ask`.
- Observability: log every question, retrieved chunks, similarity scores, and final
  answer/citation so refusals and citation quality can be audited over time — this is also
  how you'd build the eval set above from real traffic.
- Reliability: retries/backoff on the LLM calls, timeouts surfaced as a clean error
  response instead of a 500, and a fallback if the embeddings API is down.
- Cost: cache embeddings for the (static) KB instead of recomputing at every process
  restart; consider a cheaper/local embedding model given how small and low-throughput
  this KB is.
