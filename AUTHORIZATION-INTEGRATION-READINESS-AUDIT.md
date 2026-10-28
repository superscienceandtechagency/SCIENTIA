# SCIENTIA Authorization Integration Readiness Audit

> **Policy status: `DRAFT — PENDING OWNER RATIFICATION`.**
>
> Decisions 11–36 remain **`NOT VERIFIABLE AS NUMBERED`** unless the original
> authoritative record is located and verified. This is a readiness audit,
> not security certification, policy approval, or evidence of production
> authorization.

## 1. Executive verdict

**SCIENTIA is ready for documentation and design work, ready with blockers
for isolated non-exposing engineering foundations, and not ready for
protected production operations.**

The repository has a pure authorization evaluator, an internal evaluation
facade, synthetic unit tests, and local evidence/research workflows. Current
source enforces several conservative evaluator-level denials and scope/time
checks. It does not establish authenticated identity, trusted provider
provenance, approved policy integrity, durable tenant-scoped state, or
authorization at a protected service operation. No protected route or
operation consumes the facade.

This verdict assesses readiness to start work, not authorization to enable
capabilities. No operation that can disclose or mutate protected data should
be enabled based on evaluator tests, local workflow validation, or design
documents.

| Readiness category | Verdict | Basis |
|---|---|---|
| Documentation and architecture design | **READY** | Current evidence and unresolved decisions are sufficient to maintain plans and reconcile documented behavior without selecting policy. |
| Isolated, non-exposing engineering foundations | **READY WITH BLOCKERS** | Narrow, non-authorizing contract/test work can be undertaken, but must not imply trusted identity, verified policy, or operational authorization. No real providers or application integration currently exist. |
| Protected production operations | **NOT READY** | Authentication, owner-ratified policy and authority, trusted loading, scoped repositories, service-level enforcement, persistence consistency, and applicable audit/review controls are absent. |

## 2. Evidence inventory

“Implemented” means code or tests exist for the stated limited purpose; it
does not imply production integration. Design and policy documents are not
implementation evidence.

