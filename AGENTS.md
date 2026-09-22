# AGENTS.md — Chronos

**Samsung PRISM GenAI Hackathon 3rd Edition · Theme 05: Interruptible Real-Time Agents**

This file is read automatically at the start of every session by both agents working in this repo — **Antigravity** and **OpenCode**. It is the shared, tool-agnostic contract between them. If you are neither of those two, ignore the role sections below and treat this as general project context.

If this file and `chronos-project-spec.md` ever disagree on anything technical, **the spec wins** — fix this file, don't silently override the spec.

---

## 0. Read This First, Every Session

Before writing or changing anything:

1. Read `chronos-project-spec.md` in full if you have not already this session. It is the technical constitution for this project — problem statement, evaluation criteria, architecture, interface contracts, subsystem specs, invariants, build plan.
2. Look at `chronos-architecture-diagram.svg` for the system topology — it matches spec §5 exactly.
3. Open `changes.md` and read at least the last 10 entries (all of it, if shorter). This tells you what already exists, what the other agent just did and why, and whether anything is explicitly flagged for you.
4. Check the current phase's task list artifact (§4 below) before picking up new work. Don't start a task that's already in progress or already marked done.
5. Never re-derive an architectural decision from scratch if `chronos-project-spec.md` or `changes.md` already made it. Cite the section/entry instead of re-deciding.

---

## 1. What Chronos Is

Chronos is a virtual-clock-native agent kernel for full-duplex, interruptible conversation. Its scoring depends on: correct tool execution and state-snapshot accuracy (Task Completion, 40%), clean cancellation of superseded work with no stale re-runs (Interruption Recovery, 35%), fast first response (Response Latency, 15%), and zero duplicate state-changing tool calls (Safety & Protocol, 10%), plus a 1.5× multiplier on multimodal (audio/visual) scenarios in the hidden test set. Full detail: `chronos-project-spec.md` §1–2.

The whole system turns on one primitive: a **monotonically increasing epoch counter**. Everything is stamped with the epoch that produced it; anything stamped with a stale epoch is refused by comparison, never by judgment. See spec §3–4 before touching any subsystem that deals with cancellation, effect dispatch, or belief classification — those sections encode safety-critical invariants that must not be "simplified" without a deliberate, logged decision.

---

## 2. Roles

Two agents share this repo. They do not run simultaneously in real time — they hand off through the repo state and `changes.md`. Each must be able to reconstruct what the other did and why, from the repo alone, without being told live.

### Antigravity — Architect & Orchestrator

Owns anything that changes the **shape** of the system:
- Implementation plans and task-list artifacts for each phase (§4)
- New module/subsystem scaffolding, following the layout in spec §5.3
- Interface and schema design (spec §7) and any change to it
- Cross-subsystem wiring and integration (ingress → belief → ledger → planner → gateway → egress)
- The Next.js telemetry dashboard scaffold (spec §12)
- Docker/compose, CI, and deployment config (§7 below)
- Reviewing OpenCode's flagged architectural questions and resolving them

### OpenCode — Implementer & Hardener

Owns anything **within** an already-scaffolded boundary:
- Filling in function/module bodies Antigravity has stubbed
- Unit tests, property-based tests (`hypothesis`) for the invariants in spec §4 and §15
- Edge-case handling from the table in spec §13
- Performance optimization within an existing module
- Diagnosing and fixing bugs, failing tests, or CI failures
- Tightening error handling, timeouts, and validation logic

**Decision rule for an ambiguous task:** if doing it well requires changing a public interface, a module boundary, or how two subsystems talk to each other → Antigravity. If it's fully contained inside one module's existing contract → OpenCode. When genuinely unsure, default to Antigravity for the first pass (scaffold + interface), then hand the body to OpenCode.

**Neither agent freelances outside its role.** If OpenCode discovers mid-task that a real fix requires an interface change, it stops, does not improvise the interface, and logs a flagged entry (§3) instead. If Antigravity finds itself writing deep implementation logic or a full test suite, that's a signal to scaffold and hand off instead.

---

## 3. The `changes.md` Protocol

`changes.md` is an **append-only** log — like the versioned ledger this project itself builds (spec §8.2): never edit or delete a past entry, only add new ones. If a past decision was wrong, log a new entry that supersedes it and say so.

**Every session, before writing code:** read the recent entries.
**Every session, before ending:** log what you did.

Entry format:

```
### [Phase N] <short title> — <YYYY-MM-DD>
Antigravity : <what changed / decided and why — or omit this line if Antigravity didn't act this entry>
Opencode : <what changed / implemented / fixed and why — or omit if not applicable>
Files: <paths touched>
Flags: <anything the other agent needs to know, decide, or pick up — or "none">
```

