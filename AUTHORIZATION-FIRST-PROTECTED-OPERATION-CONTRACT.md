# Authorization First Protected Operation Contract

> **Decision record — proposed candidate, not production approval.** The
> authorization policy remains `DRAFT — PENDING OWNER RATIFICATION`.
> Decisions 11–36 remain `NOT VERIFIABLE AS NUMBERED`. This contract does not
> implement or enable an operation.

## Decision

Select `prepare_research` as the best existing candidate to become the first
authorization-protected operation: it reads PDF files, extracts source-linked
passages, retrieves relevant text, and returns those passages in
`PreparedResearch` ([`prepare_research`](./src/scientia/workflow.py#L101);
[`PreparedResearch`](./src/scientia/workflow.py#L13)).

This is a candidate selection only. The present function accepts caller-
provided local filesystem paths; it has no authenticated caller, resource
ownership lookup, tenant scope, or authorization check. It is not an
application endpoint and must not be exposed or treated as protected runtime
enforcement. Any future protected operation must resolve a resource through
trusted server-side scope and must not accept a path or object-store key as
authority.

### Candidate comparison

| Existing operation | Concrete behavior | Why selected or deferred |
|---|---|---|
| `prepare_research` | Reads local PDFs, extracts passages, retrieves and returns text-bearing hits. | **Selected candidate.** It is the clearest existing research-content read and can be mapped to `READ_RESEARCH`; its current local path contract is not trusted and must be replaced at a future application boundary. |
| `finalize_research` | Validates supplied assessment provenance and returns a synthesis result ([`finalize_research`](./src/scientia/workflow.py#L191)). | Deferred: consumes caller-supplied assessments and may expose evidence text; review authority and high-stakes finalization rules remain unresolved. |
| `retrieve` / `synthesize` | Rank passages or partition supplied assessments ([`retrieve`](./src/scientia/retrieval.py#L22); [`synthesize`](./src/scientia/synthesis.py#L83)). | Deferred: pure lower-level functions; neither resolves resource ownership nor performs an application operation. |

No existing candidate currently qualifies as a trusted protected boundary.
There are no application routes or protected services wired to the evaluator
or facade ([runtime feasibility assessment](./AUTHORIZATION-RUNTIME-INTEGRATION-FEASIBILITY.md#verdict)).

## Capability and authority distinction

| Category | Evidence or disposition |
|---|---|
| Existing implementation | Local PDF ingestion, retrieval, provenance validation, and pure authorization evaluation exist. These components operate on local paths or supplied in-process facts; they do not authenticate a person or establish tenant ownership ([`prepare_research`](./src/scientia/workflow.py#L101); [`authorize`](./src/scientia/authorization.py#L254)). |
| Proposed contract | A future `READ_RESEARCH` operation resolves the requesting principal and resource from trusted server-side sources, authorizes the exact scoped read, and revalidates before disclosing passages. It must not trust caller-supplied role, membership, assignment, sensitivity, policy, time, or storage locator. |
| Owner decisions | Identity provider/MFA and canonical-account rules; complete role/action and assignment policy; grant authority and duration where confidential access applies; policy authority/integrity; audit access and requirements; whole-policy ratification remain unresolved or pending. See the [ratification readiness checklist](./AUTHORIZATION-RATIFICATION-READINESS.md#3-decision-checklist-and-closure-evidence). |
| Missing infrastructure | Application entry point/service boundary, authentication adapter, authoritative membership/resource repository, scoped source-storage abstraction, ratified policy loader and integrity/rollback controls, trusted clock provider, durable restricted audit, and any queue/job infrastructure. |

## Proposed dependency contract

The order below is a prerequisite chain, not a claim that any dependency
exists. Each dependency must be bound by trusted application composition, not
by request data or test fixtures.

| Order | Dependency | Required contract | Fail-closed condition |
|---|---|---|---|
| 1 | Authenticated canonical principal | An approved authentication boundary verifies the credential/session and produces a canonical subject tied to authoritative account-linking evidence. MFA/assurance is verified when ratified policy requires it. Request fields cannot assert identity or assurance. | Missing, expired, revoked, ambiguous, inconsistent, or unverifiable identity denies before source access. |
| 2 | Tenant/workspace and resource ownership | Resolve the requested resource through an authoritative tenant-scoped repository using server-derived organization/workspace membership. Resolve storage handles only from the scoped resource record; never accept a local path or raw object key from the caller. | Missing resource, cross-tenant mismatch, ambiguous ownership, or repository failure returns no content and performs no source read. |
| 3 | Current membership and assignment eligibility | Load current active membership, roles, and assignment scoped to canonical principal, organization, workspace, and resource. Apply only assignment requirements specified by the ratified role/action policy. | Missing, stale, inactive, revoked, mismatched, or unavailable facts deny. Never infer a role or assignment from the request. |
| 4 | Ratified, integrity-verified policy | Load the approved versioned policy artifact; verify authority, integrity, freshness, supersession, and rollback authorization under ratified rules. Supply the actual approved policy configuration to evaluation. A matching version label alone is insufficient. | Draft, absent, malformed, tampered, stale, superseded, inconsistent, or unauthorized-rollback policy denies. |
| 5 | Trusted server time | Obtain an aware current timestamp from an approved server-controlled source; use it consistently for membership/assignment/grant validity and evaluation. | Clock failure, malformed time, or unapproved source denies; do not fall back to caller time or cached allow results. |
| 6 | Action-specific authorization | Evaluate only `READ_RESEARCH` for the resolved resource and current facts. Enforce the ratified sensitivity, base-role, assignment, and any confidentiality conditions. A confidentiality grant cannot add an action under the recorded U-1 selection, which remains pending ratification. | Any missing or contradictory fact, unconfigured required duration, evaluator error, or deny decision yields no read and no passage disclosure. |
| 7 | Operation-boundary enforcement | Couple authorization to the actual scoped source read using a transaction/consistent snapshot or an explicitly verified equivalent. Revalidate current authority immediately before later disclosure, streaming chunks, cache release, or other externally visible effect. Do not treat a decision object as a transferable permit. | If authorization state changes before the defined operation boundary, stop without releasing subsequent content. |
| 8 | Revocation and asynchronous execution | A synchronous initial implementation is preferred. If a later implementation queues work, bind immutable job identity to verified initiating principal, tenant/workspace, resource, action, and command/idempotency identity. Workers reload current state and reauthorize before reading and releasing content; revocation cancels or safely stops work. | Never trust mutable queue claims or serialized authorization decisions. Missing ownership, changed scope, replay conflict, revocation, or reauthorization failure prevents further reads/releases. |
| 9 | Restricted audit metadata | Where ratified policy requires audit, record only approved security metadata: canonical actor reference, tenant/workspace and resource reference, action, outcome, policy version, server time, and correlation/command reference as authorized. Do not record document content, passage text, credentials, tokens, or raw filesystem paths. Scope audit access and audit reads themselves as ratified. | If a required audit event cannot be durably recorded at the required boundary, fail closed. Do not expose audit data absent approved access rules and restricted storage. |

The trust-boundary and operation-order requirements follow the
[integration plan's identity lifecycle](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#7-identity-and-session-lifecycle),
[tenant isolation](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#6-tenant-isolation),
[service enforcement](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#5-service-enforcement-and-unavailable-operations),
and [audit boundaries](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#8-audit-boundaries).
These documents describe target controls, not current implementation.

## Acceptance criteria for a future implementation

These are evidence requirements for later engineering; they do not supply
policy decisions or authorize development against synthetic facts as if they
were production dependencies.

1. **No effect on missing trust:** tests prove that absent, malformed, stale,
   inconsistent, or unavailable principal, membership, resource, policy, or
   time sources cause denial before opening the source and before returning
   excerpts.
2. **Canonical identity and tenant isolation:** tests prove that caller-
   supplied identity/role/tenant/path values cannot override trusted context;
   an out-of-scope resource cannot be fetched, and cross-tenant cases disclose
   neither passages nor identifying content through errors.
3. **Current eligibility:** tests cover inactive/revoked membership and
   missing, expired, revoked, mismatched, or policy-required absent
   assignments; the operation checks the exact resource and `READ_RESEARCH`
   action.
4. **Policy integrity and rollback:** tests reject modified artifacts, stale
   or superseded versions, and rollback without authorized evidence. A
   synthetic matching version string alone must not produce a trusted-policy
   result.
5. **Time and provider failures:** controlled tests prove that unavailable or
   malformed server time and exceptions from identity, membership, resource,
   policy, source-storage, or required audit providers deny without fallback
   to caller facts, stale allows, or success-shaped responses.
6. **Disclosure-boundary revalidation:** concurrency tests define the
   operation's linearization point and prove a committed membership,
   assignment, grant, sensitivity, ownership, or policy revocation/change
   prevents later chunks, cache releases, and subsequent effects.
7. **Immutable jobs if introduced:** tests prove queue payload mutation,
   principal/resource substitution, replay with a conflicting command, and
   revoked authority prevent worker access or disclosure. The worker reloads
   authoritative state and reauthorizes at execution and release boundaries.
8. **Audit minimization and failure:** tests assert that event records exclude
   document bytes, extracted text, passage text, secrets, credentials,
   tokens, and raw local paths; unauthorized audit access is denied; failure
   to record a required event prevents the corresponding protected effect.
9. **No false enablement:** deployment/configuration tests prove the operation
   remains unavailable unless applicable policy ratification, trusted
   dependency wiring, operation-boundary enforcement, and independent
   verification gates are explicitly satisfied.

## Explicit production holds

Until the relevant owner decisions are ratified and every technical gate
above is implemented and independently verified, keep this candidate and all
other protected operations unavailable. Do not expose `prepare_research` as a
route or service, accept user-provided filesystem paths in an authenticated
operation, or treat the current evaluator/facade as enforcement. In
particular, confidential-content reads, exports, audit access, writes,
deletion/restore, grants, assignments, elevation, review finalization, and
queued protected work remain held
([readiness holds](./AUTHORIZATION-RATIFICATION-READINESS.md#4-protected-operation-holds)).

This contract does not establish policy ratification, production security,
trusted identity, tenant isolation, or a safe deployment. The policy status
remains `DRAFT — PENDING OWNER RATIFICATION`, and Decisions 11–36 remain
`NOT VERIFIABLE AS NUMBERED`.
