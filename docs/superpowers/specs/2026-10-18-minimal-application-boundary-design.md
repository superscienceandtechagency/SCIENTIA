# Minimal Application Boundary Foundation — Design

## Status and purpose

This is a design-stage artifact for Milestone 31, not an implementation
authorization or a production security decision. The selected outcome is to
defer application-boundary code until a real operation invocation path and
authoritative resource source exist.

The authorization policy remains `DRAFT — PENDING OWNER RATIFICATION`.
Decisions 11–36 remain `NOT VERIFIABLE AS NUMBERED`.

## Evidence and problem

The package declares FastAPI as a dependency, but `pyproject.toml` defines no
application entry point or script. The `src/scientia/` package contains
domain, workflow, and authorization modules, but no FastAPI application,
router, executable server module, or application composition root was found.
The package import test proves only that `scientia` imports.

`prepare_research` is currently invoked by workflow tests, not an application
caller. It accepts a `ResearchQuestion`, caller-selected local filesystem
paths, and a retrieval limit. The workflow calls `ingest_pdf`, which reads
those paths using `Path.read_bytes()` and returns source-linked passage text.
No trusted identity, tenant membership, resource ownership repository,
scoped file store, policy artifact source, trusted clock provider, or
operation/audit boundary is present.

The authorization evaluator consumes supplied facts. The existing
`AuthorizationBoundary` accepts injected clock, policy-version metadata, and
facts providers, checks shape and scope consistency, invokes the evaluator,
and returns a decision. The facade does not authenticate its providers,
verify policy integrity, resolve a resource, or bind its decision to a
protected effect. Existing tests use fixed/synthetic dependencies and do not
constitute production authority.

## Decision

Do not add an application factory, route, health-only server shell, generic
dependency container, local/in-memory resource catalog, or unconnected
authorization wrapper in this milestone.

Those alternatives are rejected because:

1. An empty app or health-only endpoint is invokable but does not compose an
   existing research operation or establish the resource boundary.
2. A local/in-memory catalog backed by caller paths or synthetic records
   would invent resource provenance or authority and still would not establish
   tenant ownership.
3. A wrapper around `AuthorizationBoundary` would not protect an actual
   operation, and its allow result could be mistaken for enforcement.

FastAPI's availability supports a future application implementation but does
not itself establish a safe request boundary.

## Future implementation boundary

When prerequisites exist, the actual application entry point should own
request parsing and composition of an authenticated principal. A research
service should own the use case and call a server-side resource resolver
using an opaque resource identifier. The resolver must return a
tenant-scoped resource record and server-controlled storage reference only
after checking current membership/ownership. The service then obtains
ratified policy and trusted time, evaluates the exact action, accesses the
resource through the scoped reference, revalidates immediately before
disclosure, and records required restricted audit metadata.

The concrete module, HTTP protocol, storage model, and dependency container
are intentionally not selected: the repository has no application entry
point, resource repository, or owner-approved deployment/infrastructure
choices from which to select them safely.

## Prerequisites and sequence

1. Establish a real application invocation path and an operation that needs
   the boundary; do not create a route solely to host the boundary.
2. Establish an authoritative resource identity and tenant-scoped resolver
   that never treats a caller-supplied path or object key as ownership.
3. Resolve applicable owner decisions for canonical identity, identity
   provider/MFA, membership authority, complete role/action/sensitivity
   policy, assignment rules, confidential-read policy, and whole-policy
   ratification. Preserve missing historical Decisions 11–36 as
   `NOT VERIFIABLE AS NUMBERED` unless their original authoritative record is
   found.
4. Establish authoritative policy publication, integrity, version,
   supersession, and rollback controls, plus trusted server time.
5. Define operation-level consistency and revocation semantics, restricted
   durable audit requirements, and failure behavior. Keep the initial
   operation synchronous unless a separate approved need requires jobs.
6. Implement the service-bound operation only after the prior evidence and
   contracts exist; test in the assembled application and independently
   verify before any protected enablement.

## Acceptance criteria for a later implementation

- An application test invokes a real research service through its actual
  composition point; no test-only route or provider is represented as
  production infrastructure.
- Requests identify a resource by opaque ID; scoped lookup obtains tenant,
  ownership, sensitivity, and storage reference from authoritative
  server-side state.
- Missing, stale, malformed, inconsistent, or unavailable identity,
  membership, resource, policy, time, storage, or required audit dependencies
  deny before content disclosure.
- Cross-tenant lookup, path traversal/substitution, and forged resource
  ownership cannot open content or leak its existence/content.
- Policy content, integrity, freshness, supersession, and rollback are
  verified; matching version labels alone do not establish trust.
- Authorization and resource state are revalidated at the operation's
  disclosure boundary; revocation races prevent subsequent content chunks or
  effects.
- Any future queued work is immutably bound to verified principal,
  tenant/resource, action, and command identity, reauthorized by the worker,
  and safely stopped after revocation.
- Required audit events are durable and restricted, exclude document text
  and secrets, and failure to record a required event blocks the protected
  effect.
- Confidential reads, exports, audit access, deletion, and every other
  protected operation remain disabled unless the applicable ratified policy,
  engineering gates, and independent verification are complete.

These criteria are design requirements only; existing synthetic component
tests do not satisfy them.

## Non-goals

- No app factory, HTTP route, CLI server, identity provider, database,
  resource catalog, or policy provider is implemented by this design.
- No identity, tenant membership, resource ownership, policy value, or owner
  approval is inferred.
- No protected operation is enabled and no production security readiness is
  claimed.
- This design does not select an identity provider, storage/deployment model,
  retention value, cryptographic scheme, or numeric grant/assignment limit.