Rules:
- One entry per logical unit of work, not one per file.
- "Why," not just "what" — a line like `Opencode : added retry to search_flights` is insufficient; say why (e.g., `Opencode : added bounded retry to search_flights — mock tool flaked under the randomized-timing property test, retry doesn't touch idempotency since it's non-mutating`).
- `Flags` is how you hand off. If you leave it non-empty, the other agent should treat it as the first thing to check next session.
- Never mark your own flag resolved — the agent who picks it up closes it by referencing the flagging entry in their own new entry.

---

## 4. Phase Plan

Mirrors `chronos-project-spec.md` §14, restated here as phase gates rather than calendar days so either agent can check "are we allowed to move on yet" independently of exact dates. **The calendar still matters — final submission is 25 Sep 2026, 11:59 PM** — treat the day numbers below as the pace to hold, not a hard boundary between phases.

| Phase | Spec day(s) | Scope | Primary driver | Exit criteria |
|---|---|---|---|---|
| **0 — Kernel** | Day 0 | Epoch Arbiter, Effect Gateway + poisoning, Versioned Ledger, `VirtualClock` façade | Antigravity scaffolds → OpenCode hardens & property-tests | `hypothesis` suite proves Invariants 1, 5, 6, 7 (spec §4) hold under thousands of randomized interruption timings. **Do not start Phase 1 until this passes.** |
| **1 — Fast Path & Egress** | Day 1 | Template-bound Fast Path, floor-token supersession, Egress Serializer, fail-closed validation | Antigravity scaffolds schemas/templates → OpenCode implements validation + repair-then-degrade | Fast Path cannot assert completion (type-level, spec Invariant 3) — tested, not asserted by convention |
| **2 — Multimodal** | Day 2 | ASR (faster-whisper) + OCR ingestion, Contradiction Resolver, Tier-1 lexical filter + hard-override check | Antigravity scaffolds pipeline + tables → OpenCode wires libraries, handles cancellation-mid-transcription | Audio/visual events correctly re-enter or feed the belief pipeline; contradiction table fully unit-tested (one test per row, spec §8.3/§15.3) |
| **3 — Planner & Clock Supervisor** | Day 3 | Slow Path Planner, Tool Manifest parsing, (Tier-2 if time allows), Clock Supervisor + degradation ladder | Antigravity designs planner + ladder → OpenCode isolates and stress-tests the terminal fallback | Terminal path independently tested per spec §15.5 — a hang here is treated as a launch blocker, not a bug ticket |
| **4 — Integration, Dashboard, Deploy** | Day 4 | Full pipeline against mock harness, Next.js dashboard, Docker/compose, first ablations | Antigravity leads integration + dashboard scaffold → OpenCode wires telemetry data shapes, optimizes hot paths | End-to-end adversarial trace (spec §16) reproduces exactly; `docker compose up` runs clean on an untouched machine |
| **5 — Submission Hardening** | Day 5–6 | Adversarial scenario suite, bugfixing from CI, README, demo video, PPT support | OpenCode drives bugfixing from failing tests → Antigravity finalizes docs/config | Submission checklist (spec §19) fully checked |

Antigravity should generate and maintain the actual granular task-list artifact per phase (its native strength) — this table is the gate structure, not a substitute for that.

---

## 5. Handoff & Turn-Taking

1. **Check before you build.** Read `changes.md` recent entries + the current phase's task list before starting anything.
2. **One phase gate at a time.** Don't start Phase N+1's primary scope before Phase N's exit criteria (§4) are met, even if it's tempting — a fast/pretty dashboard on top of a kernel that hasn't passed its interruption-timing property tests is wasted work.
3. **Log before you stop**, not just when a phase completes. A half-finished task with no `changes.md` entry is invisible to the other agent.
4. **Flags are requests, not suggestions.** If the previous entry has a non-empty `Flags` addressed to your role, resolve it before starting unrelated new work, unless the current task is more time-critical — and say so explicitly in your own entry if you're deferring a flag.
5. **Disagreement protocol.** If you believe a past decision in `changes.md` or the spec should change, don't silently diverge — log a new entry proposing the change and why, flagged to the other agent, and wait for either their next entry to confirm/counter, or for the human to weigh in.

---

## 6. Non-Negotiable Invariants

Full detail and code in `chronos-project-spec.md` §4 and §8. Restated here because they must never be "optimized away":

1. No effect COMMITs if its recorded epoch differs from the current epoch at commit time.
2. Cancellation decisions are integer comparisons only — never a model call.
3. The Fast Path cannot assert task completion (type-level separation).
4. All model/encoder loads happen only inside the warm-up hook — enforced by a runtime guard, not convention.
5. A correction touching a slot backing an in-flight mutating effect always forces an epoch bump, regardless of classifier confidence.
6. `CancelledError` handlers always re-raise after poisoning — never swallowed.
7. Tool arguments are canonicalized (sorted keys, normalized types) before hashing into an idempotency key.

