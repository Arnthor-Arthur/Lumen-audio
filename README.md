# Lumen Audio — grounded Q&A take-home

Thanks for taking the time. This is a short, practical build that mirrors the kind of work
this role does day to day. We care about **working software and clear thinking, not
polish**, and we'll talk through your code and choices together in a follow-up interview.

## Timebox: ~2 hours

Please **cap this at about 2 hours and submit what you have.** We're not expecting it to be
finished or perfect — we're far more interested in what you choose to build first, what you
deliberately leave out, and why. A focused, working slice beats a sprawling, broken one.

## Using AI tools

Use whatever you'd normally use, **including AI coding assistants — that's how we work
here.** The only thing we ask is that you understand what you submit: the interview is built
around walking through your code and reasoning, so anything you can't explain will work
against you, and anything you can explain well will count for you.

## The task

Lumen Audio (a fictional consumer-audio client) wants customer questions answered **only**
from their policy knowledge base — with the source shown, and a graceful refusal when the
answer isn't there.

Build an endpoint that:

1. **Ingests** the policy docs in `data/` (chunk + index however you like — an in-memory
   store is completely fine; you do not need to stand up real infrastructure).
2. Takes a customer question and returns a **grounded answer with a citation** to the
   source article it came from.
3. **Declines rather than guesses** when the question isn't covered by the KB.

### Response contract

So we can run your submission consistently, please have `POST /ask` accept
`{"question": "..."}` and return JSON with these two fields:

```json
{ "answer": "string", "sources": ["refunds.md"] }
```

- `sources` lists the source file(s) the answer came from.
- When you can't answer from the KB, return your refusal in `answer` and an **empty**
  `sources` list. (This is how we check the guardrail.)

## What's provided

- `data/` — the six-article Lumen Audio knowledge base.
- `app.py` — a runnable Flask skeleton with a stubbed `/ask` endpoint and `TODO` markers.
- `llm.py` — a thin wrapper for embeddings + chat completion, configured via environment
  variables. Swap it out if you'd rather use a different provider or approach.
- `smoke_test.py` — a tiny self-check so you can sanity-test your endpoint.
- `Dockerfile` / `docker-compose.yml` — so it runs identically anywhere.
- `DECISIONS.md` — **please fill this in** (see below).

## Running it

**Use your own model and API key** — pick whatever provider you like (OpenAI, Anthropic,
Azure OpenAI, or a local/offline model if you'd rather not use a hosted API at all). Copy
`.env.example` to `.env` and set your config:

```bash
cp .env.example .env
# edit .env with your provider, key, and model names
```

Then either:

```bash
docker compose up --build          # option A: Docker
```
or
```bash
pip install -r requirements.txt    # option B: local Python
python app.py
```

Sanity-check it:

```bash
python smoke_test.py               # hits /health and a couple of example questions
curl -X POST localhost:5000/ask -H 'content-type: application/json' \
  -d '{"question": "How long is the return window?"}'
```

## How to submit

When you're done (or your ~2 hours are up):

1. **Don't fork this repo.** Clone it, then push your solution to a **new public repo under
   your own GitHub account.**
2. **Make sure your repo is public** — confirm by opening its link in a private/incognito
   window while logged out. If you can see it there, so can we.
3. Fill in **`DECISIONS.md`** (in the repo) — it matters as much as the code: your
   assumptions about the (deliberately under-specified) brief, what you prioritised and cut,
   how you'd know it works, and what you'd do with more time or to take it to production.
4. Email your repo link to **andrei.buf@otonomee.com**.

**Timebox:** spend about 2 hours and submit what you have — please return within **5 days**.
Build the slice you'd be proud to defend, and we'll walk through it together in a follow-up
interview.
