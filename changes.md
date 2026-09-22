# changes.md — Chronos Decision Log

Append-only. Never edit or delete a past entry — if a decision changes, log a new entry that supersedes it and says so. See `AGENTS.md` §3 for the full protocol.

Format:
```
### [Phase N] <short title> — <YYYY-MM-DD>
Antigravity : <what changed / decided and why>
Opencode : <what changed / implemented / fixed and why>
Files: <paths touched>
Flags: <handoff notes for the other agent, or "none">
```

Read at least the last 10 entries (or all of it, if shorter) before starting work each session.

---

### [Phase -1] Project setup — 2026-09-19
Antigravity : n/a — this entry predates any agent session.
Opencode : n/a — this entry predates any agent session.
Files: `chronos-project-spec.md`, `chronos-architecture-diagram.svg`, `AGENTS.md`, `changes.md` created/finalized as the reference set for the build. Tech stack decided per `AGENTS.md` §7 (Python 3.11 + FastAPI backend, Next.js dashboard, Docker for judged reproducibility, Vercel/Render for optional public deploy).
Flags: Phase 0 (Kernel) has not started. First real session should begin there — see `AGENTS.md` §4. Confirm target Python version (3.10 vs. 3.11 vs. 3.12) against the official evaluation kit the moment it's released, per spec §11 note.

---

<!-- New entries go below this line, newest last. -->

### [Phase 0] Kernel Scaffolding & Hardening — 2026-09-22
Antigravity : Scaffolded Pydantic schemas, `VirtualClock` façade, `EpochArbiter`, Two-Phase `EffectGateway`, and `SnapshotLedger` per spec §8. Then wrote the `hypothesis` property-based tests for `EpochArbiter` and `EffectGateway` under randomized interruption timings, asserting Invariants 1, 5, 6, and 7. Wrote unit tests for `SnapshotLedger`. All 4 tests passed, confirming Phase 0 exit criteria.
Opencode : (Decommissioned, tasks reassigned to Antigravity)
Files: `backend/chronos/schemas.py`, `backend/chronos/clock.py`, `backend/chronos/effects.py`, `backend/chronos/epoch.py`, `backend/chronos/ledger.py`, `backend/tests/test_invariants.py`, `backend/tests/test_ledger.py`, `changes.md`
Flags: Phase 0 is complete. Proceeding to Phase 1 (Fast Path & Egress).

### [Phase 1] Fast Path & Egress — 2026-09-23
Antigravity : Built the `FastPathEmitter` with monotonic `floor_token` tracking and strictly restricted return types (`SpokenAction | ClarificationAction`) ensuring structural compliance with Invariant 3. Developed the `EgressSerializer` implementing fail-closed validation with a single structural repair attempt and a final degraded fallback, alongside the telemetry tee for JSONL output. Included exhaustive tests for both modules.
Files: `backend/chronos/fastpath.py`, `backend/chronos/egress.py`, `backend/tests/test_fastpath.py`, `backend/tests/test_egress.py`, `changes.md`
Flags: Phase 1 is complete. Moving on to Phase 2 (Multimodal).

### [Phase 2] Multimodal & Belief Pipeline — 2026-09-23
Antigravity : Implemented `ASRWorker` using `faster-whisper` with `ModelLoadGuard` to enforce warm-up constraints, and `OCRWorker` using `pytesseract`. Built the Tier-1 Lexical Fast-Filter (`tier1.py`) for sub-millisecond keyword and disfluency detection, and the Contradiction Resolver (`fusion.py`) mirroring the priority table from the spec (visual > audio for identity slots, audio > visual for intent) and hard-override check. Fully unit-tested all contradiction logic rows and tier 1 checks. All tests passed.
Files: `backend/chronos/multimodal/asr.py`, `backend/chronos/multimodal/ocr.py`, `backend/chronos/belief/tier1.py`, `backend/chronos/belief/fusion.py`, `backend/tests/test_belief.py`, `changes.md`
Flags: Phase 2 is complete. Proceeding to Phase 3 (Planner & Clock Supervisor).