---

## 7. Tech Stack (finalized — free / standard, deployable)

**Local, reproducible run (mandatory for judging — spec §2.3, §15.7):** Docker + `docker compose up`, single command, no manual steps, no network dependency during scenario execution.

| Layer | Choice | Why |
|---|---|---|
| Backend runtime | Python **3.11**, pinned | Native `asyncio.TaskGroup` — no backport needed. Confirm against the released evaluation kit on Day 0; fall back to `anyio` if the kit mandates 3.10. |
| Web/WS server | FastAPI + Uvicorn | ASGI, native WebSocket support for the telemetry tee, free/open-source, minimal boilerplate |
| Schemas | Pydantic v2 | Already the contract format in spec §7 |
| Tier-2 constrained decoding | `outlines` + a small local **GGUF model** (e.g. Qwen2.5-1.5B-Instruct or Phi-3.5-mini, quantized, via `llama-cpp-python`) | Free, open-weight, CPU-only, runs entirely inside the warm-up hook — keeps the "no external calls during scenario execution" NFR intact. **Do not use a hosted API (even a free one like Groq) for the scored Tier-2 path** — fine for ad-hoc dev experimentation only, never for the harness-facing build. |
| ASR | `faster-whisper` (tiny/base, INT8) | CPU-only, streaming-chunk friendly, free |
| OCR | `pytesseract` (+ `tesseract-ocr` system package) | Lightweight vs. a full VLM; matches the text-extractable use cases in the brief |
| Telemetry | `structlog` → JSONL | 100% trace-coverage requirement (spec NFR-6) |
| Testing | `pytest`, `pytest-asyncio`, `hypothesis` | Property-based tests are the main defense against the hidden set's adversarial timing |
| Dashboard | Next.js 14 (App Router) + TypeScript + Tailwind | Free, open-source, native WebSocket client, no server-state-fighting rerun model (spec §12 explicitly rules out Streamlit for this reason) |
| Containerization | Docker + `docker compose` | Required by the reproducibility gate |
| CI | GitHub Actions | Free for public repos (and ample free minutes for private); run the `pytest`/`hypothesis` suite on every push |

**Optional public deployment (portfolio/demo use — not required for judging):**

| Layer | Free option | Alternative if you outgrow the free tier |
|---|---|---|
| Frontend (dashboard) | **Vercel** Hobby tier | Netlify (also free-tier friendly for Next.js) |
| Backend (FastAPI/WS) | **Render** free Web Service | **Fly.io** free allowance — better for long-lived WebSocket connections since Render's free tier spins down after ~15 min idle |

Keep the deployment config isolated (`/deploy` or `/infra`, plus each service's own Dockerfile) so it never entangles with the judged, local Docker path.

---

## 8. Repo Structure

```
chronos/
├── AGENTS.md                     # this file
├── changes.md                    # shared decision log
├── chronos-project-spec.md       # technical constitution (read-only reference)
├── chronos-architecture-diagram.svg
├── backend/
│   ├── chronos/
│   │   ├── ingress.py
│   │   ├── belief/
│   │   │   ├── tier1.py
│   │   │   ├── tier2.py
│   │   │   └── fusion.py         # Contradiction Resolver
│   │   ├── epoch.py
│   │   ├── ledger.py
│   │   ├── fastpath.py
│   │   ├── planner.py
│   │   ├── effects.py
│   │   ├── multimodal/
│   │   │   ├── asr.py
│   │   │   └── ocr.py
│   │   ├── clock.py
│   │   ├── egress.py
│   │   ├── telemetry.py
│   │   ├── schemas.py            # all Pydantic models, spec §7
│   │   └── harness_adapter.py    # thin, swappable — keep the kernel decoupled from the real kit
│   ├── tests/
│   └── Dockerfile
├── dashboard/                    # Next.js telemetry UI, spec §12
│   └── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci.yml
```

---

## 9. Definition of Done (any task, either agent)

- [ ] Matches the interface contract in spec §7 exactly — no ad-hoc field additions without updating the spec first
- [ ] Doesn't violate any invariant in §6
- [ ] Has a test (unit, property-based, or integration as appropriate) — not just a manual check
- [ ] `changes.md` entry written before ending the session
- [ ] No new external network call introduced on the scenario-execution path (spec NFR-8)
- [ ] If it touches a schema, `chronos-project-spec.md` §7 is updated in the same session — the spec and the code must never silently drift apart

---

## 10. Communication Style

Keep `changes.md` entries and code comments terse and specific — cite spec section numbers instead of re-explaining rationale that's already written down. Assume the reader (the other agent, or future-you) has read the spec once but hasn't memorized it.
