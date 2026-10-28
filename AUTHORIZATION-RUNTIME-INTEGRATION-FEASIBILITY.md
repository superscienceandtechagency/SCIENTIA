# Authorization Runtime Integration Feasibility

> **Assessment only.** The authorization policy remains
> `DRAFT — PENDING OWNER RATIFICATION`; Decisions 11–36 remain
> `NOT VERIFIABLE AS NUMBERED`. This document does not authorize or enable
> protected operations.

## Verdict

Runtime integration is **not currently feasible without inventing trusted
infrastructure or creating a misleading placeholder seam**. The repository
contains a pure evaluator and an internal evaluation facade, but no
application entry point, route, protected service, authentication adapter,
authoritative membership/resource repository, policy artifact loader, audit
store, or job queue. FastAPI appears in the dependency manifest, but no
`FastAPI`, `APIRouter`, or route declarations were found in `src/` or `tests/`.
The package currently exposes local research workflow functions that ingest
caller-provided filesystem paths and validate assessment provenance; those
functions do not establish authenticated identity or tenant/action
authorization ([`pyproject.toml`](./pyproject.toml#L5);
[`prepare_research`](./src/scientia/workflow.py#L101);
[`finalize_research`](./src/scientia/workflow.py#L191);
[readiness assessment §2](./AUTHORIZATION-IMPLEMENTATION-READINESS.md#2-evidence-reviewed-and-implementation-status)).

**No new runtime code or test is justified in this milestone.** A test around a
new wrapper would validate an invented interface rather than integration with
an existing operation. Existing boundary unit tests already characterize its
in-process behavior with synthetic providers. No protected production
functionality should be enabled.

## Current request-to-effect path

There is no current authenticated request-to-protected-effect path. The
existing facade's limited path is:

1. `AuthorizationBoundary.evaluate` accepts an untrusted resource selector
   and action.
2. Injected clock and policy-version sources supply a timestamp and opaque
   version label; an injected facts source supplies an `AuthorizationContext`.
3. The facade checks value shapes, requested scope/action, and equality of
   returned/requested version labels, replaces the supplied context time with
   the clock value, and calls the pure evaluator.
4. It returns a decision. It does not read or mutate a resource, revalidate
   before an effect, or durably record an audit event
   ([`AuthorizationBoundary`](./src/scientia/authorization_boundary.py#L159);
   [`evaluate`](./src/scientia/authorization_boundary.py#L186);
   [`authorize` call](./src/scientia/authorization_boundary.py#L279)).

The remaining future path requires all of these, in order:

| Boundary | Required source/control | Current evidence and blocker |
|---|---|---|
| Request authentication | Adapter-verified principal, session, MFA assurance, canonical identity | No adapter or provider contract. Identity-provider, MFA, and account-linking questions remain unresolved ([readiness §§3, 5](./AUTHORIZATION-RATIFICATION-READINESS.md#3-decision-checklist-and-closure-evidence)). |
| Tenant and resource scope | Authoritative membership and resource lookup scoped by server-derived tenant/workspace; no caller ID treated as authority | The facade checks returned facts against the selector but has no facts-source implementation. No repository or storage layer exists. |
| Policy | Ratified policy artifact, verified integrity/version/supersession/rollback, and actual `AuthorizationPolicy` supplied to evaluation | `PolicyVersion` is metadata only; the facade calls `authorize()` without a policy argument, so evaluator defaults apply. There is no policy artifact loader or integrity verification ([`PolicyVersion`](./src/scientia/authorization_boundary.py#L60); [`AuthorizationPolicy`](./src/scientia/authorization.py#L224); [provider assessment §3](./TRUSTED-PROVIDER-AND-POLICY-INTEGRITY-ASSESSMENT.md#3-risk-assessment)). |
| Evaluation time | Trusted server clock with defined health/failure behavior | An injected clock is used and malformed/unavailable time denies; no trusted clock provider is wired. |
| Decision to effect | Revalidation at the operation boundary and a transaction/consistency strategy binding authorization facts to the protected read or mutation | No protected service, transaction, operation guard, or data store exists. A returned allow decision is not a transferable permit. |
| Audit and asynchronous work | Durable restricted audit; immutable initiating principal/tenant/resource/action binding for jobs; worker reauthorization and revocation stop points | No audit store or job queue exists. No job ownership or revocation behavior can be tested end-to-end. |

See the existing [integration roadmap](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#9-dependency-ordered-implementation-roadmap)
and [operation-boundary design](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#6-protected-operation-boundaries)
for target architecture, not implemented controls.

## What can be tested now

The current boundary tests provide useful component evidence:

- provider exceptions, malformed/missing time, policy metadata, and missing
  facts deny ([clock](./tests/test_authorization_boundary.py#L179);
  [policy version source](./tests/test_authorization_boundary.py#L225);
  [facts source](./tests/test_authorization_boundary.py#L246));
- stale version labels and facts outside requested scope deny
  ([version mismatch](./tests/test_authorization_boundary.py#L357);
  [scope mismatch](./tests/test_authorization_boundary.py#L451));
- the facade overwrites facts-source time with injected clock time
  ([server-time test](./tests/test_authorization_boundary.py#L472));
- confidential-read and export cases exercise evaluator-level denials
  ([assignment-only confidential read](./tests/test_authorization_boundary.py#L532);
  [grant-backed export](./tests/test_authorization_boundary.py#L567)).

These tests do **not** demonstrate trusted providers, authenticated identity,
policy artifact integrity, tenant isolation in storage, operation-level
revalidation, audit persistence, or production fail-closed behavior. Existing
provider fakes are contract fixtures only. A repeated facade evaluation
cannot solve a time-of-check/time-of-use race unless the eventual operation
boundary couples fresh authorization facts to the effect.

## Threat cases and fail-closed limits

| Threat or failure | Existing component behavior | Integration limitation / required future proof |
|---|---|---|
| Cross-tenant selector/facts mismatch | Facade rejects facts whose resource/action do not match the selector; evaluator compares membership and resource organization/workspace. | A match does not prove the provider queried storage within tenant scope. Verify cross-tenant denial end-to-end across records, files, derived data, caches, audit, and jobs. |
| Revocation race | Evaluator checks supplied assignment/grant revocation timestamps at one evaluation time. | Facts can become stale immediately afterward. The eventual operation must define a linearization point, revalidate before later disclosure/effects, and prove revocation races cannot commit or release protected data afterward. |
| Job ownership or replay | No queue or job authorization exists. | Bind a job immutably to verified initiating identity, tenant/workspace, resource, action, and command identity; do not serialize reusable allow decisions. Workers must reload current authority, reauthorize, and stop safely on revocation. |
| Stale or tampered policy | Facade rejects a returned label that differs from the requested label. | Equal labels do not authenticate policy contents, freshness, ratification, or rollback authority. A future loader must verify an authoritative policy artifact and reject unavailable, stale, tampered, superseded, or unauthorized rollback state. |
| Trusted-time failure | Clock exceptions and malformed/non-aware times produce denial; facts-source time is replaced. | The clock is injected and has no production implementation. Do not treat tests' fixed clock as trusted time; prove production clock provenance and health behavior before protected use. |
| Facts/provider failure | Provider exceptions, invalid shapes, or missing facts produce denial. | The facade cannot prove its dependencies are trusted. Production composition must be explicit; never replace a failed provider with caller input, cached allow, or success-shaped defaults. |
| Incomplete policy / duration | Facade invokes evaluator with default `AuthorizationPolicy`; missing generic duration bounds cause relevant grant/assignment evaluation to deny. | No approved policy configuration is loaded. Preserve all owner decisions and the global production hold; do not inject convenient numeric values or test fixtures. |

## Decision and smallest next step

The smallest safe **immediate** step is not runtime code: identify and approve
the first concrete protected application operation and its trust-boundary
owners. There is no current route or protected service to integrate, and
owner-authority blockers prevent selecting identity, membership, policy, and
grant/assignment facts ([readiness checklist](./AUTHORIZATION-RATIFICATION-READINESS.md#3-decision-checklist-and-closure-evidence);
[readiness holds](./AUTHORIZATION-RATIFICATION-READINESS.md#4-protected-operation-holds)).

Once an actual operation exists and its applicable policy and authoritative
providers are defined, the smallest testable implementation should be one
non-public, fail-closed service operation with a scoped facts source and
operation-boundary revalidation. Its contract tests must prove: no effect on
missing/unavailable/inconsistent identity, membership, policy, or time;
cross-tenant requests are denied; stale/tampered policy is rejected; revocation
between initial evaluation and the effect prevents the effect; and any queued
work retains immutable ownership and reauthorizes at execution. Keep routes
and protected capabilities disabled until assembled-system tests and
independent verification pass. This is a future entry condition, not approval
to implement or enable the operation now.

## Policy and evidence limitations

The current status remains `DRAFT — PENDING OWNER RATIFICATION`; Decisions
11–36 remain `NOT VERIFIABLE AS NUMBERED`. No identity provider, trusted
membership source, policy signing/key owner, numeric duration, deployment
model, ratifier, or production time source is established by this assessment.
The current evaluator and facade demonstrate only in-process decisions over
supplied/test facts. Neither this document nor passing component tests would
establish policy ratification or production security readiness.
