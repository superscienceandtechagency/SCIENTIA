# SCIENTIA Authorization Enforcement Gap Assessment

> **Baseline report:** The gap findings below describe the evaluator before
> Milestone 13. The “Milestone 13 evaluator update” section records subsequent
> changes and supersedes those findings for pure-evaluator behavior only.

## Executive summary

This assessment documents the difference between SCIENTIA's recorded
authorization requirements and the current repository implementation. The
authorization policy remains **`DRAFT — PENDING OWNER RATIFICATION`**; this
assessment is not approval to implement draft policy as approved policy.
Decisions 11–36 remain **`NOT VERIFIABLE AS NUMBERED`** unless the original
authoritative record is found.

The current `scientia.authorization` module is a deterministic evaluator over
immutable, caller-supplied facts. It is not an authentication boundary or an
application authorization service. This repository does not provide grant or
assignment lifecycle operations, API routes, persistence, queues, audit
storage, or production tenant isolation ([README.md, “Pure authorization
kernel”](./README.md#pure-authorization-kernel); [authorization.py,
`authorize`](./src/scientia/authorization.py#L254)).

Confirmed baseline policy mismatches (before Milestone 13):

1. **Pre-Milestone-13 baseline:** a matching `WRITE_RESEARCH` or
   `EXPORT_RESEARCH` grant could allow that action without checking whether
   the recipient's base role permitted it (**A1 gap**).
2. **Pre-Milestone-13 baseline:** an active assignment could allow
   `READ_RESEARCH` on a confidential resource without a separate
   confidential-content grant (**B2 gap**).
3. **Pre-Milestone-13 baseline:** a matching `READ_RESEARCH` grant could
   allow reading without independently verifying role and assignment
   eligibility (**U-1 gap**). The baseline test suite expected such an allow
   for an organization administrator with no assignment.

Other protection is partial: the evaluator denies grant- or assignment-based
decisions when its generic maximum duration is absent, and always denies
`ADMIN_ELEVATION`; however, it has no approved policy-version source, distinct
grant/elevation maxima, default assignment duration, or grant/assignment
creation, approval, renewal, and audit workflow. Supplying a generic duration
does not establish that the value was approved.

High-stakes review requirements are described in the draft as
conversation-derived rules, not verified against a complete authoritative
numbered policy. No high-stakes review workflow exists in the inspected code.
The current `HUMAN_REVIEWED` assessment state and synthesis partition are not
two-person approval or independent-review enforcement.

**Recommendation:** retain all affected capabilities behind explicit
fail-closed boundaries. Resolve owner-authority policy items and ratify a
versioned policy before implementing any policy-sensitive behavior. The
Milestone 13 evaluator update below closes the identified A1/B2/U-1
pure-evaluator gaps only; preserve those regression cases while prioritizing
trusted identity/policy inputs and service-level lifecycle and audit
boundaries. Enable a capability only after its applicable policy and
operation-boundary controls are verified. The plan below is conditional; it
selects no policy values.

## Evidence status and scope

Evidence is separated as follows:

- **Recorded owner selections:** A1, B2, and F2 and other A–F selections are
  transcribed in [AUTHORIZATION-POLICY-DRAFT.md, Section 2](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-a-f).
  They remain unratified.
- **U-1:** the draft records the selected confidentiality-only grant rule in
  [Section 6](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register), pending
  formal ratification.
- **Conversation-derived review requirements:** the draft records two
  independent authenticated reviewers, blind second submission, abstention
  handling, unresolved disagreement with third-person adjudication, and
  revalidation at finalization in
  [Section 3](./AUTHORIZATION-POLICY-DRAFT.md#3-conversation-derived-approved-rules).
  Those are recorded historical statements, not evidence that the current
  code enforces them or that the full numbered policy record was recovered.
- **Repository implementation evidence:** the original gap table and
  traceability matrix below record pre-Milestone-13 behavior and test
  expectations. The later evaluator update records present evaluator
  behavior. Tests were inspected but not run in the original
  documentation-only assessment.
- **Retained checkpoint evidence:** [004-tenant-authorization-design.md](../../.copilot/session-state/ad3d50ed-bfd7-4a03-9879-1d3ac90766fa/checkpoints/004-tenant-authorization-design.md)
  summarizes intended design and test gaps. [005-authorization-policy-draft-rev.md](../../.copilot/session-state/ad3d50ed-bfd7-4a03-9879-1d3ac90766fa/checkpoints/005-authorization-policy-draft-rev.md)
  documents the A1/B2 review and the earlier unresolved A1/B2 interaction.
  Checkpoints are retained context, not a substitute for the missing
  authoritative Decisions 1–36 record. The current draft's later U-1 selection
  is the current recorded status.

## Gap assessment

The following table preserves the findings and recommendations from the
pre-Milestone-13 baseline. In that table, “Current behavior” means behavior
when the baseline was written, not current repository behavior. For A1, B2,
and U-1, the pure-evaluator gap has since been addressed as recorded in
[Milestone 13 evaluator update](#milestone-13-evaluator-update); no application
service enforcement was added.

| Requirement | Evidence | Baseline behavior (pre-Milestone 13) | Risk at baseline | Proposed remediation at baseline |
|---|---|---|---|---|
| **A1 — grants cannot add a base-role action** | Draft §2.A and §5; evaluator branch [authorization.py:331–339](./src/scientia/authorization.py#L331); allowing test [test_authorization.py:279–290](./tests/test_authorization.py#L279). | For `WRITE_RESEARCH` and `EXPORT_RESEARCH`, the evaluator validates the supplied grant and action match, then allows it. It does not check a base-role permission matrix. A synthetic test allows an organization administrator's matching export grant. | A grant can elevate an action not independently allowed by the recipient's base role; least privilege is not enforced. The exact role/action matrix is not defined by A1 alone. | After ratification and approval of an explicit role/action mapping, require both base-role permission and the action-specific grant. Add denial tests for every role/action pair where the role does not independently permit the action. Keep unknown mappings denied. |
| **B2 — assignment does not grant confidential reading** | Draft §§2.B, 5; baseline `READ_RESEARCH` branch [authorization.py:303–324](./src/scientia/authorization.py#L303); historical assignment allow test [test_authorization.py:360–371](./tests/test_authorization.py#L360). | At baseline, researcher/reviewer roles used `_validate_assignment`; the helper checked subject, tenant/workspace/resource scope, time, revocation, and a configured maximum, but not resource sensitivity ([authorization.py:344–372](./src/scientia/authorization.py#L344)). The cited historical test expected a confidential read to be allowed for an assigned reviewer who also had the administrator role. | At baseline, assignment alone could expose confidential content contrary to the selected B2 rule. The draft's fail-closed hold was not wired to a service and did not change evaluator behavior. | Baseline remediation: after ratification, make confidentiality an independent condition requiring the separately authorized confidentiality grant and role/assignment eligibility. The evaluator-level change is recorded in [Milestone 13 evaluator update](#milestone-13-evaluator-update); service enforcement remains absent. |
| **U-1 — read grant satisfies confidentiality only** | Draft §6; baseline `READ_RESEARCH` branch [authorization.py:303–310](./src/scientia/authorization.py#L303); historical allow test [test_authorization.py:265–276](./tests/test_authorization.py#L265). | At baseline, a valid matching read grant immediately allowed `READ_RESEARCH` without checking whether the base role and assignment independently permitted it. Existing baseline action-mismatch tests showed a read grant did not transfer to write, submit-review, delete, or audit actions ([test_authorization.py:204–246](./tests/test_authorization.py#L204)); a separate matching write/export grant could independently allow those actions without A1 base-role enforcement. Delete and admin elevation denied even at baseline ([authorization.py:300–301](./src/scientia/authorization.py#L300)). | At baseline, confidentiality permission could be mistaken for general read entitlement. The earlier tests did not prove the subsequently selected confidentiality-only rule or whole-policy action containment. | Baseline remediation: after ratification, require base-role and assignment authorization before applying a read grant solely as the confidentiality condition. The evaluator-level change is recorded in [Milestone 13 evaluator update](#milestone-13-evaluator-update); service enforcement remains absent. |
| **Grant issuance/approval/renewal and authority** | Draft §§2.A, 3.2, 6; `AccessGrant` is a fact record [authorization.py:155–194](./src/scientia/authorization.py#L155); generic evaluator validation [authorization.py:375–405](./src/scientia/authorization.py#L375); README says lifecycle services are absent ([README.md](./README.md#pure-authorization-kernel)). | No issue, approval, renewal, or revocation workflow exists. Evaluation compares caller-supplied subject/issuer/approver IDs and rejects equality conflicts; it cannot authenticate actors or verify designated-security authority. | No trusted control prevents an unauthorized caller from constructing grant facts. No enforceable audit trail or owner-approved grant-type-specific duration exists. | Keep all issuance/approval/renewal disabled. After U-2, U-5, U-6 and whole-policy ratification, introduce a trusted lifecycle boundary that derives authority from trusted identity and policy sources, enforces approved scope/duration/action eligibility, and persists required independent approval and audit before activation. |
| **Administrator elevation** | Draft §2.D and §6; evaluator explicitly denies `ADMIN_ELEVATION` [authorization.py:300–301](./src/scientia/authorization.py#L300). | This kernel cannot grant elevation. No elevation lifecycle, separate elevation maximum, approval/audit workflow, or service boundary is implemented. | Treating a generic grant maximum or an in-memory deny branch as an approved and complete elevation control would be unsafe. | Keep disabled. Enable only after a separate U-3 maximum is approved and configured in a trusted policy source, designation/separation decisions U-5/U-6 are resolved, required audit/approval is durable, and an independently reviewed elevation path is implemented and tested. |
| **Research assignment creation and renewal** | Draft §2.E and §6; assignment record [authorization.py:127–153](./src/scientia/authorization.py#L127); generic max [authorization.py:224–245](./src/scientia/authorization.py#L224); missing-max denial test [test_authorization.py:438–445](./tests/test_authorization.py#L438). | `Assignment` represents supplied facts; the module does not create, approve, renew, or audit assignments. `_validate_assignment` denies without a generic maximum, but does not enforce an approved default or renewal workflow. Tests supply a fixture maximum (seven days) which is test data, not approved policy ([test_authorization.py:22–24, 91–103](./tests/test_authorization.py#L22)). | A caller can provide a configured generic maximum without demonstrating owner approval; no default duration, renewal approval, or required renewal audit exists. | Keep creation/renewal disabled. After U-4 and whole-policy ratification, use trusted approved default/max configuration, require scoped assignment approval/expiry, record all required renewal audit fields, and fail closed if policy or durable audit is unavailable. |
| **Authenticated identities, canonical identity, and actor authority** | Draft §§3.1–3.2, U-5–U-7; `Principal` and `Membership` inputs [authorization.py:73–108](./src/scientia/authorization.py#L73); evaluator contract [authorization.py:254–263](./src/scientia/authorization.py#L254); README limitations ([README.md](./README.md#pure-authorization-kernel)). | The kernel checks supplied principal/membership subject equality, active membership, tenant/workspace equality, and supplied MFA boolean. It does not authenticate the principal, validate membership provenance, prove MFA, link accounts, establish distinct people, or verify grantor authority. | Caller-controlled or stale assertions can be mistaken for verified identity, role, MFA, or reviewer independence. Duplicate accounts could appear to be distinct people. | Keep protected operations behind trusted identity and membership adapters. Resolve U-5 through U-7 before relying on actor independence, grant authority, or high-stakes reviewer uniqueness. Never accept effective role, tenant scope, actor identity, or MFA proof from an untrusted request payload. |
| **High-stakes review and classification** | Draft §3.1 records two distinct authenticated reviewers, blind second submission, unresolved disagreement, no abstention-as-approval, third-person adjudication, and separate classification proposal/confirmation. Additional eligibility/revalidation rules appear in §3.2. Existing structures are [verification.py:129–160](./src/scientia/verification.py#L129) and [synthesis.py:24–47](./src/scientia/synthesis.py#L24). | No high-stakes review workflow is implemented. `ClaimAssessment` has an optional `reviewer_label`, not a trusted reviewer identity or review event history. `HUMAN_REVIEWED` is a single state; `synthesize` treats it as a completed finding when an outcome exists. No first-review concealment, distinct-person check, abstention state, adjudicator, eligibility-at-finalization check, or classification approval exists. Existing tests cover assessment consistency and synthesis partitioning, not independent reviewers ([test_synthesis.py:117](./tests/test_synthesis.py#L117)). | A single human-entered assessment can be represented as reviewed and included as a finding; this does not satisfy dual-review or adjudication requirements. | Do not treat current assessments/findings as high-stakes-approved. After policy authority and U-7, implement a separate review state machine with authenticated canonical actors, blind second review, eligibility revalidation, explicit abstention, unresolved disagreement, and distinct authorized adjudication; persist immutable review events and required audit. |
| **Revalidation at operation boundaries** | Draft §3.2 records revalidation before queued execution and sensitive boundaries, plus behavior on revocation. README says queues/services are absent ([README.md](./README.md#pure-authorization-kernel)); retained design checkpoint records execution-time revalidation as a design concern ([004 checkpoint](../../.copilot/session-state/ad3d50ed-bfd7-4a03-9879-1d3ac90766fa/checkpoints/004-tenant-authorization-design.md#L116)). | Only a caller-invoked `authorize(context)` exists. No queue, API, resource operation, persistence commit, export, or review-finalization boundary is wired to invoke it or revalidate state. | Authorization may become stale between initial decision and operation; revoked membership/grant/assignment could still permit queued or in-flight work if a future service checks only once. | When service/job paths exist, derive trusted facts and check at request admission, before queued execution, and immediately before sensitive commit/export/finalization; define safe cancellation/stop boundaries; test revocation and stale-context races. Do not claim this kernel provides enforcement until all relevant paths are wired. |
| **Audit and policy holds** | Draft §§3.1, 3.2, 5–6; README states audit storage and audit-read recording are absent ([README.md](./README.md#pure-authorization-kernel)). | There is no durable audit sink or service-level hold. The policy draft/package cannot disable any callable evaluator branch. | Required grant/renewal/approval events and audit reads cannot be demonstrated; implementers or operators could mistake documentation for a control. | Keep audited/privileged capabilities disabled until append-only audit persistence, content/secret exclusion, audit-read recording, and fail-closed behavior on audit-write failure are implemented and verified. |

## Traceability matrix

This matrix preserves the source/test traceability as recorded before
Milestone 13. Present evaluator behavior for A1, B2, and U-1 is described in
the [Milestone 13 evaluator update](#milestone-13-evaluator-update); none of
these component-level changes introduced application enforcement.

“Existing tests” below means the cited tests were found in source; they were
not executed for this assessment. “No test” means no test was found that
establishes the stated end-to-end requirement, not that the repository has no
tests in that area.

| Requirement | Policy evidence and status | Implementation locations | Existing test coverage and gap |
|---|---|---|---|
| **A1 — No grant-added action** | Owner-selected, pending ratification: draft §2.A; baseline implementation gap noted in draft §5 at the time. | Grant actions: [authorization.py:331–339](./src/scientia/authorization.py#L331); base role records: [authorization.py:13–21](./src/scientia/authorization.py#L13). | Historical baseline test [test_separate_confidential_export_grant_authorizes_export, lines 279–290](./tests/test_authorization.py#L279) asserted a grant-backed export allow for organization administrator. Current evaluator denial and regression coverage are recorded in [Milestone 13 evaluator update](#milestone-13-evaluator-update). |
| **B2 — Assignment alone cannot read confidential content** | Owner-selected, pending ratification: draft §2.B; baseline implementation gap noted in draft §5 at the time. | Read branch: [authorization.py:303–324](./src/scientia/authorization.py#L303); assignment validator: [authorization.py:344–372](./src/scientia/authorization.py#L344). | Historical baseline test [test_administrator_role_does_not_cancel_separate_reviewer_assignment, lines 360–371](./tests/test_authorization.py#L360) asserted an allow on confidential sensitivity with assignment. Current evaluator denial and regression coverage are recorded in [Milestone 13 evaluator update](#milestone-13-evaluator-update). |
| **U-1 — Read grant is confidentiality-only** | Owner-selected on 2026-10-14, pending formal ratification: draft §6. | Baseline read-grant branch: [authorization.py:303–310](./src/scientia/authorization.py#L303). | Historical test [test_scoped_confidential_read_grant_allows_only_read, lines 265–276](./tests/test_authorization.py#L265) allowed organization administrator with no assignment. Current layered behavior and regression tests are recorded in [Milestone 13 evaluator update](#milestone-13-evaluator-update). |
| **Grant actor separation and authority** | Draft §2.A / U-5 / U-6: distinct IDs selected; designation and operational separation unresolved. | Identifier checks: [authorization.py:389–395](./src/scientia/authorization.py#L389); no trusted actor registry. | [Grant issuer/approver distinction test](./tests/test_authorization.py#L782) covers identifier inequality. No test verifies authenticated identity, designated status, or authorized duties. |
| **Grant and assignment duration controls** | U-2, U-3, U-4 pending; no approved numeric values in draft §§2 and 6. | Generic optional maxima: [authorization.py:224–245](./src/scientia/authorization.py#L224); assignment check [lines 344–372](./src/scientia/authorization.py#L344); grant check [lines 375–405](./src/scientia/authorization.py#L375). | Missing-max tests exist at [test_authorization.py:438–445](./tests/test_authorization.py#L438) and [546–557](./tests/test_authorization.py#L546); maximum-boundary tests use synthetic fixture values. No lifecycle/default/renewal/audit tests exist. |
| **Elevation disabled** | U-3 pending; separate maximum required by draft §2.D. | `ADMIN_ELEVATION` deny: [authorization.py:300–301](./src/scientia/authorization.py#L300). | Existing undefined-sensitive-action denial test is [test_authorization.py:431–435](./tests/test_authorization.py#L431); no elevation workflow tests exist. |
| **Trusted identity and authorization facts** | README and draft §4 describe caller-supplied facts and missing authentication/account linking. | Input records [authorization.py:73–108](./src/scientia/authorization.py#L73); evaluator [authorization.py:254–295](./src/scientia/authorization.py#L254). | Synthetic principal/membership mismatch, inactive membership, MFA, and tenant-scope tests exist ([subject mismatch](./tests/test_authorization.py#L377), [inactive membership](./tests/test_authorization.py#L370), [MFA](./tests/test_authorization.py#L833), [tenant scope](./tests/test_authorization.py#L354)); no authenticated adapter, forged request, or canonical-account tests exist. |
| **High-stakes independent review** | Draft §3.1 / §3.2: conversation-derived requirements with unverified original numbering and approval history. | Only generic `ClaimAssessment` and `HUMAN_REVIEWED` data model ([verification.py:32–38, 129–160](./src/scientia/verification.py#L129)); synthesis partition [synthesis.py:24–47, 95–116](./src/scientia/synthesis.py#L95). | Assessment/synthesis tests assert record consistency and state partition ([test_verification.py:206](./tests/test_verification.py#L206), [test_synthesis.py:117](./tests/test_synthesis.py#L117)); no test for two authenticated distinct reviewers, blind submission, abstention, adjudication, or eligibility revalidation. |
| **Operation-boundary revalidation** | Draft §3.2 records revalidation requirements; README describes absence of queues/application services. | No operation/service/job boundary exists in the inspected repository; pure evaluator entry is [authorization.py:254–273](./src/scientia/authorization.py#L254). | No service, queue, pre-commit, or revocation-during-operation tests exist. Current kernel unit tests cannot prove boundary enforcement. |

## Prioritized remediation sequence and dependencies

The following is a dependency-aware plan, not authorization to implement
unratified selections. Where the sequence depends on owner authority, preserve
the hold and continue only independent work that does not enable the affected
capability.

1. **Maintain the hold and establish policy authority.**
   - Keep the policy draft labeled `DRAFT — PENDING OWNER RATIFICATION`.
   - Do not infer missing Decisions 11–36 or accept the ratification package as
     approval.
   - Before policy-dependent implementation, obtain a ratified versioned
     policy that confirms or amends A1, B2, U-1, A–F and the relevant
     conversation-derived rules.
   - Resolve the policy items listed in “Unresolved owner-authority decisions”
     below. This is a prerequisite for the affected privileged features, not
     a prerequisite for documenting or testing fail-closed behavior.

2. **Define the trusted decision inputs and policy configuration boundary.**
   - Identify trusted sources for authenticated principal, membership/role,
     tenant/workspace ownership, resource sensitivity, assignments, grants,
     and policy version. Do not accept their effective values from a
     caller-controlled payload.
   - Resolve identity provider/account-linking policy before using identity
     uniqueness. No provider, database, or deployment choice is implied here.
   - Make missing, invalid, stale, or unrecognized trusted facts produce a
     deny at the consuming service boundary.

3. **Correct the pure evaluator for A1, B2, and U-1 after ratification.**
   - Encode an explicit approved base-role/action matrix; A1 by itself does
     not define every role/action pair. Deny unknown combinations.
   - Treat role/action eligibility and assignment/task eligibility as
     necessary read entitlements; a confidentiality-only grant may satisfy
     only the additional confidentiality condition for a confidential read.
   - Ensure a grant never supplies an otherwise missing role, assignment, or
     action permission. Preserve single-action scope and explicit denies for
     deletion, audit, and elevation as appropriate to the ratified matrix.
   - Add focused negative and positive tests before any service relies on the
     corrected kernel.

4. **Implement typed, approved duration policy and lifecycle gates.**
   - Only after U-2/U-3/U-4 approval, represent the relevant fixed maxima and
     assignment default/max as distinct, validated configuration sourced from
     the ratified policy. Do not reuse one generic duration for distinct
     policy classes unless the ratified record explicitly permits it.
   - Add grant and assignment creation, approval, renewal, and revocation
     boundaries only after U-5/U-6 authority requirements are defined.
   - Persist required grant/assignment/renewal audit events before activation;
     fail closed if the approved policy is absent or required audit persistence
     fails.

5. **Integrate authorization at every protected operation boundary.**
   - Use trusted identity and current ownership/policy facts at request
     admission, before queued execution, and immediately before sensitive
     commit, export, or finalization.
   - Revalidate grants, assignments, membership, and resource scope after
     revocation or before execution; honor the recorded safe-stop behavior for
     running work.
   - Keep externally observable failures non-disclosing where resource
     existence is sensitive. Do not report an authorization success unless
     the operation boundary itself enforced the decision.

6. **Build high-stakes review as a separate, auditable workflow.**
   - Do not retrofit `HUMAN_REVIEWED` to imply two independent reviewers.
   - After the full review requirements and canonical identity policy are
     confirmed, implement independent authenticated actors, concealment of
     the first submission from the second reviewer, eligibility checks at
     submission and finalization, explicit abstention, unresolved
     disagreement, and separately authorized third-person adjudication.
   - Persist immutable reviewer/adjudicator events and ensure finalization
     revalidates eligibility and independence.

7. **Close verification and documentation.**
   - Add unit tests for the evaluator and lifecycle; integration tests for
     authenticated service and operation boundaries; regression tests for
     revocation/races and audit failure; then run targeted and full checks.
   - Update the README and policy implementation-status record only after
     verified behavior exists. Keep historical policy evidence and runtime
     enforcement status distinct.

## Fail-closed conditions before capability enablement

| Capability | Must remain disabled or denied until |
|---|---|
| **Any action authorized by a grant** | A1 is formally ratified; the role/action matrix is approved and enforced; grant authority, scope, and independent issuer/approver requirements are resolved; the trusted grant source and required audit are operational. |
| **Confidential-content read grant** | U-1 is formally ratified; U-2 maximum is approved/configured; U-5/U-6 authority is resolved; and enforcement proves base role and active assignment independently permit the read. No assignment-only confidential read. |
| **Administrator elevation** | The separate U-3 maximum is approved/configured; authority and separation requirements are resolved; the elevation-specific workflow, approval, revocation, audit, and operation-boundary revalidation are implemented and verified. Current kernel denial is not a complete service control. |
| **Assignment creation or renewal** | Both U-4 values are approved/configured; assignment authority, lifecycle, revocation, and mandatory renewal audit are implemented; missing policy or audit failure denies activation. |
| **High-stakes approval/finalization** | The applicable review policy is confirmed in a ratified record; authenticated canonical identities and distinct-person enforcement exist; blind second review, eligibility revalidation, abstention, disagreement handling, and distinct authorized adjudication are enforced and tested. |
| **Queued or in-flight protected work** | Trusted ownership and identity are bound to the job; authorization is revalidated before execution and sensitive side effects; revocation has a safe, tested cancel/stop behavior. No queue currently exists in this repository. |

## Unresolved owner-authority decisions

These cannot safely be inferred from code, synthetic fixtures, or the
unratified draft:

1. **Whole-policy ratification:** confirm/amend the owner-selected A1, B2,
   U-1, and other applicable selections, and record the ratifier, date,
   approved version, and amendments. Until then all remain draft selections.
2. **U-1 status:** the current draft records “yes” to a confidentiality-only
   `READ_RESEARCH` grant for a read otherwise permitted by role and
   assignment, but it is pending formal ratification.
3. **Base-role permission matrix:** specify which actions each base role
   permits and whether assignments are required for each action. A1 states
   grants cannot exceed base-role permissions but does not provide the
   complete matrix needed to evaluate every role/action pair.
4. **U-2:** fixed confidential-content grant maximum after security and
   operational assessment. No value is supplied.
5. **U-3:** separate administrator-elevation maximum after assessment. No
   value is supplied.
6. **U-4:** assignment default and maximum after assessment. Neither value is
   supplied.
7. **U-5:** who designates security personnel and the exact grant issuance,
   approval, revocation, and audit authority of that designation.
8. **U-6:** whether issuer and approver must be separately designated
   personnel with distinct operational duties, beyond having distinct
   identities.
9. **U-7:** authoritative evidence and process for canonical identity and
   account linking, including duplicate-account treatment.
10. **Decisions 11–36:** locate and verify the original authoritative record.
    Until then retain `NOT VERIFIABLE AS NUMBERED`; do not fill the gap from
    inference.
11. **High-stakes rule provenance:** the draft records these requirements as
    prior-conversation approvals, but exact original numbering and complete
    approval provenance are unavailable. Confirm the rules in the ratified
    record before treating them as a complete implementation specification.

## Later implementation verification plan

No tests were run for this assessment. In a later implementation milestone,
run tests only after the relevant policy decisions are ratified and code/tests
are changed. At minimum:

```bash
uv run --locked pytest tests/test_authorization.py tests/test_verification.py tests/test_synthesis.py tests/test_workflow.py -q
uv run --locked ruff check .
uv run --locked pytest
```

Add or update tests for the following behaviors:

- **A1 matrix:** for every supported action and base role, matching and
  mismatched grants; a grant cannot turn a base-role denial into an allow;
  unknown roles/actions deny.
- **B2 sensitivity:** an active assignment by itself denies confidential
  `READ_RESEARCH` for researcher/reviewer; public reads continue only where
  the approved role/assignment policy permits.
- **U-1 layering:** missing role permission, missing assignment, wrong-scope,
  inactive, expired, revoked, or over-duration assignment denies even with an
  otherwise valid read grant; only an otherwise permitted confidential read
  can use the grant for confidentiality.
- **No grant privilege transfer:** a `READ_RESEARCH` grant cannot authorize
  write, export, submit-review, deletion, audit, or elevation. A matching
  non-read grant cannot exceed the ratified base-role matrix. Deletion and
  elevation stay denied unless a later ratified policy and separately
  implemented path authorize them.
- **Duration and lifecycle:** missing/unapproved policy, unset maxima,
  invalid policy version, and invalid duration configuration deny. The
  approved grant classes use their own approved maxima; assignment creation
  uses approved default/max; renewal requires approver and complete audit
  fields. Test exact expiry/max boundaries, revocation, and audit failure.
- **Authority and identity:** forged caller payload role/tenant/subject/MFA
  values cannot override trusted adapter facts; issuer, approver, and
  recipient identities are authenticated, distinct as required, designated,
  and authorized. Duplicate accounts do not count as separate reviewers once
  canonical linking rules are approved.
- **High-stakes review:** second reviewer cannot see the first review before
  independent submission; same canonical person or self-review is denied;
  reviewer eligibility is checked at submission and finalization; abstention
  never approves; disagreement remains unresolved until a separately
  authorized third person adjudicates.
- **Operation boundaries:** cross-tenant or stale authorization denies at
  request admission, queue execution, and immediately before side effects;
  a revocation between these points prevents the protected operation or
  causes safe cancellation at the approved boundary.
- **Audit and disclosure:** required events are persisted without document
  text, passage content, secrets, or credentials; audit-read access is
  authorized and itself recorded; failure to write required audit denies the
  protected action; inaccessible and nonexistent resources do not leak
  existence through external responses where that distinction is sensitive.

The seven-day value in current authorization test fixtures is synthetic test
data only; it is not an approved duration. Existing tests for missing
maxima, expiration, revocation, scope, identity-field inequality, and action
separation should be retained where still valid, but their success cannot
substitute for the new policy and integration tests.

## Milestone 13 evaluator update

The pure evaluator and authorization regression tests were updated after this
baseline assessment:

- Grant-backed `WRITE_RESEARCH` and `EXPORT_RESEARCH` now deny because the
  current evaluator has no independent role-only permission path for those
  actions ([authorization.py:341–350](./src/scientia/authorization.py#L341)).
  This is a conservative fail-closed ceiling, not an approved role/action
  matrix; see [the regression test](./tests/test_authorization.py#L331).
- Confidential `READ_RESEARCH` now requires both the existing role/assignment
  authorization path and a valid scoped read grant ([authorization.py:303–339](./src/scientia/authorization.py#L303)).
  Assignment alone and a grant without the base role/assignment path deny;
  see [the allow case](./tests/test_authorization.py#L279),
  [grant-only denial](./tests/test_authorization.py#L265), and
  [assignment-only denial](./tests/test_authorization.py#L308).
- These changes enforce A1/B2/U-1 constraints within the pure evaluator only.
  Policy remains `DRAFT — PENDING OWNER RATIFICATION`; no grant or assignment
  lifecycle, authentication, persistence, audit, API, queue, or operation
  boundary was added.
- After the changes, `uv run --locked pytest tests/test_authorization.py -q`
  reported 66 passed; `uv run --locked pytest` reported 252 passed; and
  `uv run --locked ruff check .` reported all checks passed. These test results
  are not production-security evidence.

## Acceptance criteria

The enforcement program is complete only when all applicable criteria below
are met. Policy-dependent criteria remain blocked until owner authority is
recorded.

1. **Policy provenance:** the approved version, ratifier, date, amendments,
   and traceability are recorded. Decisions 11–36 remain explicitly
   unverified unless the original source is located. No unratified option or
   inferred numeric value is treated as approved.
2. **A1:** every grant-backed allow is also permitted by a ratified
   base-role/action policy; tests prove grants cannot elevate unsupported
   role/action pairs.
3. **B2:** no assignment alone can allow confidential reading; the behavior
   is enforced in evaluator and every real read boundary.
4. **U-1:** a read grant only satisfies confidentiality after role/action and
   assignment checks pass; it cannot supply any missing action, role, or
   assignment permission and cannot transfer to other actions.
5. **Durations:** separate owner-approved grant/elevation maxima and approved
   assignment default/max are sourced from trusted versioned policy; missing
   or invalid values fail closed. No test fixture is promoted to policy.
6. **Grant/assignment lifecycle:** issuer/approver/recipient authority,
   scope, separation, expiry, revocation, renewal, and required audit are
   enforced by trusted lifecycle services; failure to persist mandatory audit
   prevents activation.
7. **Identity:** every protected action uses authenticated principal and
   authoritative active membership/tenant/resource facts; spoofed request
   claims cannot alter them; canonical identity rules prevent duplicate
   accounts being counted as distinct reviewers.
8. **High-stakes review:** two distinct authenticated canonical reviewers
   submit independently; the second cannot see the first beforehand;
   eligibility is revalidated at finalization; abstention is not approval;
   disagreement remains unresolved pending separately authorized third-party
   adjudication. A single `HUMAN_REVIEWED` state is not treated as satisfying
   this criterion.
9. **Operation boundaries:** protected reads, writes, exports, review
   finalization, and queued work revalidate authorization and tenant/resource
   scope at the relevant operation boundaries, including revocation races.
10. **Tests and checks:** focused regression, integration, and full-suite
    tests pass; Ruff passes; the actual commands and results are recorded.
    Synthetic unit tests alone are not production-security evidence.
11. **Safety and disclosure:** required audit is durable and content-free;
    audit reads are recorded; sensitive denials do not disclose protected
    resource existence; unsupported actions remain denied.

## Limitations

This document is an implementation-gap assessment and proposed remediation
sequence. It is **not policy ratification**, a production security
certification, or proof that tests passed. It does not claim that the
conversation-derived decisions are a complete or authoritative Decisions
1–36 record. No tests were run for this documentation-only milestone.
