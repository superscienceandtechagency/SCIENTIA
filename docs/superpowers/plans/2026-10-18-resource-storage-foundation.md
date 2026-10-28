# Resource Storage Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Determine whether the repository now has the real application consumer and authoritative resource source required before any resource-storage implementation can be designed safely.

**Architecture:** This is an entry-gate plan, not a storage implementation plan. Re-inspect the current package and evidence; if the real invocation boundary, resource ownership source, and applicable authority evidence are still absent, record the blockers and stop without changing runtime code. Any later storage implementation requires a new or revised approved design that selects its concrete interfaces from evidence.

**Tech Stack:** Python 3.14 package, `uv`, pytest, Ruff; no new runtime dependency or persistence technology is selected.

**Spec:** [Resource Storage Foundation design](../specs/2026-10-18-resource-storage-foundation-design.md)

## Global Constraints

- Preserve policy status `DRAFT — PENDING OWNER RATIFICATION`.
- Preserve `NOT VERIFIABLE AS NUMBERED` for Decisions 11–36 unless their authoritative original record is found and verified.
- Do not infer authenticated identity, tenant membership, resource ownership, policy approval, trusted time, deployment authority, or numeric policy values.
- Do not add a database, migration, resource catalog, generic persistence interface, application factory, route, or unconnected authorization wrapper under this plan.
- Do not enable confidential reads, exports, audit access, deletion, or any other protected operation.
- Do not initialize Git, connect GitHub, push, or claim Git scope verification if the workspace is not a Git repository.
- If the entry gate fails, stop. Do not proceed by replacing missing evidence with test fixtures, local paths, caller claims, or mocks.

## Review Focus

- No application invocation path: verify `src/scientia/` and package entry points; absence means no service module can yet own the integration.
- No authoritative resource ownership source: distinguish local file paths and in-memory domain records from server-controlled tenant/resource records.
- No owner-ratified policy: ensure policy drafts, conversation summaries, evaluator behavior, and tests are not treated as authorization authority.
- No trusted provider composition: distinguish injected test fakes from identity, membership, policy, time, storage, and audit providers wired for a real application.
- No operation-level consistency: ensure a component-level allow or matching version label is not mistaken for revalidation at content access and disclosure.

---

### Task 1: Revalidate implementation entry conditions

**Files:**
- Read: `pyproject.toml`
- Read: `src/scientia/`
- Read: `tests/`
- Read: `AUTHORIZATION-FIRST-PROTECTED-OPERATION-CONTRACT.md`
- Read: `AUTHORIZATION-FIRST-OPERATION-READINESS.md`
- Read: `AUTHORIZATION-SERVER-SIDE-RESOURCE-BOUNDARY-DESIGN.md`
- Read: `AUTHORIZATION-RATIFICATION-READINESS.md`
- No runtime files are created or modified by this gate.

**Interfaces:**
- Consumes: current repository source, tests, package configuration, and the approved [design spec](../specs/2026-10-18-resource-storage-foundation-design.md).
- Produces: an evidence-based gate result identifying (a) an actual application invocation path, (b) its resource-resolution source, (c) authoritative tenant/resource ownership evidence, and (d) applicable ratified policy/provider prerequisites—or the exact missing items.

- [ ] **Step 1: Inspect package and executable entry points**

Run:

```bash
find src/scientia -maxdepth 2 -type f -name '*.py' -print
rg -n 'FastAPI\\(|APIRouter\\(|@app\\.|@router\\.|\\[project\\.scripts\\]|uvicorn' pyproject.toml src tests
```

Expected: identify a real application composition root and operation invocation path, if one exists. A declared FastAPI dependency or import without an app/consumer does not pass this criterion.

- [ ] **Step 2: Inspect resource and persistence evidence**

Run:

```bash
rg -n 'sqlite|sqlalchemy|sqlmodel|alembic|psycopg|asyncpg|migration|CREATE TABLE|read_bytes|pdf_paths|resource_id|organization_id|workspace_id' pyproject.toml src tests
```

For every candidate resource source, trace where ownership is established and whether content access uses a server-controlled resource record. A local path, synthetic fixture, or `Source`/`Passage` ID alone does not pass.

- [ ] **Step 3: Check authority and provider prerequisites**

Read the exact status and unresolved-decision sections in the ratification readiness document and compare them with current source. Do not infer closure from code or passing tests. Confirm that applicable identity, membership, resource ownership, role/action/sensitivity policy, policy integrity, trusted-time, audit, and revocation requirements have authoritative evidence before marking any of them resolved.

- [ ] **Step 4: Apply the stop condition**

Proceed only if a real application operation consumes an authoritative, tenant-scoped resource source and the applicable authority/provider requirements are evidenced. If any item is absent:

1. Do not edit runtime code or dependency manifests.
2. Record which entry conditions remain missing and the source evidence.
3. Keep all protected operations unavailable.
4. Stop this plan. A later implementation requires a new evidence-backed design naming the concrete operation, resource source, interfaces, storage choice, and tests.

Current expected result from the approved design: **blocked** because no application entry point, protected service, resource repository, or authoritative resource ownership contract is present. Re-check current repository state; do not assume this expected result without inspection.

- [ ] **Step 5: Run project checks only if source/configuration changed**

If the gate is blocked and no files changed, no test, lint, or build run is required for this read-only gate. If an independently authorized later task changes code or dependencies, run:

```bash
uv run --locked pytest
uv run --locked ruff check .
uv run --locked python -c 'import scientia'
```

Do not interpret these component/package checks as proof of resource ownership, application authorization, or production security.
