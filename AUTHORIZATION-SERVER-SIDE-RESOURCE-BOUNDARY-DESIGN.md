# Authorization Server-Side Resource Boundary Design

> **Design only — not implemented or approved for production.** Policy status
> remains `DRAFT — PENDING OWNER RATIFICATION`; Decisions 11–36 remain
> `NOT VERIFIABLE AS NUMBERED`. No route or protected operation is enabled.

## Decision and repository evidence

The first candidate remains `prepare_research`: it reads PDFs, extracts
source-linked passages, retrieves text, and returns those passages. Its
current API accepts local filesystem paths, and `ingest_pdf` calls
`Path.read_bytes()` on each path
([`prepare_research`](./src/scientia/workflow.py#L101);
[`ingest_pdf`](./src/scientia/pdf_ingestion.py#L63)). Those paths do not prove
tenant ownership or permission. The current workflow is called by tests, not
an application request handler. No FastAPI application, router, protected
service, or authoritative resource repository exists in the inspected
`src/scientia/` package
([package inventory](./AUTHORIZATION-FIRST-OPERATION-READINESS.md#candidate-evidence);
[runtime feasibility](./AUTHORIZATION-RUNTIME-INTEGRATION-FEASIBILITY.md#verdict)).

The authorization evaluator accepts supplied facts. The
`AuthorizationBoundary` is an internal decision facade: it obtains an
injected time and policy-version label, loads injected facts, checks basic
shape/scope/version consistency, calls the evaluator, and returns a decision.
It does not resolve or read a resource, authenticate providers, verify policy
integrity, or enforce an operation
([`AuthorizationBoundary`](./src/scientia/authorization_boundary.py#L159);
[`evaluate`](./src/scientia/authorization_boundary.py#L186)).

**No runtime implementation is justified in this milestone.** There is no
real application entry point to attach it to, nor a trusted resource source to
resolve. FastAPI being a declared dependency does not establish an application
or trusted boundary ([`pyproject.toml`](./pyproject.toml#L5)).

## Proposed ownership and boundary

When an actual application entry point and authoritative resource source are
available:

- The **application entry point** owns request parsing, authentication
  composition, and binding the verified request identity to the service call.
  It accepts a resource identifier, never a filesystem path or storage key.
- A **research operation service** in the `scientia` application/service
  layer owns the use case: resolve the resource, obtain current authorization
  facts and policy/time dependencies, authorize the exact action, invoke
  scoped content access, revalidate at the disclosure boundary, and emit any
  required audit metadata.
- The **resource repository/resolver** owns the mapping from an opaque
  resource identifier and trusted tenant context to a server-controlled
  resource record. It must return a scoped storage reference only after
  verifying organization/workspace ownership and current membership.
- `workflow.prepare_research` remains local PDF processing/retrieval logic;
  it must not become the application entry point or a source of identity,
  ownership, or authorization facts. `AuthorizationBoundary` remains a
  decision component unless it is deliberately extended by a separately
  reviewed design to bind an authorization decision to an operation.

There is currently no `scientia` application/service module or composition
root to name as the concrete owner. Do not create a nominal entry point or
choose a web framework merely to host a security-looking wrapper. Select the
concrete module only when a real application invocation path and resource
repository are introduced.

## Proposed flow

This order is a target contract, not current behavior:

1. The application boundary authenticates the request under an approved
   identity/session contract and passes an authenticated canonical principal
   through trusted internal context.
2. The service accepts an opaque resource ID and resolves it through an
   authoritative repository scoped by that principal's current
   organization/workspace membership. It obtains sensitivity and a
   server-controlled storage reference from the resolved record.
3. The service obtains current assignment facts as required by the ratified
   role/action policy, a ratified integrity-verified policy artifact, and
   trusted server time. Caller fields cannot override any of these.
4. The service evaluates exactly `READ_RESEARCH` for the resolved resource.
   A deny or unavailable/inconsistent dependency causes no source read and no
   content disclosure.
5. The service reads only through the resolved scoped resource reference.
   It uses a consistent snapshot/transaction or a verified equivalent to bind
   ownership and authorization to the read. Before returning passages or
   releasing later chunks/cache results, it revalidates current authority and
   resource state.
6. If ratified policy requires an audit event, the service records restricted
   metadata at the required boundary. Audit failure prevents the protected
   effect when required by policy. Audit records exclude document/passage
   content, credentials, secrets, and raw local paths.

For this initial candidate, prefer synchronous execution. If asynchronous
processing is later required, it is a separate capability: bind the job
immutably to verified principal, tenant/workspace, resource, action, and
command identity; workers must reload authoritative state, reauthorize before
reading and releasing content, and stop safely on revocation.

## Minimum contract

### Request

The future operation may accept:

- an opaque resource identifier (not a path, object key, tenant claim, or
  ownership assertion);
- a validated research question; and
- a bounded retrieval parameter only if product/API policy defines and
  validates it.

The authenticated principal is supplied by trusted application composition,
not deserialized from the operation payload. No caller-provided role,
membership, assignment, sensitivity, policy version, authorization time, or
storage locator is authoritative.

### Resolved resource

The server-side resource record must bind, at minimum, the canonical resource
ID, organization and workspace ownership, sensitivity/classification, and an
opaque storage reference. The resolver must establish that the resource
belongs to the requested scope and that the principal has current membership
there before content access. File metadata is not authority for tenant or
resource ownership. If this minimum cannot be proven from authoritative
state, return no content.

### Result and errors

On success, return a typed research-preparation result containing only
passages authorized for that resolved resource and the source/location
provenance required by the workflow contract. Do not mix results across
resources or tenants.

On failure, return no partial protected content. At the application boundary,
use a non-sensitive error shape that does not reveal whether an inaccessible
resource exists; preserve a safe internal diagnostic category for
authorization/provider/audit failures without copying document content or
secrets into logs. Do not convert provider errors, missing policy, or audit
failure into success-shaped empty results.

The precise external status codes and existence-disclosure behavior must be
selected consistently with the eventual application protocol; no route or
protocol is chosen here.

## Dependency contract and ownership

| Dependency | Required evidence/owner | Current classification | Safe default |
|---|---|---|---|
| Application invocation and service composition | Application owner establishes a real request entry point and service lifecycle; engineering binds trusted dependencies there. | **Missing infrastructure.** No route/application entry point or protected service is present in the inspected package. | Do not add a fake route or unconnected service wrapper. |
| Authenticated canonical principal and MFA | Owner ratifies identity-provider/session and MFA assurance requirements; trusted adapter establishes canonical identity and verified assurance. | **Missing infrastructure; owner decisions unresolved.** | Reject missing or unverifiable identity; never accept caller-supplied identity/MFA claims. |
| Tenant membership and resource ownership | Authoritative identity/membership and resource repository owners provide current scoped lookups and auditable ownership provenance. | **Missing infrastructure.** Current `pdf_paths` do not establish ownership. | Do not open source content based on caller path or identifier alone. |
| Assignment and role/action policy | Owner ratifies complete role/action/sensitivity and assignment rules, including applicable confidential-read conditions. | **Unresolved owner decisions; policy status pending.** | Deny undefined or policy-dependent access. Preserve `DRAFT — PENDING OWNER RATIFICATION`. |
| Policy publication, integrity, version and rollback | Authorized policy owner supplies the ratified artifact and rules for verification, supersession, keys if used, and rollback. | **Missing infrastructure; owner authority unresolved.** Existing version labels are metadata only. | Reject missing, draft, tampered, stale, mismatched, superseded, or unauthorized rollback policy. |
| Trusted server time | Runtime/operations owner supplies a health-checked server clock; the operation uses it for time-bounded facts. | **Synthetic test-only clock; no production provider.** | Deny when time is unavailable, malformed, or unverifiable; never fall back to client time. |
| Scoped content source | Resource/storage owner provides a scoped read by resolved resource record, not arbitrary path. | **Missing infrastructure.** Local PDF ingestion reads filesystem paths. | No content read until scope is established by a trusted resolver. |
| Operation consistency and revocation | Service/storage owners define snapshot/transaction or equivalent and the disclosure linearization point; engineering proves revalidation on the effect boundary. | **Missing infrastructure.** No protected service, transaction, or effect boundary exists. | Do not reuse a prior allow; stop before subsequent disclosure when current authorization cannot be verified. |
| Audit access and durability | Owner ratifies audit authority, scope, retention, and event requirements; storage/security owners implement restricted durable recording. | **Missing infrastructure; owner decisions unresolved.** | Do not claim an audit trail; fail closed if a required event cannot be durably recorded. |
| Queued work | Only needed if a later product requirement adds asynchronous reads; job owner defines immutable identity, tenant/resource scope, reauthorization, and cancellation. | **No queue exists; not required for initial synchronous candidate.** | Do not create jobs. If added later, deny execution on missing ownership or failed reauthorization. |

Overall policy status remains `DRAFT — PENDING OWNER RATIFICATION`; Decisions
11–36 remain `NOT VERIFIABLE AS NUMBERED`. Engineering evidence and synthetic
tests do not close owner decisions or supply authoritative policy.

## Rejected shortcuts

- **Accepting a caller path:** path syntax and filesystem readability prove
  neither ownership nor authorization.
- **Adding a fake route or test-only identity provider:** it would test an
  invented integration and could be mistaken for a production boundary.
- **Adding an unconnected wrapper around `AuthorizationBoundary`:** the
  facade returns a decision but does not bind it to the subsequent resource
  read or protect against time-of-check/time-of-use races.
- **Treating a version string as trusted policy:** matching labels do not
  prove policy contents, ratification, freshness, or rollback authorization.
- **Treating source IDs, PDF metadata, role labels, account IDs, or test
  fixtures as ownership/identity evidence:** none establishes authoritative
  tenant membership or canonical identity.
- **Using an evaluator allow as a transferable permit:** the future service
  must revalidate at the actual content-disclosure boundary.

## Acceptance tests for a future implementation

Before the operation can be exposed, an assembled-system test suite must
demonstrate:

1. An unauthenticated, ambiguous, revoked, or unverifiable principal cannot
   trigger a source open or receive content; caller-supplied identity/MFA
   values do not override trusted context.
2. A cross-tenant or workspace-mismatched resource cannot be opened; raw
   paths, object keys, and forged tenant/resource ownership claims cannot
   steer storage access.
3. Missing, inactive, stale, revoked, or inconsistent membership and required
   assignment facts deny before source access.
4. Missing, draft, tampered, stale, superseded, mismatched, or unauthorized-
   rollback policy denies; a matching version label alone is insufficient.
5. Missing, malformed, or unavailable server time and failures from any
   required identity, membership, resource, policy, storage, or audit provider
   fail closed without returning partial content or success-shaped fallbacks.
6. Authorization and ownership changes racing with the read cannot authorize
   later disclosure; after revocation is committed, subsequent chunks,
   cache releases, and effects stop. Tests establish the operation's
   consistency/linearization point.
7. If a queue is later added, altered/replayed job payloads cannot change
   immutable owner, tenant, resource, or action; workers reauthorize before
   read and release, and revocation cancellation prevents subsequent effects.
8. Required audit events are restricted and durable, audit failures block the
   required effect, and records omit document/passage content, credentials,
   secrets, and raw local paths.
9. Policy and technical gates are independently verified before enablement;
   tests against fakes alone do not satisfy this criterion.

These tests are future acceptance criteria, not tests already present or
evidence of production security. Existing synthetic facade tests demonstrate
only component-level shape, time, provider-error, and selector checks
([boundary tests](./tests/test_authorization_boundary.py#L179)).

## Smallest prerequisite and production holds

The smallest prerequisite before implementation is a real application
invocation path **and** an authoritative server-side resource resolver that
maps an opaque resource ID to a tenant-owned record and scoped storage
reference. The repository has neither, so no package module can yet
responsibly own this boundary. Once those exist, select the concrete service
module at the real composition point and re-evaluate the unresolved identity,
policy, time, audit, and revocation dependencies before wiring access.

Keep production authentication and all protected operations unavailable,
including public or confidential protected reads, exports, audit access,
writes, deletion/purge/restore, classification changes, review submission or
finalization, grant/assignment lifecycles, administrator elevation, and
queued protected work. In particular, do not expose `prepare_research` with
caller-controlled paths. These holds are readiness requirements, not runtime
controls currently enforced by the evaluator, facade, or this design
([readiness holds](./AUTHORIZATION-RATIFICATION-READINESS.md#4-protected-operation-holds)).
