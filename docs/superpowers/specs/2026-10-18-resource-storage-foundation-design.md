# Resource Storage Foundation — Design

## Status and purpose

This design records a readiness decision for SCIENTIA's resource storage and
persistence foundation. It does not authorize application implementation or
production deployment.

The authorization policy remains `DRAFT — PENDING OWNER RATIFICATION`.
Decisions 11–36 remain `NOT VERIFIABLE AS NUMBERED`.

## Repository evidence

The project is a Python package under `src/scientia/`. `pyproject.toml`
declares FastAPI, Pydantic, and pypdf, but defines no application script or
entry point. No database client, ORM, migration tool, database configuration,
schema, migration, or persistence model was found in the inspected
repository.

The current `prepare_research` workflow accepts local filesystem paths and
uses `ingest_pdf`, which reads the path's bytes. Its call sites are in
workflow tests; there is no application request path, tenant context, or
authoritative resource repository. Its in-memory `Source` and `Passage`
records carry IDs, content hash, metadata, and provenance, but not verified
tenant ownership or durable storage identity.

The authorization evaluator accepts supplied principal, membership,
resource, assignment, grant, policy, and time facts. The
`AuthorizationBoundary` injects clock, policy-version metadata, and facts
providers and returns a decision; no provider implementation or operation
boundary is wired to it. Existing test providers are synthetic fixtures, not
production authority.

## Decision

Do not add database dependencies, a database service, schema/migrations, an
in-memory resource catalog, a generic persistence interface, an application
factory, or an unconnected wrapper in this milestone.

This is not a judgment that persistence is unnecessary. It is a scope and
evidence decision: no real application consumer or authoritative resource
ownership contract exists. Adding storage now would require choosing what
entity owns a resource, how its tenant/workspace is established, how source
bytes are addressed, and who may access it. Those facts and authorities
cannot be derived from paths, test fixtures, source metadata, or conversation
summaries.

## Target ownership boundary

Once an actual application operation and authoritative ownership source are
established:

- The **application entry point** composes authenticated request context; it
  does not accept caller-provided ownership claims as trusted.
- A **resource repository/resolver** maps an opaque resource identifier and
  trusted tenant context to a server-controlled record. It establishes
  current membership and ownership before returning a scoped storage
  reference.
- A **research service** owns the protected use case and binds current
  identity, membership, resource ownership, policy, time, authorization, and
  content access at the operation boundary.
- A **storage adapter** reads bytes only through the resource record's scoped
  server-controlled reference. It does not interpret client paths or object
  keys as authorization.
- The existing `workflow.prepare_research` remains local PDF processing and
  retrieval logic; it is not an application entry point or ownership source.

No concrete module, database engine, storage provider, or migration system is
selected. Choose these only in a later design based on an actual application
consumer, approved resource ownership contract, operational requirements,
and deployment decisions.

## Required resource contract

A future authoritative resource record must establish, at minimum:

- a canonical opaque resource identifier;
- authoritative organization and workspace ownership;
- current resource existence and lifecycle state;
- sensitivity/classification as controlled by an approved authority;
- a server-controlled storage reference that callers cannot substitute; and
- provenance sufficient to bind stored content and derived passages to the
  same resource.

The resolver must perform a tenant-scoped lookup using authenticated
server-side context. It must not trust local filesystem paths, object-store
keys, PDF metadata, source IDs, or tenant/workspace values supplied by the
caller. It must return no content or storage reference when ownership is
missing, ambiguous, inconsistent, stale, or unavailable.

This contract is not implementable from the current `Source` model alone:
its identifiers and optional metadata support content provenance, not
authoritative tenancy or access control.

## Future access sequence

1. Establish an actual application invocation path and the first real
   operation requiring protected resource access.
2. Authenticate the request under an owner-approved identity/session
   contract; derive canonical identity and required assurance from the
   trusted adapter.
3. Load current organization/workspace membership and resolve the opaque
   resource identifier through the authoritative tenant-scoped repository.
4. Load the approved policy artifact and verify integrity, freshness,
   version/supersession, and rollback authority; obtain trusted server time.
5. Evaluate the exact action and resource against current facts. No content
   read occurs on deny or unavailable/inconsistent dependencies.
6. Read through the scoped storage reference under a consistent snapshot or
   verified equivalent. Revalidate immediately before disclosure, later
   stream chunks, cache release, or other externally visible effect.
7. Record only required, approved audit metadata in restricted durable
   storage. Exclude document/passage text, secrets, credentials, tokens, and
   raw client paths. If required audit persistence fails, do not perform the
   protected effect.
8. Prefer synchronous operation initially. Any future queue must bind job
   ownership immutably and reload current identity, membership, resource, and
   policy state before reading and releasing content; stop safely on
   revocation.

## Fail-closed behavior and threat acceptance

Future implementation tests must prove:

- missing, malformed, stale, inconsistent, or unavailable identity,
  membership, resource, policy, time, storage, or required audit dependencies
  cause denial without content disclosure;
- cross-tenant and workspace-mismatched lookups do not open source bytes or
  leak content or resource existence;
- caller-controlled paths, object keys, ownership claims, tenant identifiers,
  policy labels, and evaluator decisions cannot override authoritative state;
- modified, stale, superseded, or unauthorized-rollback policy is rejected;
- revocation racing with access prevents subsequent reads, stream chunks,
  cache releases, and effects according to the operation's defined
  consistency boundary;
- any later asynchronous job has immutable owner/resource/action scope and
  reauthorizes at execution and release; and
- required audit metadata is restricted, durable, and free of content/secrets,
  while audit failure blocks the corresponding protected effect.

Synthetic repository tests alone do not establish these assembled-system
properties.

## Owner and infrastructure prerequisites

Before storage implementation can support protected operations, resolve and
record:

- the authorized identity provider/session, MFA, and canonical account-link
  contract;
- the source of truth and authority for organization/workspace membership,
  resource ownership, classification, and lifecycle;
- the complete ratified role/action/sensitivity policy and applicable
  assignment/confidential-read rules;
- policy publication, integrity, version, supersession, signing/key custody
  if used, and rollback authority;
- trusted-time source and failure semantics;
- audit access, event, durability, retention, and backup rules;
- deployment, region, operator access, key control, recovery, and deletion
  precedence as applicable; and
- whole-policy ratifier, date, approved version, amendment process, plus the
  original Decisions 1–36 record or explicit ratified replacement.

Until authoritative evidence exists, preserve `DRAFT — PENDING OWNER
RATIFICATION` and `NOT VERIFIABLE AS NUMBERED`; do not manufacture a resource
owner, tenant, identity, policy value, or infrastructure authority.

## Non-goals and production holds

- No database, migration, persistence adapter, resource catalog, storage
  provider, application route, or runtime authorization integration is
  implemented by this design.
- No identity provider, deployment model, retention period, cryptographic
  scheme, or numeric policy duration is selected.
- No protected production operation is enabled. Confidential reads, exports,
  audit access, writes, deletion/purge/restore, classification changes,
  review submission/finalization, grants, assignments, elevation, and queued
  protected work remain unavailable until their applicable owner decisions
  are ratified and end-to-end technical controls are implemented and
  independently verified.
