# Authorization First Operation Readiness

> **Readiness review only.** The policy remains
> `DRAFT — PENDING OWNER RATIFICATION`; Decisions 11–36 remain
> `NOT VERIFIABLE AS NUMBERED`. No protected operation is enabled by this
> document.

## Verdict

An isolated authorization integration step for `prepare_research` is **not
justified yet**. It is the most concrete existing research-content read
candidate, but it is a local workflow function, not an application service or
trusted resource boundary. It accepts caller-provided filesystem paths and
returns extracted passages; no authenticated identity, resource ownership,
tenant scope, policy, or effect-boundary revalidation is present
([`prepare_research`](./src/scientia/workflow.py#L101);
[`ingest_pdf`](./src/scientia/pdf_ingestion.py#L63)).

The smallest safe prerequisite is to establish a real server-side operation
and resource-resolution boundary: identify how a protected request reaches
the operation and how an authorized server-side source resolves a tenant-
scoped resource without caller-supplied paths or object keys. No such route,
service, or resource repository exists in the inspected project, so creating
an authorization wrapper now would be unconnected and potentially
misleading. Do not implement or expose the candidate until that prerequisite
and its applicable authority decisions are available.

## Candidate evidence

| Aspect | Repository evidence | Readiness implication |
|---|---|---|
| Operation | `prepare_research(question, pdf_paths, limit)` ingests each path, flattens passages, ranks them against the question, and returns `PreparedResearch` ([workflow](./src/scientia/workflow.py#L101); [result record](./src/scientia/workflow.py#L13)). | Concrete content-read behavior exists; its future mapping to a protected `READ_RESEARCH` action must be made at a real operation boundary and remain subject to ratified policy. |
| Callers | Search of Python sources found its only call sites in `tests/test_workflow.py`; no application caller or route was found. | No production request path exists to protect or exercise end to end. |
| Inputs | Question text, a sequence of local filesystem paths, and a caller-selectable result limit. `ingest_pdf` constructs a `Path`, checks `is_file()`, and calls `read_bytes()` ([workflow](./src/scientia/workflow.py#L101); [PDF read](./src/scientia/pdf_ingestion.py#L63)). | A path is a locator, not evidence of tenant ownership or authorization. The current API cannot be treated as trusted resource resolution. |
| Outputs | `PreparedResearch` contains ingestion records and retrieval hits; passages retain extracted text, source IDs, and page locations ([`PreparedResearch`](./src/scientia/workflow.py#L13); [`Passage`](./src/scientia/evidence.py#L69)). | Returned passages disclose document content. Resource sensitivity and entitlement are not determined by this function. |
| Side effects | Reads files into memory, parses and extracts text, creates in-memory records/UUIDs, and computes retrieval results. It does not persist, mutate, export, enqueue, or audit. | Local reads can still disclose content; absence of durable writes does not make a public/application boundary safe. There is no operation-level transaction or revalidation point. |
| Related workflow | `finalize_research` validates provenance of supplied assessments and synthesizes them ([workflow](./src/scientia/workflow.py#L191)). Retrieval and synthesis are pure operations over supplied records ([`retrieve`](./src/scientia/retrieval.py#L22); [`synthesize`](./src/scientia/synthesis.py#L83)). | Do not treat provenance validation, retrieval, synthesis, or `HUMAN_REVIEWED` values as authentication, tenant isolation, reviewer independence, or protected-service authorization. |

## Prerequisite classification

Statuses describe current repository evidence, not deployment state or
production readiness.

| Prerequisite | Classification | Evidence / gap | Safe default |
|---|---|---|---|
| Local PDF parsing and passage provenance | **Verified existing capability** | `ingest_pdf` reads local file bytes, hashes them, extracts page text, and returns source-linked passages ([PDF ingestion](./src/scientia/pdf_ingestion.py#L63); [workflow tests](./tests/test_workflow.py#L115)). | Use only as a local processing capability; do not infer access rights from its inputs or outputs. |
| Pure action evaluator | **Verified existing capability** | `authorize` evaluates supplied facts; it does not authenticate or verify their provenance ([`authorize`](./src/scientia/authorization.py#L254)). | Treat results as in-process decisions only, never as application enforcement. |
| Authorization facade test behavior | **Synthetic test-only capability** | Unit tests use fixed clock, version, and facts fakes; they exercise time replacement, selector checks, and fail-closed behavior ([boundary tests](./tests/test_authorization_boundary.py#L357); [scope test](./tests/test_authorization_boundary.py#L451); [time test](./tests/test_authorization_boundary.py#L472)). | Do not treat fixtures or matching version labels as trusted providers or policy evidence. |
| Application entry point / protected service | **Missing infrastructure** | No application route or caller of the boundary/evaluator appears in `src/`; the only `prepare_research` callers are tests. | Do not add an isolated wrapper or expose a route in this readiness step. |
| Canonical authenticated principal and MFA evidence | **Missing infrastructure; unresolved owner decision** | No authentication adapter exists. Provider, MFA assurance, and canonical account-linking choices remain unresolved ([readiness identity checklist](./AUTHORIZATION-RATIFICATION-READINESS.md#identity-and-authentication)). | Do not trust request identity, role, tenant, or MFA claims. |
| Tenant/workspace membership and resource ownership | **Missing infrastructure** | There is no authoritative membership/resource repository or scoped file store. Current local path input cannot establish ownership. | Resolve resources only from a future trusted server-side tenant-scoped source; reject caller paths and raw object keys as authority. |
| Assignment eligibility and capability policy | **Unresolved owner decision; blocked by absent authoritative evidence** | Assignment conditions and full action/sensitivity matrix are not ratified; grant/assignment durations remain unresolved. | Deny when a required assignment or policy fact cannot be authoritatively loaded. Do not insert synthetic/default values. |
| Ratified policy artifact and integrity/rollback controls | **Missing infrastructure; blocked by absent authoritative evidence** | No policy loader or integrity verification exists; the facade's version metadata is not policy integrity. Policy status is pending ratification. | Load no draft or unverifiable policy as production authorization configuration. |
| Trusted server time | **Synthetic test-only capability; missing infrastructure** | The facade accepts an injected clock and tests use fixed clocks; no production clock provider is wired ([clock contract](./src/scientia/authorization_boundary.py#L78); [clock failure test](./tests/test_authorization_boundary.py#L179)). | Deny on missing, malformed, or unavailable time; never use caller time. |
| Operation-level revalidation / revocation consistency | **Missing infrastructure** | No resource operation, transaction, consistency strategy, or disclosure boundary exists. Evaluator checks only supplied validity/revocation facts at evaluation time. | Do not reuse an earlier allow. Future reads must revalidate before disclosure and prevent stale state from authorizing later chunks or effects. |
| Durable restricted audit | **Missing infrastructure; unresolved owner decision** | No audit storage exists; audit access and retention authority remain open ([audit checklist](./AUTHORIZATION-RATIFICATION-READINESS.md#audit-retention-deletion-and-recovery)). | Do not claim an audit trail exists. If policy later requires a durable event, fail closed when it cannot be recorded. |
| Immutable jobs and cancellation | **Missing infrastructure** | No queue or background job path exists. | Prefer synchronous execution initially. If jobs are later introduced, bind ownership immutably and reload/re-authorize before access and release. |
| Whole-policy ratification and Decisions 11–36 source | **Unresolved owner decision; blocked by absent authoritative evidence** | Ratification is pending and the original numbered record has not been verified in inspected project materials ([readiness status](./AUTHORIZATION-RATIFICATION-READINESS.md#1-overall-status-and-evidence-basis)). | Preserve `DRAFT — PENDING OWNER RATIFICATION` and `NOT VERIFIABLE AS NUMBERED`; do not reconstruct history or enable policy-sensitive operations. |

## Critical dependency order

The future dependency sequence for a protected read is:

1. **Real operation boundary and server-side resource resolution.** Establish
   how the request reaches the service and how resource identity and storage
   access are scoped independently of caller-supplied paths.
2. **Authenticated canonical principal.** Resolve verified identity and any
   required assurance; then load current membership and assignment from
   authoritative sources.
3. **Ratified policy and integrity verification.** Establish the approved
   role/action/sensitivity rules, policy source, version/supersession, and
   rollback authority before loading configuration.
4. **Trusted server time.** Supply the current time to policy checks; failure
   or inconsistency must deny.
5. **Action-specific authorization.** Evaluate exactly the requested
   `READ_RESEARCH` against trusted facts and applicable policy. Confidential
   access remains separately held until its policy and technical prerequisites
   are complete.
6. **Operation-level revalidation and disclosure.** Couple fresh authorization
   state to the scoped resource read and revalidate before later chunks,
   derived-content reuse, or other disclosure. Define and test revocation
   ordering.
7. **Required audit.** Record only approved metadata, exclude document text and
   secrets, restrict audit access, and prevent the protected effect if a
   required durable event fails.
8. **Asynchronous work only if later needed.** Bind immutable principal,
   tenant, resource, action, and command/job identity; reauthorize in workers
   and stop safely on revocation. No queue is required for the current local
   workflow, and none should be invented for this candidate.

Cross-tenant denial must hold at resource resolution and every storage or
derived-data boundary. A stale policy label, stale membership or assignment,
clock failure, provider error, ownership mismatch, or unavailable required
audit must fail closed. A revocation committed after an initial check must
prevent subsequent disclosure or effects. Detailed target requirements are in
the [integration plan](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#5-service-enforcement-and-unavailable-operations)
and [tenant-isolation section](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#6-tenant-isolation);
they are not implemented controls.

## Acceptance criteria before implementation or enablement

These are gates for a future real service, not evidence that it exists:

- A concrete application invocation path and server-side resource resolver
  are identified; the resolver cannot be steered to an arbitrary local path
  or cross-tenant resource by request data.
- An approved identity contract yields a canonical principal, and authoritative
  membership, resource ownership, assignment, and sensitivity facts are
  loaded for that principal and resource.
- A whole-policy ratification record exists, including applicable
  role/action/sensitivity and confidential-read rules. Policy loading verifies
  integrity, version/freshness, supersession, and authorized rollback rather
  than comparing labels alone.
- Trusted server time and all authoritative providers have explicit failure
  behavior. Missing, stale, malformed, inconsistent, or unavailable required
  facts cause denial before source access or content disclosure.
- Tests prove cross-tenant requests cannot open source content, and caller-
  supplied identity, roles, assignments, tenant, paths, or policy cannot
  override trusted state.
- Concurrency tests define the read's consistency/linearization boundary and
  prove revocation prevents later chunks, cache releases, and subsequent
  disclosure. Any future job is immutably owned and reauthorized at execution
  and release.
- Required audit metadata is durably recorded and access-restricted; tests
  prove records contain no document/passage text, credentials, secrets, or
  raw local paths, and audit failure prevents a required protected effect.
- Independent verification confirms operation-level enforcement and that
  every protected operation remains unavailable unless its own policy and
  technical gates are satisfied.

## Smallest safe next prerequisite

Before adding authorization wiring, establish one real server-side operation
boundary and its authoritative resource-resolution contract for the selected
research read. This requires evidence of an actual application invocation
path and a trusted way to map its request to a tenant-owned source. The current
repository provides neither. Do not satisfy this prerequisite with a fake
route, test-only identity provider, in-memory mock authority represented as
production, or an unconnected wrapper. Until a real boundary and its
authoritative dependencies exist, further progress should remain
documentation/design or isolated component testing that does not claim
integration.

## Explicit holds

No production authentication or protected operation is ready. Keep
confidential-content reads, public protected reads, writes, exports, audit
access, deletion/purge/restore, classification changes, review submissions
and finalization, grant and assignment lifecycle operations, administrator
elevation, and queued protected work unavailable until their applicable owner
decisions are ratified and end-to-end controls are implemented and
independently verified. The evaluator and facade do not enforce these holds
at application boundaries ([ratification readiness holds](./AUTHORIZATION-RATIFICATION-READINESS.md#4-protected-operation-holds)).
