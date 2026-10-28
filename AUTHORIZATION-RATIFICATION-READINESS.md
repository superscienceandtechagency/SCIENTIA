# SCIENTIA Authorization Policy Ratification Readiness

> **Current policy status: `DRAFT — PENDING OWNER RATIFICATION`.**
>
> This is an owner decision aid, not an approval record, security certification,
> or runtime control. Decisions 11–36 remain **`NOT VERIFIABLE AS NUMBERED`**
> unless their original authoritative record is located and verified.

## 1. Overall status and evidence basis

The [Authorization Policy Decision Register](./AUTHORIZATION-POLICY-DECISION-REGISTER.md)
is the primary index for this package. The [policy draft](./AUTHORIZATION-POLICY-DRAFT.md)
and [ratification package](./AUTHORIZATION-RATIFICATION-PACKAGE.md) record
conversation-derived constraints and owner-selected options, but both say that
formal whole-policy ratification is pending. The pure
[evaluator](./src/scientia/authorization.py) and internal
[authorization facade](./src/scientia/authorization_boundary.py) are
repository evidence of limited in-process behavior only. They do not establish
owner authority, authenticated identity, authoritative policy loading, or
production enforcement.

The requested original Decisions 1–36 source was not found in the inspected
repository Markdown policy/design records or supplied evidence. Those records
refer to missing Decisions 11–36 and conversation-derived summaries for
Decisions 1–10; this search was limited to the project materials inspected for
this package and is not a claim about external archives. No absent wording or
numbering is reconstructed here.

The register lists unresolved decisions and proposed holds. Its checklist
below makes evidence expectations explicit; it does not close a decision.
Evidence must be traceable to an authorized owner and an approved policy
version. A repository implementation, synthetic test, or version label is
not evidence of policy ratification.

## 2. Recorded selections — not ratified

The following are recorded selections or conversation-derived constraints,
not approved production policy. The owner must confirm or amend applicable
items as part of formal ratification.