| Evidence | Classification | What it establishes | What it does not establish |
|---|---|---|---|
| [`src/scientia/authorization.py`](./src/scientia/authorization.py#L254) | **IMPLEMENTED — pure evaluator** | Evaluates caller-supplied immutable facts. Current source denies delete/elevation, denies grant-backed write/export, and requires the base role/assignment path plus a read grant for confidential reads. Grant/assignment lifecycles requiring durations deny when generic maxima are unconfigured. | Authentication, trusted provenance, ratified complete role/action policy, authoritative data, or service enforcement. |
| [`src/scientia/authorization_boundary.py`](./src/scientia/authorization_boundary.py#L159) | **IMPLEMENTED — internal evaluation seam** | Accepts untrusted selectors, gets time/version labels from injected dependencies, validates returned fact shapes and scope/action, overwrites evaluation time, catches ordinary provider/evaluator failures, and validates decisions. | Provider trust, identity verification, policy loading/integrity, rollback protection, freshness transaction, or execution of a protected operation. |
| [`tests/test_authorization.py`](./tests/test_authorization.py#L265) | **IMPLEMENTED — synthetic evaluator tests** | Tests layered confidential-read behavior, grant/assignment-only denial, grant-backed write/export denial, and other evaluator inputs. | Production identity, repositories, deployment, race behavior, or policy approval. |
| [`tests/test_authorization_boundary.py`](./tests/test_authorization_boundary.py#L301) | **IMPLEMENTED — synthetic seam tests** | Exercises provider/evaluator failures, malformed facts and decisions, selector/action mismatch, and current evaluator integration. | Trust of production provider wiring or service operation boundaries. |
| [`src/scientia/workflow.py`](./src/scientia/workflow.py#L101) | **IMPLEMENTED — local workflow** | Ingests local PDF paths, retrieves passages, validates assessment provenance, and synthesizes supplied assessments. | Authenticated user, tenant authorization, protected API, or service-level permission checks. |
| [`src/scientia/verification.py`](./src/scientia/verification.py#L33) | **IMPLEMENTED — domain records** | Represents assessment/review states and reviewer labels. | Authenticated reviewer identity, independent-human verification, blind review, or adjudication. |
| [`AUTHORIZATION-POLICY-DRAFT.md`](./AUTHORIZATION-POLICY-DRAFT.md#5-policy-requirements-vs-current-implementation-enforcement) | **DRAFT POLICY / UNRESOLVED** | Records selected options, current evaluator-only A1/B2/U-1 behavior, historical baseline, unresolved decisions, and fail-closed requirements. | Ratification or runtime control. |
| [`AUTHORIZATION-RATIFICATION-PACKAGE.md`](./AUTHORIZATION-RATIFICATION-PACKAGE.md#owner-decision-workflow) | **REVIEW PACKAGE / UNRESOLVED** | Summarizes recorded selections and owner-input requirements; its U-1 evidence now matches current evaluator behavior and retains the ratification question. | Ratification or runtime control. |
| [`AUTHORIZATION-ENFORCEMENT-GAP-ASSESSMENT.md`](./AUTHORIZATION-ENFORCEMENT-GAP-ASSESSMENT.md#milestone-13-evaluator-update) | **HISTORICAL BASELINE + CURRENT UPDATE** | Original pre-Milestone-13 gaps are explicitly labeled; the later update records current evaluator changes and limitations. | Application boundary implementation, owner approval, or production security. |
| [`TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md`](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#2-current-architecture-and-evaluator-limits) | **DESIGN — NOT IMPLEMENTED** | Specifies a future boundary and threat controls. | Existence of those controls. |
| [`AUTHORIZATION-IMPLEMENTATION-READINESS.md`](./AUTHORIZATION-IMPLEMENTATION-READINESS.md#3-requirement-traceability) | **READINESS DESIGN / EVIDENCE SUMMARY** | Tracks evaluator-level safeguards and integration blockers. | Authentication, repositories, service enforcement, or ratification. |
| [`TRUSTED-PROVIDER-AND-POLICY-INTEGRITY-ASSESSMENT.md`](./TRUSTED-PROVIDER-AND-POLICY-INTEGRITY-ASSESSMENT.md#2-evidence-categories) | **RISK ASSESSMENT** | Separates facade checks, provider assumptions, and missing policy integrity controls. | A trusted provider or policy-integrity implementation. |
| [`AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md`](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#9-dependency-ordered-implementation-roadmap) | **INTEGRATION PLAN — NOT IMPLEMENTED** | Provides target request flow, component ownership, stages, gates, and verification requirements. | Completion of any target stage. |

## 3. Cross-document consistency matrix

Current source is the evidence of present implementation. Policy documents
remain the evidence of policy status; implementation behavior does not ratify
policy.

| Comparison | Current source/evidence | Document statement | Audit finding |
|---|---|---|---|
| Evaluator vs policy draft §5 | [`authorize`](./src/scientia/authorization.py#L300) denies delete/elevation; confidential reads require base role/assignment then a grant; write/export grant paths deny ([lines 303](./src/scientia/authorization.py#L303), [341](./src/scientia/authorization.py#L341)). Tests cover the corresponding denials ([confidential assignment](./tests/test_authorization.py#L308), [grant-backed action](./tests/test_authorization.py#L331)). | Draft §5 now describes these evaluator-only behaviors and explicitly distinguishes them from ratified policy and production enforcement ([current implementation notes](./AUTHORIZATION-POLICY-DRAFT.md#5-policy-requirements-vs-current-implementation-enforcement)). | **Reconciled.** A1/B2/U-1 remain pending ratification; evaluator checks do not create service enforcement. |
| Evaluator vs ratification package U-1 row | Current evaluator denies grant-only confidential reading and requires assignment/role base eligibility ([`authorize`](./src/scientia/authorization.py#L303)); tests assert grant-only denial ([test](./tests/test_authorization.py#L265)). | The U-1 evidence row now cites current evaluator and synthetic tests, while retaining the original owner-ratification question ([row](./AUTHORIZATION-RATIFICATION-PACKAGE.md#owner-decision-workflow)). | **Reconciled.** U-1 remains owner-selected and pending formal ratification; the row states that evaluator behavior is not an application control. |
| Evaluator vs enforcement-gap assessment | The gap assessment labels the early findings a **pre-Milestone-13 baseline**, and a later section records current evaluator changes ([baseline header](./AUTHORIZATION-ENFORCEMENT-GAP-ASSESSMENT.md#executive-summary), [update](./AUTHORIZATION-ENFORCEMENT-GAP-ASSESSMENT.md#milestone-13-evaluator-update)). | The baseline table now explicitly names its behavior, risk, and remediation columns as historical; the update states current evaluator behavior. | **Historical evidence intentionally preserved and clarified.** Do not read the baseline table as current behavior; its original findings and recommendations are retained. |
| Evaluator vs readiness document | Current evaluator and tests implement the described limited A1/B2/U-1 ceilings. | Readiness document says these are evaluator-only safeguards, with no operation boundary or complete role/action policy ([readiness §1](./AUTHORIZATION-IMPLEMENTATION-READINESS.md#1-executive-summary)). | **Consistent.** Its test references are evidence of synthetic component behavior, not production security. |
| Boundary facade vs integration plan | Facade injects facts, clock, and version-label dependencies, replaces supplied time, scope-checks context, then calls `authorize()` without a policy argument ([`evaluate`](./src/scientia/authorization_boundary.py#L186)). | Integration plan says the facade is not authentication, version label is not integrity, and no service consumes it ([plan §1](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#1-current-state)). | **Consistent.** No trusted provider, policy loader, or operation wrapper should be inferred. |
| Boundary assessment vs facade | Facade validates type/shape, action/resource selector, time, version-label equality, and evaluator result; injected dependencies remain assumed trusted. | Provider assessment distinguishes these checks from provider trust, identity provenance, verified policy, and transaction consistency ([assessment §2](./TRUSTED-PROVIDER-AND-POLICY-INTEGRITY-ASSESSMENT.md#2-evidence-categories)). | **Consistent.** Matching version labels are not integrity or rollback controls. |
| Design vs current architecture | No routes, authentication adapter, persistence, queue, audit store, or protected service was found. | Trusted-boundary design is explicitly “DESIGN FOR REVIEW — NOT IMPLEMENTED” and defines desired future controls ([design status](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#2-current-architecture-and-evaluator-limits)). | **Consistent when read as design.** Do not report design controls as implemented. |
| Local workflow vs authorization requirements | Workflow accepts local files/assessments and validates provenance; review model contains `reviewer_label` and `HUMAN_REVIEWED` state ([workflow](./src/scientia/workflow.py#L101), [`ClaimAssessment`](./src/scientia/verification.py#L129)). | Design and integration plan correctly distinguish this from tenant protection and independent review ([integration plan §1](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#1-current-state)). | **Consistent.** No workflow defect is established by these local-model behaviors; they are simply not an application security workflow. |
| Integration plan vs owner decisions | Plan says no provider, retention, jurisdiction, numeric duration, or security authority is selected and keeps protected operations blocked ([plan §11](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#11-explicit-non-goals-and-unresolved-decisions)). | Draft and ratification package preserve U-1, U-2–U-8, and ratification as open or pending. | **Consistent.** Do not turn the target architecture into approval to implement policy-sensitive capabilities. |

### Genuine implementation gaps versus documentation drift

- **Genuine integration gaps:** no authentication/session adapter, verified
  principal, authoritative membership/resource repositories, policy artifact
  loader/integrity/rollback controls, transactional or equivalent operation
  enforcement, durable audit store, queue/job authorization, or independent
  high-stakes review service exists in the inspected source.
- **Not a current evaluator defect:** A1/B2/U-1 conservative evaluator
  behavior is present in current source and covered by synthetic tests. These
  checks are incomplete as a production boundary, but stale prose is not
  evidence that the code still has the earlier allow paths.
- **Documentation drift:** policy draft §5 and the ratification package U-1
  evidence row retain older current-behavior claims. The gap assessment's
  original findings are historical, though its explicit baseline/update
  framing limits the contradiction.
- **Duplicated requirements:** identity provenance, policy integrity,
  tenant/resource scoping, operation revalidation, audit, and owner blockers
  repeat across the readiness, design, provider assessment, and integration
  plan. The repetition is largely consistent but should be maintained from
  source-backed facts to avoid divergent stale copies.
- **Reconciliation note:** Milestone 22 corrected
  `AUTHORIZATION-POLICY-DRAFT.md` §5 and its Section 6 confidential-read hold,
  and the U-1 evidence row in `AUTHORIZATION-RATIFICATION-PACKAGE.md`. These
  now describe current evaluator behavior as in-process only, link to
  relevant source/tests, and distinguish it from application enforcement.
  `AUTHORIZATION-ENFORCEMENT-GAP-ASSESSMENT.md` now labels its gap table
  columns as pre-Milestone-13 baseline behavior and updates its recommendation
  to reflect that the evaluator-only gaps were addressed. The baseline
  findings remain preserved as historical evidence; the later update remains
  the record of current evaluator behavior. No policy selection, unresolved
  authority decision, or historical policy record was changed.
- **Missing connection:** the facade's `PolicyVersion` is not linked to an
  actual loaded `AuthorizationPolicy`; the evaluator receives its default
  policy. No durable decision version, authenticated subject, or operation
  transaction binds a facade result to an effect.

## 4. Stage readiness matrix

Statuses assess whether the project can begin the named future implementation
stage on current evidence. `READY` does not mean the stage is complete or
that it enables protected operations.

| Future stage | Status | Why / minimum entry condition |
|---|---|---|
| Trusted authentication adapter | **NOT READY** | No adapter exists and no identity-provider, session, token-purpose, or MFA assurance contract has been selected. First establish owner-approved identity/session requirements; do not invent provider choice. |
| Verified identity and tenant membership resolution | **NOT READY** | `Principal`, roles, membership, and `mfa_verified` are caller-supplied values to the evaluator; no authenticated principal construction or authoritative membership source exists. Requires identity contract, canonical subject rules, and scoped membership/resource repositories. |
| Authoritative policy loading and integrity/rollback protection | **NOT READY** | Facade obtains only an opaque version label and calls evaluator with default `AuthorizationPolicy()`. No ratified artifact, loader, provenance/integrity check, supersession rule, or rollback authority exists. Requires applicable ratification and owner-authorized publication/rollback process. |
| Trusted provider wiring | **READY WITH BLOCKERS** | The facade supplies a seam and structural callable checks, so non-exposing composition-contract/test work is possible. There is no application composition root or concrete trusted provider; actual wiring is blocked on authenticated request binding, authoritative sources, and policy loading. |
| Service-level authorization enforcement | **NOT READY** | No route/service executes the decision or binds it to reads, writes, commits, or audit. Requires trusted identity, policy, scoped facts, and transaction/revalidation semantics before protected effects. |
| Tenant-isolated persistence and file access | **NOT READY** | No application persistence/object store exists; local PDF paths and evidence-provenance checks are not tenant authorization. Requires scoped repository and file-access design with integration tests across original, parsed, and derived content. |
| Asynchronous job authorization and revocation | **NOT READY** | No queue or job service exists. Requires authenticated job provenance, execution-time and side-effect revalidation, safe cancel/stop behavior, and revocation-race tests. |
| Audit event storage and restricted access | **NOT READY** | No durable audit writer/store or separately authorized audit query path exists. Retention, access authority, integrity, and jurisdiction are unresolved. |
| High-stakes independent review/adjudication | **NOT READY** | Local `HUMAN_REVIEWED` and reviewer labels are not authenticated identities or two-person approval. U-7 and historical provenance/ratification remain unresolved; no workflow exists. |
| Exports and deletion workflows | **NOT READY** | No service workflows exist; current evaluator denies grant-backed export and deletion. Requires ratified role/action and lifecycle rules, trusted operation boundary, audit, and per-operation race tests. |

No stage should skip its prerequisite gates. An upstream identity, policy,
membership, resource, clock, or provider failure or inconsistency must deny
before downstream evaluation or effects. A successful evaluator decision
alone is not readiness to access data.

## 5. Owner-authority blockers

The following are policy or authority decisions, not choices this audit may
resolve:

1. **Whole-policy ratification:** ratifier, date, approved version, amendments,
   and formal ratification of applicable recorded selections.
2. **Recorded selections:** A1, B2, U-1 confidentiality-only grant, duration
   shapes, audited renewals, and F2 remain pending formal ratification.
3. **U-2:** fixed confidential-content grant maximum; no numeric value is
   approved.
4. **U-3:** separate fixed administrator-elevation maximum; no numeric value
   is approved.
5. **U-4:** assignment default and maximum; neither numeric value is approved.
6. **U-5:** who designates security personnel and the scope of their grant,
   approval, revocation, and audit authority.
7. **U-6:** whether issuer and approver require separate operational duties
   beyond distinct identities.
8. **U-7:** canonical identity/account-linking evidence, duplicate-account
   handling, and sufficient proof for distinct-person review.
9. **U-8:** original authoritative Decisions 1–36 record, version, approval
   provenance, and supersession history. Decisions 11–36 remain
   **`NOT VERIFIABLE AS NUMBERED`** unless the source is actually found and
   verified; do not reconstruct it.
10. Complete role/action matrix and action-specific assignment requirements.
11. High-stakes review rules recorded from prior conversation, pending
    confirmation in an authoritative ratified record.
12. Authentication/MFA assurance and identity-provider choice.
13. Policy publication, integrity, supersession, rollback authority and
    mechanism.
14. Audit access authority, retention, legal hold, integrity requirements,
    and deployment jurisdiction.

Until applicable decisions are authoritative and enforced, keep grants,
assignments, elevation, confidential-content access, high-stakes finalization,
exports, deletion, audit reads, and queued protected work disabled or denied.
Documentation of a hold does not itself disable a runtime path.

## 6. Security-critical dependency graph

```text
Owner ratification of applicable policy + authority
        ├──> Identity/session/MFA contract ──> Authentication adapter
        │                                      └──> Verified request identity
        │                                                │
        ├──> Policy publication/rollback authority      │
        │       └──> Authoritative policy loader         │
        │                └──> Verified policy snapshot   │
        │                                                │
        └──> Scope/action requirements                  │
                                                         v
                         Trusted composition + authoritative membership,
                         resource, grant/assignment, clock and audit sources
                                         │
                   Verified identity + policy + current scoped facts
                                         v
                            Configured authorization evaluation
                                         │
                 Transaction/revalidation + tenant-scoped operation service
                     ├──> Reads / writes / review commits
                     ├──> Exports / deletion
                     └──> Audited grant/assignment/elevation lifecycle
                                  │
                     Queue execution + revocation stop rules
                                  │
                    Independent verification / controlled enablement
```

### Blocking and fail-closed edges

- Without applicable ratification, do not load draft policy as authority or
  enable policy-sensitive decisions. Keep Decisions 11–36 unverifiable
  unless the source is recovered.
- Without verified authentication and membership, caller IDs, roles,
  tenant/workspace selectors, or MFA booleans cannot authorize a principal.
  Deny before resource content is fetched.
- Without authoritative resource ownership, deny; matching selector strings
  only proves the returned context echoed the selector.
- Without a valid server time, current membership/facts, or consistent
  provider results, deny. Never fall back to caller timestamps, cached allows,
  or success-shaped defaults.
- Without a verified policy artifact and authorized version/rollback state,
  deny policy-dependent access. Version-label equality alone is insufficient.
- Without operation-level revalidation/transaction semantics, no protected
  read release, durable write/review commit, export, deletion, or queued side
  effect may occur.
- If required audit persistence fails, do not report a policy-required audited
  operation as successful.
- A missing queue stop/revalidation contract blocks queued protected work;
  missing canonical identity rules block claims of independent review.

## 7. Minimal next implementation milestone

### Recommendation: Milestone 22 — Reconcile authorization implementation evidence

The smallest evidence-supported next step is a bounded **documentation-only
consistency correction**, not authentication or application integration. Two
existing documents describe evaluator behavior superseded by current source:
the implementation claims in policy draft §5 and the U-1 evidence in the
ratification package. Correcting these statements would reduce the risk that
future implementers follow obsolete behavior while preserving the policy's
unratified status.

**Scope**

- Update only the implementation-evidence statements in
  `AUTHORIZATION-POLICY-DRAFT.md` §4–§5 and the U-1 row in
  `AUTHORIZATION-RATIFICATION-PACKAGE.md`.
- Cite current evaluator and test locations for the evaluator-only
  confidential-read layering and grant-backed write/export denials.
- Preserve any historical pre-Milestone-13 claims only as clearly labeled
  historical baseline, not present behavior.

**Non-goals**

- No source, test, dependency, policy decision, duration value, authority
  assignment, or ratification status change.
- No authentication, provider, policy loader, route, persistence, lifecycle,
  audit, queue, or protected operation.
- No assertion that evaluator behavior is production authorization.

**Entry criteria**

- Current evaluator behavior remains as inspected in this audit.
- Policy draft and ratification package remain non-authoritative and
  `DRAFT — PENDING OWNER RATIFICATION`.
- Decisions 11–36 have not been recovered from an authoritative source.

**Exit criteria and measurable completion**

- Each present-tense implementation claim in the two scoped passages matches
  current source and tests, with line-linked evidence.
- Historical behavior, if retained, is explicitly dated/labeled as superseded.
- A1, B2, U-1 and all owner decisions remain pending/unresolved as recorded;
  no absent historical wording is reconstructed.
- Only the two named documentation files change; local links/line references
  validate. No test run is needed for the documentation-only correction unless
  a documentation check exists.

This recommendation does not unblock any runtime integration stage. A
subsequent engineering milestone must not implement production authentication
or protected APIs until their upstream owner-authority and trust prerequisites
are satisfied.

## 8. Threat-driven verification checklist

For each later implementation stage, test the real assembled adapter,
repositories, operation boundary, and persistence. Synthetic unit tests are
necessary component evidence but not production-security evidence.

- [ ] **Identity spoofing:** request-supplied subject, role, issuer, tenant,
  or `mfa_verified` cannot override adapter-verified context.
- [ ] **Cross-tenant access:** foreign organization/workspace/resource IDs,
  unscoped joins, file handles, passages, derived artifacts, caches, jobs, and
  audit queries return no protected data or effect.
- [ ] **Policy tampering and rollback:** altered content with a matching
  label, draft/unratified policy, stale/superseded version, and unauthorized
  rollback all deny before side effects.
- [ ] **Stale facts:** membership, role, resource ownership/sensitivity,
  grant, assignment, and policy changes invalidate stale snapshots/caches.
- [ ] **Revocation races:** membership/grant/assignment/session revocation
  between request admission and read release, commit, export, or job execution
  safely denies or stops.
- [ ] **Provider failures:** identity, policy, clock, membership, resource,
  grant/assignment, evaluator, repository, and required audit failures never
  fall back to caller data or a cached allow.
- [ ] **TOCTOU:** concurrent ownership, role, policy, expiry, revocation,
  retry, streaming, and commit changes cannot produce an unauthorized effect.
- [ ] **Reviewer independence:** duplicate/linked accounts cannot represent
  distinct people; eligibility is current at submission/finalization; the
  ratified blind-review, abstention, and adjudication rules are enforced.
- [ ] **Contradictory evaluator results:** malformed decisions, mismatched
  reason/allow values, wrong action/resource, or provider/policy-version
  inconsistency deny and cannot be translated by a service into success.

## 9. Limitations and remaining unknowns

### Confirmed from source

- The current evaluator is pure and consumes caller-supplied facts.
- The internal boundary performs shape, scope/action, time, metadata-equality,
  and evaluator-result checks; its injected providers are not authenticated.
- The boundary calls the evaluator without an explicit loaded policy.
- Current evaluator tests cover conservative A1/B2/U-1-like behavior, but
  test fixtures are synthetic.
- Local workflow records and provenance validation do not authenticate
  reviewers or enforce tenant/action permissions.
- No protected application routes/services, authoritative repositories,
  policy loader, persistence, queue, or durable audit integration are present
  in the inspected source.

### Assumptions and unresolved evidence

- Concrete future providers could be trustworthy only if construction,
  provenance, request binding, data sources, lifecycle, and failure behavior
  are specified and verified; no such providers exist to inspect.
- No authoritative record for Decisions 11–36 was found in the evidence
  reviewed. They remain `NOT VERIFIABLE AS NUMBERED`.
- Owner ratification, numeric duration limits, security-personnel authority,
  identity-provider/MFA choices, policy publication/rollback authority,
  audit authority/retention/jurisdiction, and full role/action rules remain
  undecided.
- This audit does not prove deployment configuration, threat resistance,
  operational monitoring, independent review quality, or production security.
  Passing tests cannot establish those claims.
