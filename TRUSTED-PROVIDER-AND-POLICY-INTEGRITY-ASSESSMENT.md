# Trusted Provider and Policy Integrity Assessment

> **Policy status: `DRAFT — PENDING OWNER RATIFICATION`.**
>
> Decisions 11–36 remain **`NOT VERIFIABLE AS NUMBERED`** unless the original
> authoritative record is found and verified. This assessment is a review
> artifact, not a trusted provider implementation, policy approval, production
> security boundary, or certification.

## 1. Executive summary

The current `AuthorizationBoundary` is an internal evaluation seam around
`scientia.authorization.authorize`. It checks the shape of several inputs,
uses an injected clock rather than the context's supplied timestamp, compares
a returned policy-version label with the current label, checks action and
resource scope, validates the evaluator result, and returns a denial for
ordinary exceptions from its injected providers and evaluator
([`AuthorizationBoundary.evaluate`](./src/scientia/authorization_boundary.py#L186)).

Those checks do not authenticate the caller, establish where injected
dependencies came from, load or verify a policy artifact, or ensure that
authorization facts are current and transactionally bound to a protected
operation. `PolicyVersion` is metadata only; equality of labels is not
cryptographic integrity, ratification, freshness, or rollback protection.
The facade does not pass a loaded policy into the evaluator; it calls
`authorize()` with the evaluator's default `AuthorizationPolicy`
([`AuthorizationPolicy`](./src/scientia/authorization.py#L224),
[`authorize`](./src/scientia/authorization.py#L254),
[`evaluate`](./src/scientia/authorization_boundary.py#L266)).

**Readiness conclusion:** do not use this facade to enable application-facing
protected operations. It currently has no route/service callers, authentication
adapter, authoritative repositories, policy loader, transactional operation
boundary, or durable audit integration. The dependency objects are trusted
because application construction supplies them; the module cannot prove that
trust. Their identities, results, and lifetime are not bound by the current
interface to an authenticated request.

## 2. Evidence categories

### Actually enforced by the current code

- `ResourceSelector` rejects blank/non-string identifiers, and
  `AuthorizationBoundary.evaluate` requires that exact selector type and an
  `Action` value ([`ResourceSelector`](./src/scientia/authorization_boundary.py#L43),
  [`evaluate`](./src/scientia/authorization_boundary.py#L186)).
- The boundary obtains evaluation time from its injected clock, denies on a
  missing/malformed/raising clock result, and replaces the facts context's
  evaluation time before evaluation ([`evaluate`](./src/scientia/authorization_boundary.py#L195),
  [`_is_aware_datetime`](./src/scientia/authorization_boundary.py#L371)).
- It denies missing or malformed policy-version metadata and rejects
  `LoadedAuthorizationFacts` whose label differs from the label returned by
  its injected version source ([`PolicyVersion`](./src/scientia/authorization_boundary.py#L60),
  [`LoadedAuthorizationFacts`](./src/scientia/authorization_boundary.py#L120),
  [`evaluate`](./src/scientia/authorization_boundary.py#L208)).
- It denies absent/malformed facts, mismatched action or resource identifiers,
  ordinary exceptions from providers/evaluator, and malformed or contradictory
  evaluator decisions ([`evaluate`](./src/scientia/authorization_boundary.py#L214),
  [`_is_valid_context_shape`](./src/scientia/authorization_boundary.py#L336),
  [`_is_valid_decision`](./src/scientia/authorization_boundary.py#L308)).
- The existing pure evaluator preserves its current fail-closed grant,
  assignment, confidentiality, and unsupported-action behavior; this
  assessment does not change it.

These properties hold when execution reaches the stated Python code and the
runtime objects behave according to the checked contracts. They are not
authentication, provider attestation, policy verification, or operation
enforcement.

### Assumptions about injected dependencies

- The constructor accepts any object with callable `load()`, `now()`, and
  `current_version()` attributes; it does not authenticate, authorize,
  attest, or otherwise verify those objects
  ([`AuthorizationBoundary.__init__`](./src/scientia/authorization_boundary.py#L169),
  [`_has_callable_method`](./src/scientia/authorization_boundary.py#L318)).
- The facts provider is expected by documentation to be an internal trusted
  dependency bound to the authenticated request, but that binding is not
  established or enforceable by this module
  ([`AuthorizationFactsSource`](./src/scientia/authorization_boundary.py#L84)).
- `LoadedAuthorizationFacts` and its `PolicyVersion` are Python values
  returned by that provider. A matching label can detect accidental mismatch
  only when providers report it honestly; it cannot prove the facts were
  loaded from the named policy version
  ([`LoadedAuthorizationFacts`](./src/scientia/authorization_boundary.py#L107)).
- The selector is caller-controlled input. The facade verifies that the
  returned resource IDs match it, but relies on the facts provider and future
  repository to establish that the resource was authoritatively loaded and
  belongs to the authenticated principal's membership scope.

### Protections not implemented

No production authentication or session validation; no authenticated-principal
provenance; no authoritative membership/resource/grant/assignment repository;
no policy artifact loader, signature or integrity verification, ratification
record validation, supersession handling, or rollback authority; no explicit
policy passed to the evaluator; no transaction or operation-boundary
revalidation; and no application route, persistence, queue, or audit service
were found in the inspected project source
([implementation readiness](./AUTHORIZATION-IMPLEMENTATION-READINESS.md#2-evidence-reviewed-and-implementation-status),
[trusted-boundary design](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#2-current-architecture-and-evaluator-limits)).

## 3. Risk assessment

| Risk | Evidence and current mitigation | Impact | Missing control | Recommended prerequisite |
|---|---|---|---|---|
| **Provider construction and dependency wiring** | `AuthorizationBoundary` takes three injected objects and checks callable attributes. This is a structural check, not proof that the objects are trusted, correctly scoped, immutable, or safe for the request ([constructor](./src/scientia/authorization_boundary.py#L169)). Provider exceptions ordinarily produce failure categories and denial ([`BoundaryFailure`](./src/scientia/authorization_boundary.py#L103)). | A future route could wire a request-controlled, stale, misconfigured, or over-privileged provider. A deliberately malicious in-process provider can return an allow-eligible principal and membership. | Application composition root, dependency lifetime/scope rules, request-bound provider contract, startup validation, and security review of concrete providers. Python `Protocol` and callable checks do not enforce trust. | Before routes: define an application composition root that constructs providers from trusted configuration, binds per-request authentication context explicitly, rejects missing/ambiguous providers at startup, and prevents transport payloads from selecting or replacing dependencies. |
| **Authenticated identity provenance** | The facade receives no separately verified principal. Its provider returns an `AuthorizationContext` containing caller-asserted `Principal` and `Membership`; the facade checks shape and scope, not the provenance or authenticity of those records ([`AuthorizationFactsSource`](./src/scientia/authorization_boundary.py#L84), [`_is_valid_context_shape`](./src/scientia/authorization_boundary.py#L336)). The kernel documents that it does not authenticate ([`Principal`](./src/scientia/authorization.py#L73)). | A miswired or caller-influenced facts source can assert another subject, role, tenant, or MFA state. A public-read-eligible researcher lead can produce an evaluator allow from such synthetic facts. This is not currently exposed by a route, but the facade result itself is not proof of identity. | Authentication adapter, verified session/token semantics, trusted principal construction, authoritative membership lookup, and binding between authenticated request and facts lookup. | Before any protected operation: select and implement an approved authentication boundary and ensure every facts load derives subject and session from its verified result; ignore caller-supplied identity/role/MFA claims. |
| **Policy-version label mistaken for integrity** | `PolicyVersion` validates only a nonblank string. Equality is checked between two provider-returned labels; neither signature, digest, approval metadata, nor trusted provenance is checked ([`PolicyVersion`](./src/scientia/authorization_boundary.py#L60), [`evaluate`](./src/scientia/authorization_boundary.py#L208)). | A tampered, unratified, superseded, or rolled-back policy can carry a matching label. Consumers may incorrectly interpret result metadata as a verified policy decision. | Authoritative policy artifact, integrity and provenance verification, ratification metadata validation, version/supersession model, and authorized rollback process. | Before policy-based allows: define the owner-authorized publication and rollback process; then load only a provenance-verified ratified artifact and bind the actual verified artifact/version to the decision. Do not treat a label or hash alone as proof of ratification. |
| **Policy is not loaded or evaluated** | The boundary asks a version source for a label but no policy source returns evaluator rules. It invokes `authorize()` without a policy argument, so `AuthorizationPolicy()` defaults apply ([`evaluate`](./src/scientia/authorization_boundary.py#L266), [`authorize`](./src/scientia/authorization.py#L254), [`AuthorizationPolicy`](./src/scientia/authorization.py#L224)). | Evaluation is not demonstrated to correspond to the metadata version included in the result. Assignment/grant paths deny for missing generic maxima, but any evaluator path that does not require those values can still allow based on the supplied facts. | Typed, validated policy loading from an approved source, binding between loaded policy and its version metadata, complete role/action rules, and explicit evaluator invocation with that policy. | Before policy-sensitive enablement: ratify the relevant rules and values, implement authenticated policy loading, validate the entire supported policy shape, and pass the same verified policy object/version through facts loading and evaluation. |
| **Facts/policy consistency and stale caches** | The version label is requested from one provider and then passed to another; the returned envelope echoes a version label. This catches only a mismatching returned label, not a provider that labels stale facts with the requested version. One timestamp is captured before metadata and facts loading ([`evaluate`](./src/scientia/authorization_boundary.py#L195)). | Concurrent policy or membership changes, stale caches, inconsistent repositories, or a slow lookup can yield facts that are no longer current when the decision is consumed. | Shared snapshot/transaction, immutable versioned policy/facts read, source-of-truth version check, freshness guarantees, and revalidation before side effects. | Before operation integration: define consistency semantics for policy plus membership/resource/grant/assignment facts; ensure the returned versions derive from storage state and recheck state at the operation's commit/release boundary. |
| **Provider/evaluator failures and invalid results** | The boundary catches ordinary `Exception` from clock, policy metadata, facts, and evaluator calls; validates the resulting decision's shape and reason/allow consistency ([`evaluate`](./src/scientia/authorization_boundary.py#L195), [`_is_valid_decision`](./src/scientia/authorization_boundary.py#L308)). Tests exercise provider/evaluator exceptions, invalid results, and malformed facts ([boundary tests](./tests/test_authorization_boundary.py#L179), [facts tests](./tests/test_authorization_boundary.py#L246), [decision tests](./tests/test_authorization_boundary.py#L301)). | Denial avoids accidental allow on these ordinary failure paths, but there is no operational alerting or dependency health policy. Process-control exceptions outside `Exception` are intentionally not normalized. A future caller must not translate failure metadata into success. | Observability that does not expose sensitive data, service-level mapping of diagnostic failures to non-disclosing errors, and tests proving no wrapper converts a denial/failure into success. | Before routes: define failure handling and monitoring in the service layer; preserve a deny on every dependency/evaluator failure and never use success-shaped fallback. |
| **Caller-controlled selector and tenant/resource scope** | Selector is validated for type/nonblank identifiers and returned resource identifiers must match it ([`ResourceSelector`](./src/scientia/authorization_boundary.py#L43), [`_resource_matches_selector`](./src/scientia/authorization_boundary.py#L325)). The evaluator checks equality between supplied membership and resource organization/workspace ([`authorize`](./src/scientia/authorization.py#L254)). | A selector is not authorization. A malicious request may choose any IDs; safety depends on provider lookup being scoped to authenticated membership, which the facade does not establish. IDs can also refer to a resource whose backing object or derived content was fetched through an unscoped path. | Authenticated membership-bound query and tenant-scoped resource/object/index/cache repositories; no unscoped lookup before authorization. | Before reads or writes: obtain scope from verified principal and authoritative membership, use that scope in the repository query, verify returned ownership, and preserve it for blobs, passages, indexes, caches, and derived data. |
| **No operation-level revalidation / concurrency control** | `evaluate()` returns a decision and metadata; it does not execute or wrap a protected operation. No transaction, authorization-state version, queue, or commit/release callback is present ([`AuthorizationBoundary.evaluate`](./src/scientia/authorization_boundary.py#L186), [design §7](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#7-transactional-consistency-replay-revocation-and-jobs)). | State may be revoked or changed after the decision, before data disclosure or mutation. The earlier evaluation time can predate completion of slow provider calls. | Atomic authorization-and-operation snapshot where applicable, revalidation immediately before sensitive effects, defined revocation ordering, and race/failure tests. | Before enabling operations: integrate the decision within a service transaction or revalidate current state at the exact protected side effect; test concurrent grant/membership/resource/policy changes and streaming/job stop behavior. |
| **Tests mistaken for security evidence** | The boundary tests use synthetic `FixedClock`, version, facts providers, and caller-created principals. They verify local code paths, not identity provider, storage, runtime wiring, operations, or deployment ([test helpers](./tests/test_authorization_boundary.py#L26), [policy mismatch test](./tests/test_authorization_boundary.py#L357)). | Passing unit tests may create unwarranted confidence that a production provider or policy artifact is trustworthy. | Integration tests with real configured provider adapters and repositories, deployment configuration review, concurrency/failure testing, and independent security review. | Treat unit tests as component evidence only. Before production, add integration and deployment-specific tests and independent review against the actual assembled runtime. |

## 4. Policy and owner-authority blockers

The policy draft is still non-authoritative. Preserve its exact status,
**`DRAFT — PENDING OWNER RATIFICATION`**, and do not infer decisions from test
fixtures or version labels. At minimum, these decisions remain open or
unratified:

1. Whole-policy ratification metadata: ratifier, date, approved version, and
   amendments.
2. U-2: fixed confidential-content grant maximum.
3. U-3: separate fixed administrator-elevation maximum.
4. U-4: assignment default and maximum.
5. U-5: who designates security personnel and the scope of their authority.
6. U-6: whether issuer and approver need separate operational duties beyond
   distinct identities.
7. U-7: canonical identity/account-linking evidence and duplicate-account
   handling.
8. U-8: locate and verify the original numbered policy record. Decisions
   11–36 remain **`NOT VERIFIABLE AS NUMBERED`** unless that source is found.
9. Complete role/action matrix and assignment requirements for each action.
10. MFA assurance/session details; audit authority, scope, retention and
    jurisdiction; policy publication/integrity/rollback authority; and
    identity-provider/transport details.

Recorded A1, B2, U-1, and duration-shape selections remain pending formal
ratification. The ratification package is for review, not an authoritative
policy source
([draft §6](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register),
[ratification package status](./AUTHORIZATION-RATIFICATION-PACKAGE.md#status)).
Do not reconstruct or renumber Decisions 11–36.

## 5. Staged roadmap and entry criteria

No stage below authorizes protected operations by itself. A capability remains
disabled until all applicable stages and its owner-authority decisions are
complete.

| Stage | Work | Entry criteria | Exit evidence / gate |
|---|---|---|---|
| **0 — Preserve fail-closed state** | Keep this facade internal and do not expose protected routes or operations. Preserve evaluator denies for unresolved grants/assignments and unsupported actions. | Current state; no policy approval is presumed. | No protected application callers. Policy remains pending; Decisions 11–36 retain the stated historical status. |
| **1 — Ratify applicable policy and authority** | Produce an owner-ratified versioned policy; resolve only the policy and authority decisions required by each capability. Locate the original numbered record if available. | Owner review and authoritative evidence. | Ratifier/date/version/amendments recorded; role/action rules and applicable duration/authority decisions explicit; no inferred values. |
| **2 — Define provider and identity composition** | Specify verified identity/session contract, provider construction, request binding, authoritative membership and resource resolution, and provider lifecycle/failure monitoring. | Approved identity-provider/transport decisions and MFA semantics; U-7 before identity-independence claims. | Forged request facts cannot establish identity; provider wiring is controlled; identity, membership, and ownership provenance are tested in integration. |
| **3 — Establish policy integrity and binding** | Implement authoritative policy publication/loading, verify approval provenance and integrity, handle supersession and authorized rollback, and bind the loaded rules/version to facts and evaluation. | Ratified policy plus owner-authorized publication and rollback process. | Tampered, unratified, stale, superseded, or unauthorized rollback policy denies; evaluator uses the exact policy object whose verified metadata accompanies the result. |
| **4 — Establish consistency and operation boundary** | Integrate scoped authorization with reads/mutations; define transaction or equivalent revalidation semantics, current-time/facts consistency, revocation ordering, and safe stream/job boundaries. | Stages 1–3 complete and chosen persistence/transaction semantics. | Cross-tenant, stale-state, policy-change, and TOCTOU tests deny or safely stop before protected effects; no caller can bypass the service. |
| **5 — Audit and capability-specific lifecycle** | Implement durable, content-free audit and only the grant/assignment/elevation/review/deletion lifecycle explicitly authorized by ratified policy. | Audit governance and capability-specific authority/durations resolved; trusted identity, policy, and operation boundary exist. | Required audit failure prevents success; lifecycle authority, scope, expiry, revocation, and operation revalidation pass tests. |
| **6 — Independent verification before enablement** | Test the assembled runtime, concurrency/failure behavior, deployment configuration, and every exposed operation; obtain independent security review. | Applicable stages complete; all dependencies are configured in the target environment. | Document observed evidence and residual risks. Enable only individually accepted capabilities; tests alone are not certification. |

**Protected-operation gate:** do not enable even public-resource reads or
ordinary review submissions until verified authentication, authoritative
policy handling, tenant/resource-scoped operation enforcement, and the
required owner ratifications for those capabilities are in place. Grant
issuance/reliance, assignment lifecycle, elevation, exports, deletion,
audit queries, classification changes, and high-stakes review each require
their own unresolved authority and lifecycle decisions to be closed.

## 6. Verification and limitations

This assessment is based on the current boundary source and tests, the pure
evaluator, and the policy, ratification, enforcement-gap, trusted-boundary,
and readiness documents cited above. Existing boundary tests were inspected;
they are component tests over synthetic in-process objects and do not prove
production identity or policy integrity.

This document does not implement or claim a trusted provider, authentication,
policy signature, rollback protection, authoritative policy loader, operation
transaction, or production control. The assessment does not ratify policy or
recover missing historical Decisions 11–36. Keep the global fail-closed
requirement from the trusted-boundary design in force until actual
operation-level enforcement and applicable owner approvals are verified.