| Register item | Recorded content | Current status and evidence |
|---|---|---|
| **A1** | A grant can authorize only an action already permitted by the recipient's base role. | Owner-selected, pending formal ratification ([draft §2.A](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-af); [register §2](./AUTHORIZATION-POLICY-DECISION-REGISTER.md#2-recorded-selections-pending-whole-policy-ratification)). |
| **B2** | Assignment alone does not authorize confidential reading; a separate confidential-content grant is required. | Owner-selected, pending formal ratification ([draft §2.B](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-af)). |
| **U-1** | A confidential-content grant may satisfy only the confidentiality condition for `READ_RESEARCH`, and only where role and assignment already permit that action; it adds no action. | Owner-selected 2026-10-14, pending formal ratification ([draft §6](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register); [package recorded selections](./AUTHORIZATION-RATIFICATION-PACKAGE.md#recorded-selections)). |
| **C / U-2 shape** | Confidential-content grants have one fixed maximum duration. | Shape selected; numeric value unresolved ([draft §2.C](./AUTHORIZATION-POLICY-DRAFT.md#c-confidential-content-grant-maximum)). |
| **D / U-3 shape** | Administrator elevation has a separate fixed maximum duration. | Shape selected; numeric value unresolved ([draft §2.D](./AUTHORIZATION-POLICY-DRAFT.md#d-administrator-elevation-maximum)). |
| **E / U-4 shape** | Assignments have one default and one maximum duration; every renewal is audited with requester, approver, scope, reason, and new expiry. | Shapes and renewal fields selected; numeric values unresolved ([draft §2.E](./AUTHORIZATION-POLICY-DRAFT.md#e-research-assignment-duration-and-renewal)). |
| **F2** | Prepare a new owner-ratified, versioned policy record; do not reconstruct missing historical decisions. | Owner-selected approach, pending ratification ([draft §2.F](./AUTHORIZATION-POLICY-DRAFT.md#f-authoritative-policy-record)). |
| **Conversation-derived constraints** | Recorded examples include a replaceable OIDC-compatible identity boundary, MFA requirements for specified roles, audit-access restrictions, deletion/restore constraints, and comparing deployment models before selection. | Historical conversation summaries, not formal ratification or verified historical numbering ([draft §3](./AUTHORIZATION-POLICY-DRAFT.md#3-conversation-derived-approved-rules)). |

## 3. Decision checklist and closure evidence

Implementation stages refer to the [integration plan roadmap](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#9-dependency-ordered-implementation-roadmap):
**1** policy ratification; **2** identity/session; **3** providers and
repositories; **4** authoritative policy loading; **5** operation boundary;
**6** audit and capability lifecycle; **7** independent verification.
Stage completion is not by itself permission to enable an operation.

For policy decisions, acceptable closure evidence is an authoritative,
versioned owner ratification record that identifies the authorized
decision-maker, decision text, rationale, date, affected sections, and any
amendment/supersession. Where a decision also requires an engineering control,
the policy record must be paired with implementation and verification evidence
from the assembled system. The evidence requirements below add specificity;
they do not prescribe policy answers.

### Security and authorization policy

| ID | Exact unresolved question | Why it matters | Evidence needed to close / acceptable evidence | Dependent stages | Safe default while unresolved |
|---|---|---|---|---|---|
| **U-2** | What fixed maximum duration is approved for confidential-content grants? | Bounds grant exposure and must be enforced from authoritative policy, not a test value. | Owner-approved numeric value in the ratified version, with rationale and affected grant rule; separate configuration/enforcement test evidence before grant use. | 1, 4, 6; confidential grant/read. | No grant issue, renewal, or operational reliance. Current evaluator's missing generic maximum denies grant-dependent evaluation but is not a service hold. |
| **U-3** | What separate fixed maximum duration is approved for administrator elevation? | Elevation has a distinct limit; U-2 cannot be substituted. | Owner-approved separate numeric value and rationale in ratified policy; evidence the elevation path consumes that value and fails closed if absent. | 1, 4, 6; elevation. | Keep elevation unavailable; current evaluator denies `ADMIN_ELEVATION`. |
| **U-5** | Who designates and removes security/audit personnel, how is designation represented and reviewed, and what exact grant, revocation, audit-read, audit-administration, and cross-tenant authority does it confer? | Designation and authority cannot be inferred from a role name or supplied actor identifier. | Ratified designation and scope rules naming the authorized designating authority; technical evidence that only verified designated actors can perform the specified operations. | 1, 3, 6; grants, elevation, audit. | No grant lifecycle, elevation, or application audit access based on unverified designation. |
| **U-6** | Beyond distinct issuer, approver, and recipient identities, must issuer and approver be separate designated personnel with separate operational duties or other independence requirements? | Different identifiers do not establish distinct people, duties, or authority. | Ratified explicit separation rule (including an explicit statement if no additional duty separation is required); tests/evidence must verify the chosen requirement against canonical actor records. | 1, 3, 6; grant approval and privileged workflows. | No grant issuance/approval workflow; do not treat identifier inequality as sufficient duty separation. |
| **POL-1** | For every role, action, and resource sensitivity, what is permitted; which actions require assignment; how do multiple roles combine; and how do grants relate to base permissions? | A1 limits grants but does not define a complete permission matrix. Current evaluator behavior is not a substitute for policy. | Ratified, complete role/action/sensitivity matrix including assignment conditions, combination/precedence rules, and explicit deny cases; implementation conformance evidence per action before enablement. | 1, 4–7. | Deny undefined role/action combinations; no capability is enabled from inferred evaluator behavior. |
| **POL-2** | What source and approval evidence make policy authoritative; how is policy integrity checked; who owns and controls signing/verification keys if used; how are versions and supersession ordered; and who may authorize rollback? | Matching version labels do not prove integrity, ratification, freshness, or authorized rollback. | Ratified publication, integrity, key-custody (if applicable), version/supersession, and rollback rules; verifiable policy artifact plus tamper, stale-version, and rollback rejection evidence. No cryptographic method is chosen here. | 1, 4; all policy-dependent actions. | Load no draft/unverified policy as authorization configuration; deny on unavailable, inconsistent, tampered, stale, superseded, or unauthorized rollback state. |
| **A1 / B2 / U-1** | Will the owner confirm or amend the recorded rules that grants cannot add base-role actions, assignments alone do not authorize confidential reading, and U-1 grants satisfy confidentiality only for already role- and assignment-permitted `READ_RESEARCH`? | These recorded selections constrain grants and confidential reads but remain pending formal ratification. | Explicit confirmation or replacement wording in the ratified policy, with affected sections identified; later, evaluator and service-boundary evidence must separately demonstrate conformance. | 1, 4–6; confidential reads and any grant-backed action. | Keep confidential reads and grant-backed protected actions unavailable at application level; evaluator behavior is not a runtime control. |

### Identity and authentication

| ID | Exact unresolved question | Why it matters | Evidence needed to close / acceptable evidence | Dependent stages | Safe default while unresolved |
|---|---|---|---|---|---|
| **AUTH-1** | Which identity provider(s), client types, protocol flows, rollout sequence, and supported populations are authorized, and what migration/fallback behavior is acceptable? | Determines how credentials and identities become trusted and how sessions are operated. | Owner-authorized identity/session decision in the versioned policy/authority record, including supported flows and failure/fallback behavior; later provider configuration and integration tests against the selected contract. The recorded replaceable OIDC-compatible boundary does not select a provider. | 1–3, 5, 7; all authenticated operations. | No production authentication or protected routes; do not trust caller-supplied identity claims. |
| **AUTH-2** | What MFA assurance evidence is required, how is it bound to a session, when is step-up or refresh required, and how does rollout apply by role/population? | The evaluator accepts a boolean; it does not verify assurance or freshness. | Ratified assurance, session-binding, freshness/step-up and rollout rules; later tests prove claims are adapter-verified and stale/unavailable MFA evidence denies. | 1–2, 5, 7; roles/actions requiring MFA. | Do not treat a caller-supplied or unverified MFA boolean/claim as proof; deny paths requiring unverifiable MFA. |
| **U-7** | What authoritative evidence and process link accounts to a canonical person, resolve duplicates/merges/disablement, and establish distinct people where independence is required? | Subject/account identifiers do not prove canonical identity or distinct humans. | Ratified canonical identity and account-linking process with duplicate-account handling and authoritative evidence rules; later integration evidence that aliases cannot count as independent reviewers. | 1–3, 5–7; independent review and other separation checks. | Do not rely on account IDs as proof of distinct people; keep high-stakes independence/finalization unavailable. |

### Review, adjudication, and classification authority

| ID | Exact unresolved question | Why it matters | Evidence needed to close / acceptable evidence | Dependent stages | Safe default while unresolved |
|---|---|---|---|---|---|
| **POL-3** | Which roles and eligibility rules govern first/second reviewers, blind independent submission, abstention, disagreement, third-person adjudication, and finalization; who may propose and confirm high-stakes classification; and what establishes reviewer independence? | Determines validity and independence of high-stakes decisions; provenance and complete historical numbering are unavailable. | Explicit owner-ratified review/classification rules, including authority and eligibility, in the approved version; later workflow tests/evidence for blind second submission, canonical distinct people, abstention, adjudication, and finalization revalidation. | 1–2, 5, 7; high-stakes review and classification. | Keep high-stakes review/finalization and classification changes unavailable; conversation summaries and synthetic workflow states are not approval evidence. |

### Audit, retention, deletion, and recovery

| ID | Exact unresolved question | Why it matters | Evidence needed to close / acceptable evidence | Dependent stages | Safe default while unresolved |
|---|---|---|---|---|---|
| **AUD-1** | Which roles may read, search, export, administer, or delete audit metadata and at what scope; what retention and backup-expiry rules apply; what integrity/availability controls are required; and how are audit reads recorded? | Audit data is sensitive, while retention and expiry decisions can affect preservation and accountability. | Ratified access, scope, retention, backup-expiry, integrity, and audit-read rules; later evidence of restricted durable storage, access controls, content/secret exclusion, read auditing, and failure behavior. No retention value is assumed. | 1, 5–7; audit store, query, export, lifecycle. | Keep application audit access/storage unavailable; do not claim durable audit controls exist. |
| **LEG-1** | When legal hold, authorized deletion, retention, backup expiration, restore, and preservation duties conflict, what is their precedence; who may place/release a hold; and how are deletion records reapplied on restore? | The draft records deletion/restore constraints but not a complete hold, purge, and retention precedence rule. | Owner-approved precedence and authority in ratified policy with affected deletion/restore sections; later verified behavior across purge, backup expiry, restore, and deletion-record replay. No legal conclusion is supplied here. | 1, 5–7; deletion, purge, hold, backup, restore. | No deletion, purge, restore, or backup-expiry workflow; do not destroy held or otherwise protected data on an inferred rule. |
| **REC-1** | What recovery objectives, backup protections, restore authority/testing, key recovery, deletion-record replay, and operator approvals are required? | Recovery could reintroduce deleted content or restore inconsistent policy/audit state. | Ratified recovery authority and requirements; reviewed recovery/restore tests demonstrating deletion and policy/audit state consistency. These questions are not recorded selections in the draft. | 1, 3–7; persistence, backup, restore, deletion. | No production persistence/recovery workflow; do not restore protected operations without verified authoritative state. |

### Deployment and operational authority

| ID | Exact unresolved question | Why it matters | Evidence needed to close / acceptable evidence | Dependent stages | Safe default while unresolved |
|---|---|---|---|---|---|
| **DEP-1** | After comparing managed cloud and client-controlled/self-hosted options, which deployment model is authorized; where may data reside; which operators may access systems/data; who controls keys and emergency access; and what support/isolation rules apply? | Deployment, jurisdiction, operator access, and key custody change the trust and data-protection boundaries. | Documented comparison and explicit authorized deployment/region/operator/key-control decision in the approved governance record; later target-environment access and configuration review. No model or region is selected here. | 1, 3–4, 6–7; any production deployment or managed operations. | No deployment or production operations; do not infer region, operator authority, or key custody. |

### Ratification and historical record

| ID | Exact unresolved question | Why it matters | Evidence needed to close / acceptable evidence | Dependent stages | Safe default while unresolved |
|---|---|---|---|---|---|
| **RAT-1** | Who is authorized to ratify; what is the ratification date and approved version; what amendments are approved; and how are later amendments proposed, authorized, versioned, and superseded? | Without an authoritative approval and change record, draft selections cannot be treated as policy. | Approved versioned policy record containing authorized ratifier identity/basis, date, exact approved text/sections, rationale, version, and amendment/supersession process. No identity or date is prefilled. | 1; all policy-sensitive stages. | Preserve `DRAFT — PENDING OWNER RATIFICATION`; no draft is loaded as approved policy. |
| **HIST-1 / U-8** | Can the original authoritative Decisions 1–36 record be located and verified, including exact text, numbering, version, approval provenance, and supersession; if not, what replacement policy text will be explicitly ratified? | Missing historical wording must not be reconstructed or silently renumbered. | Original authoritative record with provenance and version for historical verification; or an explicit owner-ratified replacement that identifies affected scope and preserves the limitation. The inspected project materials did not contain the original record. | 1; every policy requirement dependent on missing history. | Keep Decisions 11–36 `NOT VERIFIABLE AS NUMBERED`; do not reconstruct or implement from inferred text. |

### Decision-specific source references

| ID(s) | Source references |
|---|---|
| **U-2** | [Draft §2.C](./AUTHORIZATION-POLICY-DRAFT.md#c-confidential-content-grant-maximum), [draft §6](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register), [`maximum_grant_duration`](./src/scientia/authorization.py#L232), [`_validate_grant`](./src/scientia/authorization.py#L413). |
| **U-3** | [Draft §2.D](./AUTHORIZATION-POLICY-DRAFT.md#d-administrator-elevation-maximum), [draft §6](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register), [`authorize` elevation denial](./src/scientia/authorization.py#L300). |
| **U-4** | [Draft §2.E](./AUTHORIZATION-POLICY-DRAFT.md#e-research-assignment-duration-and-renewal), [draft §6](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register), [`maximum_assignment_duration`](./src/scientia/authorization.py#L231), [`_validate_assignment`](./src/scientia/authorization.py#L378). |
| **AUTH-1** | [Draft identity rule](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-110), [replaceable OIDC-compatible adapter design](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#41-replaceable-oidc-compatible-adapter), [integration-plan identity lifecycle](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#7-identity-and-session-lifecycle). |
| **AUTH-2** | [Draft identity/MFA rule](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-110), [`Principal.mfa_verified`](./src/scientia/authorization.py#L73), [MFA boundary design](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#42-mfa), [readiness inventory](./AUTHORIZATION-IMPLEMENTATION-READINESS.md#5-unresolved-policy-and-owner-authority-inventory). |
| **U-5** | [Draft §2.A](./AUTHORIZATION-POLICY-DRAFT.md#a-grant-recipient-eligibility-and-authority), [draft U-5](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register), [ratification-package workflow](./AUTHORIZATION-RATIFICATION-PACKAGE.md#owner-decision-workflow), [readiness-audit blockers](./AUTHORIZATION-INTEGRATION-READINESS-AUDIT.md#5-owner-authority-blockers). |
| **U-6** | [Draft §2.A](./AUTHORIZATION-POLICY-DRAFT.md#a-grant-recipient-eligibility-and-authority), [draft U-6](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register), [ratification-package workflow](./AUTHORIZATION-RATIFICATION-PACKAGE.md#owner-decision-workflow), [evaluator actor-conflict check](./src/scientia/authorization.py#L401). |
| **U-7** | [Draft §3.2](./AUTHORIZATION-POLICY-DRAFT.md#32-additional-approved-rules-with-unverified-historical-numbering), [draft U-7](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register), [ratification-package workflow](./AUTHORIZATION-RATIFICATION-PACKAGE.md#owner-decision-workflow), [`Principal`](./src/scientia/authorization.py#L73). |
| **POL-1** | [Draft unresolved-policy register](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register), [implementation-readiness inventory](./AUTHORIZATION-IMPLEMENTATION-READINESS.md#5-unresolved-policy-and-owner-authority-inventory), [integration-plan current state](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#1-current-state), [`authorize`](./src/scientia/authorization.py#L254). |
| **POL-2** | [Draft §2.F](./AUTHORIZATION-POLICY-DRAFT.md#f-authoritative-policy-record), [provider-integrity risks](./TRUSTED-PROVIDER-AND-POLICY-INTEGRITY-ASSESSMENT.md#3-risk-assessment), [integration-plan policy integrity](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#4-policy-integrity), [`PolicyVersion`](./src/scientia/authorization_boundary.py#L61). |
| **A1 / B2 / U-1** | [Draft §2](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-af), [draft U-1](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register), [ratification package](./AUTHORIZATION-RATIFICATION-PACKAGE.md#recorded-selections), [evaluator read logic](./src/scientia/authorization.py#L303), [Milestone 13 evaluator update](./AUTHORIZATION-ENFORCEMENT-GAP-ASSESSMENT.md#milestone-13-evaluator-update). |
| **POL-3** | [Draft §3.1](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-110), [draft §3.2](./AUTHORIZATION-POLICY-DRAFT.md#32-additional-approved-rules-with-unverified-historical-numbering), [implementation-readiness inventory](./AUTHORIZATION-IMPLEMENTATION-READINESS.md#5-unresolved-policy-and-owner-authority-inventory), [boundary-design verification plan](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#11-verification-plan-and-acceptance-criteria). |
| **AUD-1** | [Draft audit rule](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-110), [integration-plan audit boundaries](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#8-audit-boundaries), [readiness-audit blockers](./AUTHORIZATION-INTEGRATION-READINESS-AUDIT.md#5-owner-authority-blockers). |
| **LEG-1 / REC-1** | [Draft deletion/restore rule](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-110), [boundary-design consistency and revocation](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#7-transactional-consistency-replay-revocation-and-jobs), [integration-plan unresolved decisions](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#11-explicit-non-goals-and-unresolved-decisions). |
| **DEP-1** | [Draft deployment-comparison rule](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-110), [boundary-design scope](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#1-purpose-and-design-principles), [integration-plan non-goals](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#11-explicit-non-goals-and-unresolved-decisions), [readiness-audit blockers](./AUTHORIZATION-INTEGRATION-READINESS-AUDIT.md#5-owner-authority-blockers). |
| **RAT-1** | [Draft authority](./AUTHORIZATION-POLICY-DRAFT.md#1-purpose-and-authority), [draft ratification checklist](./AUTHORIZATION-POLICY-DRAFT.md#8-owner-ratification-checklist), [ratification-package status](./AUTHORIZATION-RATIFICATION-PACKAGE.md#status), [decision register §5](./AUTHORIZATION-POLICY-DECISION-REGISTER.md#5-ratification-and-change-record-procedure). |
| **HIST-1 / U-8** | [Draft decision history](./AUTHORIZATION-POLICY-DRAFT.md#7-decision-history-and-record-integrity), [ratification-package historical limitation](./AUTHORIZATION-RATIFICATION-PACKAGE.md#historical-evidence-limitation), [decision register §6](./AUTHORIZATION-POLICY-DECISION-REGISTER.md#6-historical-decision-limitation). |

## 4. Protected-operation holds

These are readiness requirements, not controls enforced by this document.
The current evaluator is a pure in-process function and the facade is an
internal seam; the inspected application has no route or protected service
wired to enforce these holds ([register §4](./AUTHORIZATION-POLICY-DECISION-REGISTER.md#4-dependency-and-hold-matrix);
[readiness audit §5](./AUTHORIZATION-INTEGRATION-READINESS-AUDIT.md#5-owner-authority-blockers)).

Until the relevant owner decisions are ratified **and** the corresponding
technical gates are implemented and independently verified, keep unavailable:

- production authentication and all authenticated protected routes;
- public or confidential protected reads, especially confidential-content
  access;
- writes, exports, deletion, purge, restore, classification changes, and
  review submissions/finalization;
- grant or assignment issue, approval, renewal, revocation, or reliance;
- administrator elevation, audit queries, and queued protected work.

No protected production operation is ready merely because a decision is
recorded, a source-level evaluator denies a case, or tests pass. Required
upstream conditions include verified authentication and identity provenance,
authoritative policy integrity/version handling, trusted tenant/resource
resolution, service-level enforcement with operation-boundary revalidation,
capability-specific ratification, durable restricted audit where required, and
independent verification. See the [integration readiness audit](./AUTHORIZATION-INTEGRATION-READINESS-AUDIT.md#6-security-critical-dependency-graph)
and [integration plan service gates](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#5-service-enforcement-and-unavailable-operations).

Before any protected path is enabled, engineering evidence must also
demonstrate tenant scoping at each data, file, derived-artifact, cache, job,
and audit boundary; authorization revalidation before later disclosure or
side effects; and that membership, assignment, grant, or policy changes stop
subsequent reads, commits, exports, and queued work. Cross-tenant and
revocation-race cases require end-to-end verification. These are engineering
gates, not additional owner decisions or controls supplied by this document
([integration plan §6](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#6-tenant-isolation);
[boundary design §7](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#7-transactional-consistency-replay-revocation-and-jobs)).

## 5. Decision-register traceability matrix

Every item in the current decision register maps below to a checklist entry.
Selection labels A1/B2/C/D/E/F2 appear in the recorded-selection checklist;
unresolved IDs map to the corresponding decision section above. U-8 and HIST-1
refer to the same historical-record issue, not separate policy decisions.

| Decision-register item | Readiness checklist entry |
|---|---|
| **A1** | [Recorded selections](#2-recorded-selections-not-ratified); [security and authorization policy](#security-and-authorization-policy) |
| **B2** | [Recorded selections](#2-recorded-selections-not-ratified); [security and authorization policy](#security-and-authorization-policy) |
| **U-1** | [Recorded selections](#2-recorded-selections-not-ratified); [security and authorization policy](#security-and-authorization-policy) |
| **Confidential-content grant maximum shape (C / U-2); U-2** | [Recorded selections](#2-recorded-selections-not-ratified); [security and authorization policy](#security-and-authorization-policy) |
| **Administrator-elevation maximum shape (D / U-3); U-3** | [Recorded selections](#2-recorded-selections-not-ratified); [security and authorization policy](#security-and-authorization-policy) |
| **Assignment duration shape and renewal audit (E / U-4); U-4** | [Recorded selections](#2-recorded-selections-not-ratified); [security and authorization policy](#security-and-authorization-policy) |
| **F2** | [Recorded selections](#2-recorded-selections-not-ratified); [ratification and historical record](#ratification-and-historical-record) |
| **Conversation-derived constraints** | [Recorded selections](#2-recorded-selections-not-ratified); applicable category checklists under [identity](#identity-and-authentication), [review authority](#review-adjudication-and-classification-authority), [audit/deletion](#audit-retention-deletion-and-recovery), and [deployment](#deployment-and-operational-authority) |
| **RAT-1** | [Ratification and historical record](#ratification-and-historical-record) |
| **AUTH-1** | [Identity and authentication](#identity-and-authentication) |
| **AUTH-2** | [Identity and authentication](#identity-and-authentication) |
| **U-5** | [Security and authorization policy](#security-and-authorization-policy) |
| **U-6** | [Security and authorization policy](#security-and-authorization-policy) |
| **U-7** | [Identity and authentication](#identity-and-authentication) |
| **POL-1** | [Security and authorization policy](#security-and-authorization-policy) |
| **POL-2** | [Security and authorization policy](#security-and-authorization-policy) |
| **POL-3** | [Review, adjudication, and classification authority](#review-adjudication-and-classification-authority) |
| **AUD-1** | [Audit, retention, deletion, and recovery](#audit-retention-deletion-and-recovery) |
| **LEG-1** | [Audit, retention, deletion, and recovery](#audit-retention-deletion-and-recovery) |
| **DEP-1** | [Deployment and operational authority](#deployment-and-operational-authority) |
| **REC-1** | [Audit, retention, deletion, and recovery](#audit-retention-deletion-and-recovery) |
| **HIST-1 / U-8** | [Ratification and historical record](#ratification-and-historical-record) |

## 6. Evidence closure protocol

For each decision, maintain an evidence record with:

1. Stable decision ID and exact question answered.
2. Explicit decision text, scope, rationale, affected policy section, and
   effective conditions; unresolved subparts remain marked unresolved.
3. Authorized decision-maker and evidence of that authority, date, approved
   policy version, and amendment/supersession relationship.
4. Source artifact and provenance. For Decisions 11–36, include the original
   authoritative record only if actually located and verified; otherwise
   retain `NOT VERIFIABLE AS NUMBERED`.
5. Separate engineering evidence where applicable: implementation location,
   configured policy source, integration/operation-boundary test evidence,
   failure behavior, and independent review. Engineering evidence does not
   substitute for owner ratification.

The package is ready to support owner review; the decisions are not thereby
closed. Until an authoritative record demonstrates otherwise, preserve
**`DRAFT — PENDING OWNER RATIFICATION`** and all applicable holds.

## 7. Milestone 26 audit note

The independent cross-check against the current decision register confirmed
that each listed register item maps to the checklist and traceability matrix.
This audit makes tenant-scoping and revocation-race verification explicit in
the protected-operation prerequisites, following the integration plan and
boundary design. These remain future engineering requirements: their design
documentation does not establish implementation. Recorded selections remain
pending formal ratification, and Decisions 11–36 remain
`NOT VERIFIABLE AS NUMBERED`.
