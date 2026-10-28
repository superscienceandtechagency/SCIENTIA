# SCIENTIA Authorization Implementation Readiness

> **Policy status: `DRAFT — PENDING OWNER RATIFICATION`.**
>
> This document is an evidence-backed implementation-readiness assessment,
> not policy approval, an implemented production authorization boundary, a
> security certification, or proof that tests passed. Decisions 11–36 remain
> **`NOT VERIFIABLE AS NUMBERED`** unless the original authoritative record
> is found and verified.

## 1. Executive summary

SCIENTIA currently has a deterministic, pure authorization evaluator and a
local evidence/research workflow. The evaluator implements conservative
evaluator-level A1, B2, and U-1 behavior: a grant cannot create an otherwise
unsupported write/export permission; an assignment alone cannot authorize
confidential reading; and a confidential read requires the existing
role/assignment path plus a valid scoped read grant. These checks do not
authenticate a person, establish the provenance of caller-supplied facts,
enforce authorization at a service or data-access boundary, or represent an
approved complete role/action policy
([`authorize`](./src/scientia/authorization.py#L254),
[README, “Pure authorization kernel”](./README.md#pure-authorization-kernel)).

No application routes, authentication adapter, authoritative membership or
resource repository, grant/assignment lifecycle, persistence, durable audit
store, queue, or protected-operation service was found in the inspected
`src/scientia/` tree. FastAPI is declared as a dependency, but that declaration
does not constitute an application or security boundary
([`pyproject.toml`](./pyproject.toml#L5)). The existing research workflow
accepts local PDF paths and caller-supplied assessments; its provenance
validation is not user, tenant, or action authorization
([`prepare_research`](./src/scientia/workflow.py#L101),
[`finalize_research`](./src/scientia/workflow.py#L191)).

**Readiness decision:** evaluator-level invariant work is already present.
No protected application capability is ready to enable. The next
implementation work that can proceed safely is limited to non-exposing,
policy-independent boundary foundations and tests; provider, policy,
authority, transaction, and audit prerequisites must be resolved before
routes or services can disclose or mutate protected state. Existing local
functions must not be presented as production-authorized operations.

## 2. Evidence reviewed and implementation status

Inspected the current README, `pyproject.toml`, all modules under
`src/scientia/`, all tests under `tests/`, the policy draft, ratification
package, enforcement-gap assessment, trusted-boundary design, and the
retained checkpoint index and authorization checkpoints.

The current source inventory includes `authorization.py`, evidence and
verification records, PDF ingestion, retrieval, synthesis, and workflow
modules. The authorization code defines immutable input records and
`authorize()`; it trusts the caller to supply principal, membership, resource,
assignment, grant, policy, and evaluation time. It rejects mismatched scope,
invalid/inactive/expired/revoked facts, and missing duration policy in the
branches that require assignments or grants. These are deterministic
function-level checks, not trusted fact acquisition.

The current policy draft records A1, B2, U-1, fixed but unspecified grant and
elevation maxima, assignment default and maximum, audited assignment renewals,
and F2 as owner selections pending formal ratification. The ratification
package is expressly review-only. The trusted-boundary design supplies
architecture and fail-closed guidance, not implemented controls. The gap
assessment includes a pre-Milestone-13 baseline; its later evaluator update
and current source must be used for present evaluator behavior.

The retained [checkpoint index](../../.copilot/session-state/83deb4fa-5d25-4a95-a338-80f3351a1eac/checkpoints/index.md)
lists [“Enforcing Authorization Invariants”](../../.copilot/session-state/83deb4fa-5d25-4a95-a338-80f3351a1eac/checkpoints/001-enforcing-authorization-invari.md)
and [“Authorization Readiness Handoff”](../../.copilot/session-state/83deb4fa-5d25-4a95-a338-80f3351a1eac/checkpoints/002-authorization-readiness-handof.md).
These are session context, not the missing authoritative policy record. The
current repository still does not contain verifiable original text for
Decisions 11–36.

## 3. Requirement traceability

“Test evidence” below identifies existing test source inspected for this
assessment. No tests were run for this documentation-only milestone.

| Requirement | Authority/evidence | Current implementation and tests | Status and remaining work |
|---|---|---|---|
| **A1 — a grant cannot add an action beyond base-role permission** | Owner-selected, pending ratification: [policy draft §2.A](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-a-f). | The evaluator has no role-only write/export allow path and denies grant-backed `WRITE_RESEARCH` and `EXPORT_RESEARCH` at [`authorization.py`](./src/scientia/authorization.py#L341). Regression coverage: [`test_grant_does_not_authorize_action_without_base_role_permission`](./tests/test_authorization.py#L331). | **Enforced only as a conservative evaluator ceiling.** A complete ratified role/action matrix does not exist. Keep unsupported combinations denied; do not infer that every role can write or export. Before adding such permissions, approve the matrix and test every role/action pair. |
| **B2 — assignment alone cannot authorize confidential reading** | Owner-selected, pending ratification: [policy draft §2.B](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-a-f). | Confidential `READ_RESEARCH` requires a valid read grant after role/assignment eligibility in [`authorize`](./src/scientia/authorization.py#L303). Denial test: [`test_confidential_assignment_without_grant_does_not_allow_read`](./tests/test_authorization.py#L308). | **Enforced in the pure evaluator only.** No read service invokes it. Keep confidential content unavailable through any future application route until a trusted, scoped operation boundary enforces this and the applicable policy is ratified. |
| **U-1 — confidentiality-only grant for an otherwise permitted read** | Owner-selected on 2026-10-14 and pending formal ratification: [policy draft §6](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register); also recorded in the [ratification package](./AUTHORIZATION-RATIFICATION-PACKAGE.md#recorded-selections). | The evaluator validates grant facts and requires base role/assignment eligibility before a confidential-read allow; see [`authorization.py`](./src/scientia/authorization.py#L303). Tests cover allowed layered access and grant-only denial: [`test_confidential_read_grant_allows_read_with_role_and_assignment`](./tests/test_authorization.py#L279), [`test_confidential_read_grant_does_not_replace_base_role_or_assignment`](./tests/test_authorization.py#L265). | **Selected, not ratified; evaluator-only.** The grant adds no write/export/delete/audit/elevation permission in this evaluator. Keep confidential reads and grant reliance held at application boundaries until U-1 is ratified, the grant authority/duration decisions are resolved, and service enforcement is verified. |
| **Tenant/workspace/resource scoping** | Draft [conversation-derived rule 1](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-1-10); boundary design [§5](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#5-tenantworkspace-scoped-authorization-flow). | Evaluator compares membership and resource organization/workspace; test: [`test_public_resources_remain_tenant_and_workspace_scoped`](./tests/test_authorization.py#L354). | **Evaluator comparison only.** There is no authenticated membership lookup, scoped resource repository, object-store isolation, cache isolation, or service boundary. Before routes/services, use server-derived tenant/resource ownership and scoped queries at every storage layer; test cross-tenant access end to end. |
| **Identity authenticity, membership provenance, MFA, canonical identity** | README [Pure authorization kernel](./README.md#pure-authorization-kernel); policy draft [§3.1 and U-7](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-1-10); boundary design [§4](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#4-trusted-principal-and-authentication-boundary). | `Principal` and `Membership` are supplied records ([`authorization.py`](./src/scientia/authorization.py#L73)); evaluator checks a supplied MFA boolean. Synthetic tests cover subject mismatch and boolean MFA, including [`test_reviewer_and_administrator_actions_require_mfa`](./tests/test_authorization.py#L833). | **Not implemented as authentication.** No verified identity-provider adapter, session/token validation, authoritative role/membership source, MFA evidence validation, or account-linking service exists. Never accept request-supplied ID, role, tenant, or MFA as proof. Resolve U-7 before counting identities as distinct people. |
| **Grant validity, duration, issuance, approval, renewal, and revocation** | Draft [§2.A, §2.C, §6](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-a-f); ratification package [owner decision workflow](./AUTHORIZATION-RATIFICATION-PACKAGE.md#owner-decision-workflow). | The evaluator validates supplied grant scope, actor-ID inequality, time state, and a generic maximum ([`_validate_grant`](./src/scientia/authorization.py#L386)); tests cover missing maximum and revocation ([`test_missing_grant_duration_policy_fails_closed`](./tests/test_authorization.py#L598), [`test_revoked_grant_is_denied_at_revocation_instant`](./tests/test_authorization.py#L652)). | **Validation exists; lifecycle and authority do not.** U-2, U-5, and U-6 remain open. The evaluator cannot authenticate issuer/approver or establish designation. No issuance, approval, renewal, revocation service, durable record, or audit exists. Keep grant issuance and operational reliance disabled. |
| **Assignment validity, duration, creation, renewal, and revocation** | Draft [§2.E and §6](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-a-f); ratification package [U-4](./AUTHORIZATION-RATIFICATION-PACKAGE.md#owner-decision-workflow). | The evaluator checks supplied assignment scope/state and a generic maximum ([`_validate_assignment`](./src/scientia/authorization.py#L355)); tests cover missing maximum and revocation ([`test_missing_assignment_duration_policy_fails_closed`](./tests/test_authorization.py#L490), [`test_revoked_assignment_is_denied_at_revocation_instant`](./tests/test_authorization.py#L564)). | **Validation exists; lifecycle/default/renewal audit do not.** U-4 is unresolved. Fixture values are synthetic, not approved limits. Keep creation and renewal disabled; do not interpret a configured generic maximum as approved policy. |
| **Administrator elevation** | Draft [§2.D and §6](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-a-f); boundary design [operation holds](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#6-protected-operation-boundaries). | `ADMIN_ELEVATION` is explicitly denied by the evaluator ([`authorization.py`](./src/scientia/authorization.py#L300)); denial test: [`test_undefined_sensitive_permissions_fail_closed`](./tests/test_authorization.py#L483). | **Denied in evaluator; no elevation workflow or service control.** U-3, U-5, and U-6 remain unresolved. Keep elevation disabled until separate approved maximum, authority, independent approval, revocation, audit, MFA step-up, and operation-level enforcement are in place. |
| **Deletion and restore** | Draft [conversation-derived rule 6](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-1-10); boundary design [operation table](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#6-protected-operation-boundaries). | `DELETE_RESEARCH` is denied by the evaluator ([`authorization.py`](./src/scientia/authorization.py#L300)); there is no deletion or restoration workflow in the inspected source tree. | **Not implemented; evaluator denies deletion.** Keep deletion/restore unavailable until authoritative policy, tombstone/purge/recovery behavior, audit, and transactional authorization are designed, implemented, and tested. |
| **High-stakes review, classification, and independent adjudication** | Draft [§3.1–3.2](./AUTHORIZATION-POLICY-DRAFT.md#3-conversation-derived-approved-rules) records these as conversation-derived rules; the original complete policy record is unavailable. | `ClaimAssessment` has a `reviewer_label`, not an authenticated reviewer event ([`verification.py`](./src/scientia/verification.py#L129)). Synthesis treats a `HUMAN_REVIEWED` assessment with an outcome as a finding ([`synthesis.py`](./src/scientia/synthesis.py#L31), [`synthesize`](./src/scientia/synthesis.py#L83)); tests verify this record partition ([`test_only_reviewed_assessments_with_outcome_become_findings`](./tests/test_synthesis.py#L117)). | **No high-stakes workflow.** No authenticated distinct reviewers, blinded second submission, eligibility-at-finalization, abstention workflow, disagreement state, third-person adjudication, or classification-approval flow exists. `HUMAN_REVIEWED` is not dual review. Keep high-stakes finalization and classification changes disabled. |
| **Operation-boundary authorization and revalidation** | Policy draft [§6](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register); boundary design [§6–7](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#6-protected-operation-boundaries). | Only direct calls to the pure evaluator exist; local research preparation/finalization are in [`workflow.py`](./src/scientia/workflow.py#L101) and [`workflow.py`](./src/scientia/workflow.py#L191). No route/service/job integration was found. | **Not implemented.** No boundary checks at read, write, export, delete, review-finalization, or commit/release; no TOCTOU or revocation-race protection. Do not expose protected routes/services until a mandatory facade and relevant atomic/revalidation controls exist. |
| **Durable, restricted, content-free audit** | Draft [rule 9](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-1-10); boundary design [§8](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#8-audit-event-design). | The evaluator returns a decision only. No audit sink, audit-query service, or audit-read recording was found. | **Not implemented.** Keep grant, assignment, elevation, deletion, classification, high-stakes review, and audit access workflows disabled until required events are durable, access-controlled, content/secret-free, and fail closed on persistence failure. |
| **Policy version integrity and rollback protection** | Draft [§1 and §7](./AUTHORIZATION-POLICY-DRAFT.md#1-purpose-and-authority); boundary design [§5, §9](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#9-dependency-ordered-implementation-roadmap). | `AuthorizationPolicy` contains only generic optional assignment/grant maxima ([`authorization.py`](./src/scientia/authorization.py#L224)); no policy artifact loader, ratification provenance, integrity, supersession, or rollback check exists. | **Not implemented.** Do not treat draft or test policy values as approved. A trusted, provenance-verified ratified policy source is a prerequisite for policy-sensitive capabilities. |
| **Time-of-check/time-of-use, replay, jobs, revocation ordering** | Boundary design [§7](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#7-transactional-consistency-replay-revocation-and-jobs). | Evaluator accepts caller-supplied `evaluated_at`; there is no transaction boundary, queue, job worker, idempotency store, or revocation propagation. | **Not implemented.** Require trusted server time, consistent state/effect boundaries, current revalidation before sensitive effects, durable replay protection for mutations, and tested safe stop/cancel semantics before adding affected services. |
| **Policy record integrity / Decisions 11–36** | Draft [§2.F and §7](./AUTHORIZATION-POLICY-DRAFT.md#7-decision-history-and-record-integrity); ratification package [Historical evidence limitation](./AUTHORIZATION-RATIFICATION-PACKAGE.md#historical-evidence-limitation). | The current draft and checkpoint index do not contain the original authoritative numbered record. | **Historical evidence unresolved.** Keep Decisions 11–36 **`NOT VERIFIABLE AS NUMBERED`**. Do not reconstruct, renumber, or infer policy from checkpoint summaries. |

## 4. Readiness categories

### Evidence-backed invariants already implemented in the evaluator

- Scope mismatch, inactive membership, unknown action, unsupported sensitive
  actions, expired/revoked/future grant or assignment, duration-policy absence,
  and grant/assignment scope mismatch deny in the relevant evaluator branches.
- Grant-backed write/export have no allow path; this is conservative denial,
  not a complete role/action matrix.
- Confidential reads require base-role/assignment eligibility and a separate
  scoped read grant. Neither an assignment nor a read grant alone supplies
  both conditions.
- These claims describe the pure evaluator only, not production security.

### Safe work that can proceed without new policy choices

- Maintain explicit deny-by-default behavior for unknown and unsupported
  actions.
- Add boundary-independent tests and structural scaffolding that cannot expose
  or mutate protected data, provided it does not claim authentication,
  authority, policy approval, or production enforcement.
- Define typed interfaces for trusted identity, scoped resource resolution,
  policy loading, authorization decisions, transaction/revalidation, and
  audit dependencies without selecting an identity provider, persistence
  engine, queue, deployment model, jurisdiction, retention period, or policy
  value.
- Keep implementation status and historical provenance distinct in future
  documentation.

### Policy-sensitive requirements still unapproved

- Owner selections A1, B2, U-1, fixed confidential grant maximum, separate
  elevation maximum, assignment default/maximum, audited renewals, and F2
  remain pending formal ratification.
- No permission matrix or additional grantable action may be inferred from
  A1. Do not infer security-personnel designation, approval duties,
  identity-linking rules, durations, MFA assurance levels, audit retention,
  or deployment jurisdiction.
- Conversation-derived high-stakes review and classification rules must not
  be treated as recovered authoritative numbered policy.

### Capabilities that must remain disabled or fail closed

Until both policy prerequisites and trusted enforcement are satisfied, do not
expose application routes or services for:

- public or confidential research reads, including list/search/download or
  derived-content access;
- writes, exports, or disclosure of audit metadata;
- grant or assignment issuance, approval, renewal, revocation, or reliance;
- administrator elevation;
- deletion, purge, or restore;
- ordinary review submissions, high-stakes review/finalization, and
  classification changes;
- queued or running protected work.

The absence of an application endpoint in the current source tree is not a
runtime control over direct local function use. No present code path should be
described as a production authorization boundary.

## 5. Unresolved policy and owner-authority inventory

The following items cannot safely be inferred from code, tests, draft wording,
or retained checkpoints:

1. **Whole-policy ratification:** ratifier, date, approved version, amendments,
   and complete applicable policy. Preserve
   `DRAFT — PENDING OWNER RATIFICATION`.
2. **U-2:** numeric fixed maximum for confidential-content grants.
3. **U-3:** numeric fixed maximum for administrator elevation, separate from
   U-2.
4. **U-4:** numeric default and maximum research-assignment durations.
5. **U-5:** who designates security personnel and the scope of issue,
   approval, revocation, and audit authority.
6. **U-6:** whether issuer and approver need separate operational duties in
   addition to distinct identities.
7. **U-7:** authoritative canonical identity/account-linking evidence and
   process, including duplicate-account treatment.
8. **U-8 / historical record:** whether the original authoritative Decisions
   1–36 record can be located and verified. Until then, Decisions 11–36
   remain `NOT VERIFIABLE AS NUMBERED`; never reconstruct the missing text or
   numbering.
9. **Complete role/action matrix:** which actions each base role permits,
   which require assignment, and how multiple roles combine. A1 alone does
   not supply this matrix.
10. **High-stakes authority and eligibility:** confirm the applicable
    independent-review, blind second submission, abstention, disagreement,
    third-person adjudication, and classification proposal/confirmation
    rules in the ratified policy; exact historical numbering/provenance is
    unavailable.
11. **MFA detail:** required assurance evidence, step-up/session freshness,
    and interpretation by role; a boolean evaluator field is not an approved
    authentication contract.
12. **Audit governance:** authorized audit roles/scope, retention, integrity,
    audit-read controls, and jurisdiction. No numeric retention period or
    jurisdiction is established.
13. **Policy publication authority:** how ratification provenance, integrity,
    supersession, version selection, and authorized rollback are established.
14. **Authentication transport and provider configuration:** supported
    identity provider, client types, protocol flows, session, logout,
    revocation, CSRF, and token semantics. The project context requires a
    replaceable OIDC-compatible boundary and MFA for designated roles, but
    does not select a provider or settle all assurance details.
15. **Deployment model:** managed versus self-hosted/client-controlled
    deployment remains a comparison, not an approved choice.

## 6. Dependency-ordered implementation roadmap

This sequence is conditional and does not authorize implementation of
unratified policy. No capability may be enabled merely because its earlier
roadmap item is complete.

| Order | Work | Depends on | Acceptance criteria |
|---|---|---|---|
| 0 | Establish policy authority. Ratify a versioned record or continue to hold policy-sensitive work; resolve only the authority items needed for each capability. | Owner ratification and authoritative evidence. | Ratifier/date/version/amendments recorded; Decisions 11–36 remain explicitly unverified unless the source is found; no numeric values or permissions inferred. |
| 1 | Specify a trusted-principal contract and replaceable authentication adapter; define verified session and MFA evidence without binding domain code to a vendor. | Supported provider/transport and authentication/MFA requirements; U-7 before claims of distinct humans. | Caller-supplied ID, role, tenant, and MFA fields cannot construct or override a trusted principal; invalid/unavailable authentication or required MFA denies. |
| 2 | Implement authoritative account/membership resolution and tenant/workspace-scoped resource repositories, including backing stores and caches. | Trusted-principal contract; approved canonical identity process before identity-independence decisions. | No unscoped protected lookup; inactive or cross-tenant membership/resource tests deny across every store involved. |
| 3 | Add one mandatory authorization facade that builds one-action contexts from trusted facts, trusted server time, and a provenance-verified policy version. | Orders 0–2; complete role/action matrix for any newly allowed actions. | No application handler/job can provide effective authorization facts directly or bypass the facade; missing, stale, unapproved, or rolled-back policy/time/facts deny. |
| 4 | Establish state-change consistency, transactional/outbox behavior, content-free audit storage, audit access controls, and audit-read recording. | Chosen persistence/transaction design; applicable audit authority/retention/jurisdiction decisions. | Required state change and audit commit together or neither does; audit failure prevents protected success; events exclude content and secrets; audit reads are authorized and recorded. |
| 5 | Integrate read, write, export, and ordinary review service boundaries with authorization, scope, sensitivity, and current-state checks. | Orders 0–4; ratified rules for each action; U-2/U-4 and authority decisions where grants/assignments are used. | Tests cover request admission, scoped data access, output release, and revalidation; no unsupported action or caller claim grants access. Keep all affected operations held until their individual criteria pass. |
| 6 | Add assignment and grant lifecycle services only for policy-authorized types; implement approval, expiry, renewal, revocation, and durable audit. | Orders 0–4; U-2/U-4/U-5/U-6 and applicable ratification. | Creation, approval, renewal, and revocation enforce trusted actor authority, exact scope, approved duration, distinct roles/duties as decided, and mandatory audit; missing configuration denies activation. |
| 7 | Add deletion/restore and elevation as distinct sensitive workflows. | Orders 0–4; approved deletion/recovery authority; U-3/U-5/U-6; applicable MFA requirements. | Access is denied at deletion request; purge/restore obey durable deletion state; elevation obeys its separate approved maximum, authority, revocation, audit, and revalidation controls. |
| 8 | Implement classification and high-stakes review as separate auditable workflows. | Ratified review/classification policy; Orders 0–4; U-7 and resolved eligibility/authority. | Distinct canonical actors, blind second review, abstention, disagreement, adjudication, and finalization revalidation are enforced; classification proposal/confirmation and sensitivity changes are atomic and audited. |
| 9 | Add asynchronous jobs, replay/idempotency, revocation cancellation, safe stop points, and concurrency/failure verification where needed. | Relevant operation workflows and transaction/outbox contracts. | A revoked or stale job cannot begin or perform later protected effects; retries do not duplicate effects or disclose stale content; race and failure-injection tests pass. |
| 10 | Run integrated security verification and independent review; update implementation status only against observed behavior. | All capability-specific prerequisites and deployment configuration. | Targeted and full checks pass with actual outputs recorded; remaining risks are explicit; no test result is represented as certification. |

## 7. Required security tests for later implementation

Tests below are requirements for the appropriate implementation milestone;
they have not been run or implemented as a service-level suite here.

- **Identity spoofing:** forged subject, issuer, role, organization/workspace,
  MFA assertion, token purpose, audience, session, or account-link claim cannot
  alter adapter-derived identity or membership. Invalid, expired, revoked, or
  unavailable required authentication denies.
- **Tenant isolation:** cross-organization/workspace resource selectors,
  unscoped lookups, object/blob keys, search indexes, caches, derived content,
  and job payloads cannot access another tenant's data. Verify both allow and
  deny at the repository and operation boundary.
- **Privilege escalation / A1:** exercise every ratified role/action pair
  with and without matching grants. Grants cannot turn role denial into allow;
  a read grant cannot authorize write, export, deletion, audit, or elevation.
  Unknown actions and mappings deny.
- **Confidentiality / B2 / U-1:** assignment-only confidential read denies;
  grant-only read denies without base-role and assignment eligibility; the
  complete eligible path allows only the confidentiality condition. Include
  public-resource rules only as supported by ratified policy.
- **Grant and assignment lifecycle:** test missing/unapproved policy values,
  wrong scope, future issue/assignment, expiry boundaries, revocation,
  duration boundaries, renewals, authority separation, and audit failure.
  Test synthetic configured values as test data only, never as approved
  duration evidence.
- **Revocation races and TOCTOU:** revoke membership, grant, or assignment
  after initial authorization and before retrieval, commit, export release,
  queued execution, or finalization. Prove the later side effect denies or
  stops at its defined safe boundary.
- **Policy rollback:** reject unsigned/tampered/unratified/superseded policy,
  unauthorized rollback, missing provenance, and stale policy versions;
  decisions bind to the verified version.
- **High-stakes review:** same canonical person, self-review, duplicate
  accounts, ineligible/revoked reviewer, or second reviewer exposed to the
  first review cannot satisfy independence. Verify abstention is not approval,
  disagreement remains unresolved, and only a separately authorized third
  person can adjudicate where ratified policy requires it.
- **Audit and disclosure:** required audit-write failure aborts the protected
  operation; audit events contain no document/passage text, secrets, tokens,
  or raw request bodies; audit reads are scoped and themselves audited;
  sensitive denials do not reveal resource existence where that is protected.
- **Operation coverage:** demonstrate that no protected route, service,
  background job, alternate storage path, or direct helper bypasses the
  mandatory boundary. Exercise current-state checks at admission and the
  relevant sensitive side effect.

## 8. Architectural prerequisites before routes or services

Do not add or expose application routes/services that access protected data or
mutate protected state until all applicable prerequisites are met:

1. A ratified, versioned policy artifact and an explicit policy loader that
   verifies provenance, integrity, supersession, and rollback authority.
2. A replaceable OIDC-compatible authentication adapter with validated token
   purpose, issuer, audience, session lifecycle, and required MFA evidence;
   provider and transport must be selected through owner-approved project
   decisions where not already authoritative.
3. A trusted-principal construction path unavailable to request payloads;
   authoritative account, membership, role, and canonical identity
   resolution.
4. Server-derived organization/workspace/resource ownership and scoped
   queries for relational data, objects, search indexes, caches, and derived
   artifacts. Client identifiers are selectors only.
5. A mandatory authorization facade that evaluates one action/resource at a
   time using trusted facts, approved policy, and server-controlled time.
6. Explicit per-operation service APIs; no unrestricted resource getter or
   alternate code path that bypasses authorization.
7. A defined consistency/linearization strategy so current authorization and
   protected reads/writes are consistent; long-running or streamed work
   revalidates before further disclosure or side effects.
8. Durable, access-controlled, content-free audit events and fail-closed
   behavior when required audit cannot be persisted. Resolve audit scope,
   retention, integrity, and jurisdiction before relying on those controls.
9. Lifecycle-specific policy and authority for grants, assignments,
   elevation, deletion/restore, classification, and high-stakes review before
   enabling each capability.
10. Revocation propagation, job rehydration, idempotency/replay controls,
    cancellation/safe-stop semantics, monitoring, and failure recovery before
    adding asynchronous protected work.
11. Security regression, integration, concurrency, and failure-injection
    tests for each route/service and underlying repository, plus independent
    deployment-specific review before production exposure.

FastAPI's presence in `pyproject.toml` is not evidence that any of these
prerequisites exists. No application routes or services were found in the
current source inventory.

## 9. Verification evidence and limitations

### Verification performed for this document

- Inspected current contents of the README, `pyproject.toml`, authorization
  evaluator and tests, workflow/verification/synthesis modules and tests,
  policy draft, ratification package, enforcement-gap assessment,
  trusted-boundary design, and retained authorization checkpoint index and
  checkpoints.
- Confirmed the readiness document was not present before creation.
- Compared the evaluator behavior, test expectations, policy status,
  historical evidence status, and local workflow scope against the claims
  above.
- No tests, builds, or lints were run, as required for this
  documentation-only milestone.
- Prior test and lint results recorded in earlier project documents are
  historical reports; they are not fresh verification for this assessment and
  are not production-security evidence.

### Limitations

This assessment does not ratify policy, recover the original Decisions 11–36,
establish production identity or storage controls, or prove that tests pass.
Evaluator-level checks and synthetic tests are not a trusted application
boundary. The lack of routes in the inspected source tree is not a control
against direct library use. Conversation-derived policy context and retained
checkpoints are not substitutes for an authoritative ratified policy record.
