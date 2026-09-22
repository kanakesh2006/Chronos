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

### [Phase 0] Kernel Scaffolding — 2026-09-21
Antigravity : Created Phase 0 implementation plan and task list artifacts. Scaffolded Pydantic schemas, `VirtualClock` façade, `EpochArbiter`, Two-Phase `EffectGateway`, and `SnapshotLedger` adhering to invariants 1, 5, 6, and 7 per spec §8. Enforced session-scoped class instantiations instead of module-level globals.
Opencode : 
Files: `backend/chronos/schemas.py`, `backend/chronos/clock.py`, `backend/chronos/effects.py`, `backend/chronos/epoch.py`, `backend/chronos/ledger.py`, `changes.md`
Flags: [OpenCode] Scaffold interfaces are ready. Please implement the `hypothesis` property-based test suite for `EpochArbiter` and `EffectGateway` under randomized interruption timings. **Do not start Phase 1 until the test suite proves Invariants 1, 5, 6, 7 hold.**
