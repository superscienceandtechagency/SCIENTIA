# SCIENTIA Authorization Policy Decision Register

> **Policy status: `DRAFT — PENDING OWNER RATIFICATION`.**
>
> This register organizes owner-authority questions for review. It does not
> approve, interpret, or substitute for policy. Engineering implementation,
> evaluator behavior, and passing tests do not constitute policy ratification.
> Decisions 11–36 remain **`NOT VERIFIABLE AS NUMBERED`** unless the original
> authoritative record is actually located and verified.

## 1. Authority, scope, and status vocabulary

The [policy draft](./AUTHORIZATION-POLICY-DRAFT.md#1-purpose-and-authority)
is non-authoritative. The [ratification package](./AUTHORIZATION-RATIFICATION-PACKAGE.md#status)
is for owner review only. It records selected options and unresolved
questions, but changes neither policy status nor runtime behavior.

This register uses these descriptions:

- **Owner-selected, pending formal ratification:** the draft records a
  selection made by the owner in conversation; it is not approved policy.
- **Conversation-derived, approval provenance incomplete:** a rule is
  recorded as previously approved in available conversation context, but its
  original numbered record or complete approval provenance is unavailable.
- **Unresolved:** no answer is recorded, or the recorded material does not
  specify the complete decision needed.
- **Not verifiable:** the evidence does not establish the decision's original
  wording, numbering, authority, or complete scope.

Where this register notes a “recorded selection,” it preserves what the
inspected documents say; it does not independently establish identity,
consent, or approval beyond those records. No missing option, value, authority,
or historical wording is inferred. The prescribed safe default for each
unresolved item is a fail-closed hold; this register does not impose a runtime
control.

## 2. Recorded selections — pending whole-policy ratification

These are current recorded selections, not final approvals:

| Selection | Recorded content | Status/evidence |
|---|---|---|
| **A1** | A grant may authorize only actions already permitted by the recipient's base role. | Owner-selected, pending formal ratification ([draft §2.A](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-af); [package](./AUTHORIZATION-RATIFICATION-PACKAGE.md#recorded-selections)). |
| **B2** | A research or review assignment alone does not authorize reading confidential content; a separate confidential-content grant is required. | Owner-selected, pending formal ratification ([draft §2.B](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-af)). |
| **U-1** | Yes: a separate confidential-content grant may satisfy the confidentiality condition for `READ_RESEARCH` only when the recipient's base role and assignment already permit that action. It must not add an action. | Owner-selected on 2026-10-14, pending formal ratification ([draft §6](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register); [package](./AUTHORIZATION-RATIFICATION-PACKAGE.md#recorded-selections)). |
| **Confidential-content grant maximum shape** | One fixed maximum duration. No numeric maximum is recorded. | Owner-selected duration shape; value unresolved ([draft §2.C](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-af)). |
| **Administrator-elevation maximum shape** | A separate fixed maximum duration, distinct from the confidential-content grant maximum. No numeric maximum is recorded. | Owner-selected duration shape; value unresolved ([draft §2.D](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-af)). |
| **Assignment duration shape and renewal audit** | One default and one maximum duration; every renewal requires an audit record identifying requester, approver, scope, reason, and new expiry. No numeric values are recorded. | Owner-selected shapes and audit fields; values unresolved ([draft §2.E](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-af)). |
| **F2 — authoritative record approach** | Prepare a new owner-ratified, versioned policy record; preserve Decisions 11–36 as unverifiable unless the original is found and verified. | Owner-selected approach, pending ratification; missing historical record not reconstructed ([draft §2.F](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-af)). |

The draft also records prior-conversation rules in §3, including an
OIDC-compatible replaceable identity boundary, MFA for administrators,
reviewers and high-stakes approvers (with MFA preferred for all users where
feasible), audit access restrictions, immediate access denial after an
authorized deletion request, controlled purge, reapplication of deletion
records after backup restoration, and comparison of deployment models before
selection. These are conversation-derived evidence summaries with incomplete
historical numbering/provenance, not formal ratification
([draft §3](./AUTHORIZATION-POLICY-DRAFT.md#3-conversation-derived-approved-rules)).

## 3. Unresolved owner-authority decision register

Implementation stage names below refer to the dependency order in the
[integration plan](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#9-dependency-ordered-implementation-roadmap):
Stage 1 policy ratification; Stage 2 identity/session; Stage 3 providers and
repositories; Stage 4 authoritative policy loading; Stage 5 operation
boundary; Stage 6 audit and lifecycle; Stage 7 independent verification.
“Blocked” means that the dependent capability remains disabled or denied; it
does not prevent unrelated safe documentation or non-exposing work.

| ID | Owner decision / exact question | Why it matters | Recorded options or selection (not approval) | Evidence | Dependent stages / capability | Safe default while unresolved |
|---|---|---|---|---|---|---|
| **RAT-1 — Whole-policy ratification metadata** | Who is the authorized ratifier; what is the ratification date and approved version; what exact amendments are approved; and how are later amendments proposed, authorized, versioned, and superseded? | Without an authoritative complete policy and approval chain, draft selections cannot be treated as binding configuration or implementation authority. | The draft checklist requests ratifier, date, approved version, and corrections. No ratifier, date, approved version, or amendment procedure is recorded ([draft §8](./AUTHORIZATION-POLICY-DRAFT.md#8-owner-ratification-checklist)). | [Draft authority](./AUTHORIZATION-POLICY-DRAFT.md#1-purpose-and-authority); [package status](./AUTHORIZATION-RATIFICATION-PACKAGE.md#status). | Stage 1; all policy-sensitive stages and protected capabilities. | Preserve `DRAFT — PENDING OWNER RATIFICATION`; load no draft as approved policy and enable no policy-sensitive operation. |
| **U-2 — Confidential-content grant maximum** | What is the approved fixed maximum duration for confidential-content grants? | The maximum bounds exposure from a grant. The current evaluator's generic grant maximum is not a grant-type-specific approved value. | One fixed maximum selected; no numeric value supplied ([draft §2.C](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-af)). | [Draft U-2](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register); evaluator default is `None`, and absent maximum denies grant-dependent decisions ([`AuthorizationPolicy.maximum_grant_duration`](./src/scientia/authorization.py#L232), [`_validate_grant`](./src/scientia/authorization.py#L413)). | Stages 1, 4, 6; confidential-grant issuance, renewal, and reliance; confidential reads. | Do not issue, renew, configure, or operationally rely on confidential grants. Missing maximum denies grant-dependent evaluator decisions. |
| **U-3 — Administrator-elevation maximum** | What is the approved fixed maximum duration for administrator elevation, separate from U-2? | Elevation has a distinct risk and the draft expressly selects a separate bound; reusing or inventing U-2 would contradict the recorded shape. | Separate fixed maximum selected; no numeric value supplied ([draft §2.D](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-af)). | [Draft U-3](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register); evaluator denies `ADMIN_ELEVATION` ([`authorize`](./src/scientia/authorization.py#L300)). | Stages 1, 4, 6; administrator-elevation workflow. | Keep elevation unavailable and denied; do not substitute U-2 or a test fixture. |
| **U-4 — Assignment default and maximum** | What are the approved default duration and maximum duration for research assignments? | Both are needed to create bounded assignments and enforce the ceiling; the evaluator has a generic maximum only and no default/renewal service. | One default plus one maximum selected; both values unresolved; renewals recorded as requiring audit fields ([draft §2.E](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-af)). | [Draft U-4](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register); [`AuthorizationPolicy.maximum_assignment_duration`](./src/scientia/authorization.py#L231); [`_validate_assignment`](./src/scientia/authorization.py#L378). | Stages 1, 4, 6; assignment creation, renewal, and assignment-dependent actions. | Do not create or renew assignments. With no configured maximum, assignment-dependent evaluator decisions deny. |
| **AUTH-1 — Identity provider and rollout** | Which identity provider(s), client types, protocol flows, rollout sequence, and supported populations are authorized, and what migration/fallback behavior is acceptable? | The provider and rollout determine credential validation, identity provenance, session lifecycle, availability, and operational responsibility. | A replaceable OIDC-compatible boundary is recorded in conversation-derived rules; managed provider or provider implementation is not selected ([draft rule 8](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-110)). | [Draft identity/MFA rule](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-110); [design adapter section](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#41-replaceable-oidc-compatible-adapter); no adapter exists in the inspected source. | Stages 1–3; every authenticated protected operation. | No production authentication or protected route. Do not select a provider or accept caller-supplied identity claims. |
| **AUTH-2 — MFA assurance and rollout detail** | What evidence/assurance satisfies MFA, how is it bound to a session, when is step-up required or refreshed, and how should rollout to all users be handled? | The evaluator accepts a boolean, not verified MFA evidence; assurance and freshness cannot safely be inferred from that value. | Conversation-derived rule: require MFA for administrators, reviewers, and high-stakes approvers; prefer MFA for all users where feasible. Assurance protocol, freshness, step-up and rollout details are unspecified ([draft rule 8](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-110)). | [`Principal.mfa_verified`](./src/scientia/authorization.py#L73); [design MFA section](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#42-mfa); [readiness inventory](./AUTHORIZATION-IMPLEMENTATION-READINESS.md#5-unresolved-policy-and-owner-authority-inventory). | Stages 1–2; protected actions requiring MFA; independent review. | Do not treat caller-provided or unverified MFA booleans/claims as proof. Deny a protected path whenever its required MFA state cannot be verified. |
| **U-5 — Security/audit personnel designation and authority** | Who designates and removes security/audit personnel; how is designation represented and reviewed; what exact issue, approval, revocation, audit-read, audit-administration, and cross-tenant authority may each designation exercise? | A role label or caller-supplied actor ID does not establish authority. Audit and grant powers can affect multiple tenants and sensitive records. | Recorded: only designated security personnel may issue or approve grants; revocation of confidential-content and elevation grants is controlled by designated security personnel; audit metadata access is restricted to explicitly designated security/audit personnel. The designating authority and full scope are unresolved ([draft §2.A](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-af); [draft §3](./AUTHORIZATION-POLICY-DRAFT.md#3-conversation-derived-approved-rules)). | [Draft U-5](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register); [package U-5](./AUTHORIZATION-RATIFICATION-PACKAGE.md#owner-decision-workflow); evaluator checks issuer/approver identifier conflicts but not their authority ([`_validate_grant`](./src/scientia/authorization.py#L403)). | Stages 1, 3, 6; grants, elevation, audit queries/administration. | No grant lifecycle, elevation, or audit query. Never infer designated status from role name or supplied ID. |
| **U-6 — Separation of duties** | Beyond the recorded requirement that issuer, approver, and recipient be distinct identities, must issuer and approver be separate designated personnel, hold separate operational duties, or satisfy further independence conditions? | Distinct identifiers do not prove distinct people, independent duties, or authority. | Recorded selection requires three distinct identities. Additional issuer/approver duty separation remains open ([draft §2.A](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-af); [draft U-6](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register)). | [Package U-6](./AUTHORIZATION-RATIFICATION-PACKAGE.md#owner-decision-workflow); evaluator's issuer/approver/recipient identifier-conflict check ([`_validate_grant`](./src/scientia/authorization.py#L403)). | Stages 1, 3, 6; grant approval and other multi-person privileged workflows. | No grant issuance/approval workflow; do not count distinct identifiers as proof of independent duties or distinct humans. |
| **U-7 — Canonical identity verification/account linking** | What authoritative evidence and process link external accounts to a canonical person, resolve duplicates/merges/disablement, and establish two genuinely distinct people for independent review? | The evaluator compares subject strings; that cannot establish identity uniqueness or independent reviewers. | Recorded conversation-derived constraint: duplicate accounts must not count as separate reviewers. Evidence/process and duplicate handling remain unresolved ([draft §3.2](./AUTHORIZATION-POLICY-DRAFT.md#32-additional-approved-rules-with-unverified-historical-numbering); [draft U-7](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register)). | [Package U-7](./AUTHORIZATION-RATIFICATION-PACKAGE.md#owner-decision-workflow); [design identity section](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#4-trusted-principal-and-authentication-boundary); [`Principal.subject_id`](./src/scientia/authorization.py#L74). | Stages 1–3, 5–7; high-stakes review, grant separation, canonical identity claims. | Do not rely on account IDs or reviewer labels to establish distinct people; keep high-stakes approval/finalization unavailable. |
| **POL-1 — Complete base-role/action and assignment matrix** | For every role/action/resource sensitivity, what is permitted, what assignment is required, how do multiple roles combine, and what is the precedence of grants versus base permissions? | A1 limits grants but does not define which actions a role permits; evaluator behavior is a limited conservative implementation, not a complete policy. | A1/B2 and U-1 are recorded selections; a complete matrix and action-specific assignment requirements are identified as unresolved ([draft §§2, 6](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register)). | [Readiness inventory](./AUTHORIZATION-IMPLEMENTATION-READINESS.md#5-unresolved-policy-and-owner-authority-inventory); [implementation plan](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#1-current-state); [`authorize`](./src/scientia/authorization.py#L254). | Stages 1, 4–7; any operation whose permission is not already explicit and ratified. | Deny undefined role/action combinations; do not generalize current evaluator paths into a complete permission matrix. |
| **POL-3 — High-stakes review, adjudication, and classification authority** | Which roles and eligibility rules govern the first and second reviewers, blind independent submission, abstention, disagreement, third-person adjudication, and finalization; who may propose and confirm high-stakes classification, and what evidence/process establishes the required independence? | These rules determine whether a high-stakes decision is independent, valid, and authorized; distinct account identifiers alone do not establish distinct people or authority. | Conversation-derived rules record two distinct authenticated reviewers, an independently submitted second review before seeing the first, abstention not being approval, unresolved disagreement pending separately authorized third-person adjudication, and research-lead proposal with authorized high-stakes-approver confirmation. They remain pending whole-policy ratification and their complete historical provenance is unavailable ([draft §3.1](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-110); [draft §3.2](./AUTHORIZATION-POLICY-DRAFT.md#32-additional-approved-rules-with-unverified-historical-numbering)). | [Readiness owner-authority inventory](./AUTHORIZATION-IMPLEMENTATION-READINESS.md#5-unresolved-policy-and-owner-authority-inventory); [readiness audit blockers](./AUTHORIZATION-INTEGRATION-READINESS-AUDIT.md#5-owner-authority-blockers); [design verification plan](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#11-verification-plan-and-acceptance-criteria). | Stages 1, 2, 5, 7; high-stakes review, adjudication, classification changes, and finalization. | Keep high-stakes review/finalization and classification changes unavailable; do not treat synthetic workflow state or distinct account IDs as proof of independent, authorized decisions. |
| **POL-2 — Authoritative policy integrity, signing, keys, versioning, rollback** | What publication source and approval evidence make a policy authoritative; whether/how content is signed or otherwise integrity-checked; who owns/rotates/revokes verification keys; how versions/supersession are ordered; who may authorize rollback and under what record? | A matching version string cannot prove content integrity, ratification, freshness, or authorized rollback. | F2 selects a new ratified versioned record; no signing scheme, key owner, publication authority, supersession rule, or rollback authority is selected ([draft §2.F](./AUTHORIZATION-POLICY-DRAFT.md#2-owner-selected-decisions-af); [provider assessment](./TRUSTED-PROVIDER-AND-POLICY-INTEGRITY-ASSESSMENT.md#3-risk-assessment)). | [`PolicyVersion`](./src/scientia/authorization_boundary.py#L61); [policy integrity assessment](./TRUSTED-PROVIDER-AND-POLICY-INTEGRITY-ASSESSMENT.md#3-risk-assessment); [integration plan §4](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#4-policy-integrity). | Stages 1, 4; all policy-dependent evaluations. | Load no unratified/unverifiable policy as authorization configuration. Deny on missing, mismatched, tampered, stale, superseded, or unauthorized rollback state. |
| **AUD-1 — Audit access, retention, backup expiry** | Which roles may read, search, export, administer, or delete audit metadata, at what scope; what retention and backup-expiry rules apply; what access is itself audited; and how are integrity and availability requirements met? | Audit metadata can expose sensitive operational information; indefinite retention or premature deletion may both violate obligations. No retention value can be inferred. | Recorded: restrict audit metadata to explicitly designated security/audit personnel, audit audit-reads, exclude document text/secrets. Audit authority, access, retention, integrity, and jurisdiction remain unresolved in the source documents; backup-expiry rules are an additional follow-up question not separately itemized there ([draft rule 9](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-110); [integration plan §8](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#8-audit-boundaries); [readiness audit blockers](./AUTHORIZATION-INTEGRATION-READINESS-AUDIT.md#5-owner-authority-blockers)). | [Draft unresolved items](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register); [integration audit boundaries](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#8-audit-boundaries); [readiness blockers](./AUTHORIZATION-INTEGRATION-READINESS-AUDIT.md#5-owner-authority-blockers). | Stages 1, 5–7; audit storage, query, export, retention and backup lifecycle. | Keep application audit query/store unavailable. Do not invent retention/backup-expiry values; preserve content/secret exclusion and deny unverified audit access. |
| **LEG-1 — Legal hold versus deletion/purge/backup expiry** | When legal hold, authorized deletion, retention, backup expiration, restore, and applicable preservation duties conflict, what is the precedence, who may place/release a hold, and how are deletion tombstones applied on restore? | The draft records immediate access denial and controlled purge with deletion records reapplied after restore, but does not specify legal-hold precedence or purge/backup timelines. | Conversation-derived deletion/restore behavior is recorded; legal-hold precedence is explicitly unresolved in the integration plan, while hold authority, purge timing, and retention details are not specified ([draft rule 6](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-110); [integration plan §11](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#11-explicit-non-goals-and-unresolved-decisions)). | [Integration plan unresolved decisions](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#11-explicit-non-goals-and-unresolved-decisions); [readiness audit blockers](./AUTHORIZATION-INTEGRATION-READINESS-AUDIT.md#5-owner-authority-blockers). | Stages 1, 5–7; deletion, purge, backup, restore, audit/legal hold. | No deletion, purge, restore, or backup expiry workflow. Keep access denied after an authorized deletion request if/when implemented; do not destroy held data or invent precedence. |
| **DEP-1 — Deployment model, data region, operator access, key control** | After the recorded comparison, which deployment model is authorized; where may data reside; which operators may access systems/data; who controls encryption/signing keys and emergency access; what isolation and support access rules apply? | Deployment and operator choices affect data jurisdiction, threat boundaries, key custody, tenant isolation, and operational access. | The draft records comparing managed cloud and client-controlled/self-hosted deployment before selection. The reviewed documents do not record a selected model or specific region/operator-access decision; these are follow-up scope questions, not recorded options. Policy-signing key ownership is separately unresolved ([draft rule 10](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-110); [integration plan §11](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#11-explicit-non-goals-and-unresolved-decisions)). | [Design scope](./TRUSTED-AUTHORIZATION-BOUNDARY-DESIGN.md#1-purpose-and-design-principles); [integration plan unresolved decisions](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#11-explicit-non-goals-and-unresolved-decisions); [readiness audit blockers](./AUTHORIZATION-INTEGRATION-READINESS-AUDIT.md#5-owner-authority-blockers). | Stages 1, 3, 4, 6–7; any production deployment or managed operational access. | No deployment. Do not select a region, model, operator access, or key-control policy on the owner's behalf. |
| **REC-1 — Recovery, backup restore, disaster recovery** | What recovery objectives, backup protection, restore authority/testing, key recovery, deletion-record replay, and operator approvals are required? | Recovery can reintroduce deleted content or lose policy/audit integrity if state and tombstones are not restored consistently. | The draft records that deletion records must be reapplied after backup restoration. It does not specify recovery objectives, authority, backup expiry, or key recovery; these additional recovery questions are not recorded selections ([draft rule 6](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-110); [integration plan §11](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#11-explicit-non-goals-and-unresolved-decisions)). | [Draft deletion/restore rule](./AUTHORIZATION-POLICY-DRAFT.md#31-recoverable-numbered-rules-110); [integration plan unresolved decisions](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#11-explicit-non-goals-and-unresolved-decisions). | Stages 1, 3–7; persistence, backups, policy/audit restoration, deletion. | No production persistence or recovery workflow; do not restore protected operations without verified deletion and policy state. |
| **HIST-1 / U-8 — Original Decisions 1–36 or approved replacement** | Can the original authoritative Decisions 1–36 record be located and verified, including exact wording, numbering, version, approver, provenance, and supersession; if not, what replacement text is explicitly adopted in a new ratified policy? | Missing rules must not be reconstructed from conversation summaries or duplicated draft language; approval provenance and supersession affect interpretation. | F2 records a new versioned record approach; Decisions 11–36 remain `NOT VERIFIABLE AS NUMBERED` unless the original is found. No substitute text is authorized by this register ([draft §§2.F, 7](./AUTHORIZATION-POLICY-DRAFT.md#7-decision-history-and-record-integrity)). | [Historical limitation](./AUTHORIZATION-RATIFICATION-PACKAGE.md#historical-evidence-limitation); [readiness history](./AUTHORIZATION-IMPLEMENTATION-READINESS.md#5-unresolved-policy-and-owner-authority-inventory); [audit blockers](./AUTHORIZATION-INTEGRATION-READINESS-AUDIT.md#5-owner-authority-blockers). | Stage 1; all requirements dependent on potentially missing rules. | Preserve `NOT VERIFIABLE AS NUMBERED`; do not reconstruct or renumber. If unavailable, proceed only through explicit ratification of a replacement policy that makes its provenance and scope clear. |

### Completeness note

The inspected documents explicitly identify U-1 through U-8, whole-policy
ratification, the base-role/action matrix, high-stakes authority, MFA detail,
audit governance, policy publication authority, authentication transport,
and deployment choice. This register also separates broader governance and
engineering-scope questions (such as signing/key custody, retention/backup
expiry, legal-hold precedence, region/operator access, and recovery) into
stable tracking IDs. Where source documents do not itemize those subquestions,
the register labels them as follow-up questions rather than recorded
selections. These IDs are organizational labels, not recovered historical
decision numbers.

## 4. Dependency and hold matrix

| Capability or stage | Decisions/prerequisites that must be resolved | Hold while unresolved |
|---|---|---|
| Any policy-sensitive implementation | RAT-1, applicable A1/B2/U-1 selections, POL-1, HIST-1, and applicable policy publication evidence. | Draft remains non-authoritative; undefined permissions deny. |
| Authentication and verified principal | AUTH-1, AUTH-2, canonical identity rules in U-7, and a verified provider contract. | Do not expose authenticated protected routes or trust caller identity/role/MFA claims. |
| Tenant/resource lookup and provider wiring | Verified principal, U-7 where person identity matters, DEP-1 data/operator boundaries, trusted provider construction. | Selectors are untrusted; no protected content fetch based solely on IDs. |
| Policy loader and evaluator configuration | RAT-1, POL-2, HIST-1, complete role/action rules in POL-1. | No draft policy or version label as authorization policy; deny if integrity/version/rollback cannot be verified. |
| Confidential grant/read | Formal ratification of U-1, U-2, U-5, U-6, AUTH-1/AUTH-2, POL-1/POL-2, and trusted operation enforcement. | No grant issuance, renewal, reliance, or application confidential read. |
| Assignment creation/renewal/action | U-4, RAT-1/POL-1, verified identity and membership, lifecycle audit requirements in AUD-1. | No assignment creation or renewal; assignment-based evaluator path denies absent configured maximum. |
| Elevation | U-3, U-5, U-6, AUTH-2, POL-2, audit and service revalidation. | `ADMIN_ELEVATION` remains denied; no elevation workflow. |
| Audit store/query | U-5, AUD-1, LEG-1, DEP-1, REC-1 and ratified audit rules. | No audit application access or durable audit claims; never expose content/secrets. |
| Deletion, purge, backup, restore | LEG-1, REC-1, DEP-1, authorized deletion/recovery authority, audited operation boundary. | No deletion/purge/restore workflow; do not invent retention or legal-hold precedence. |
| High-stakes review/classification | U-7, POL-1, POL-3, RAT-1/HIST-1, AUTH-1/AUTH-2, U-5/U-6 as applicable. | No claims of independent reviewers or authorized finalization; keep high-stakes decisions and classification changes unavailable. |
| Exports and queued work | POL-1, relevant A1/role rules, U-2/U-4/U-5/U-6 as applicable, AUD-1, verified identity/policy and service-level revalidation. | No export or queued protected operation. |
| Production deployment/enablement | DEP-1, REC-1, AUD-1, POL-2, all applicable ratifications, integrated tests and independent review. | No deployment or protected production capability. |

These are prescribed policy and architecture holds, not runtime enforcement.
The current `authorize` function is a pure in-process evaluator, and the
`AuthorizationBoundary` is an internal seam; the inspected application has
no route or protected service wired to them ([draft §5](./AUTHORIZATION-POLICY-DRAFT.md#5-policy-requirements-vs-current-implementation-enforcement);
[`authorize`](./src/scientia/authorization.py#L254);
[`AuthorizationBoundary`](./src/scientia/authorization_boundary.py#L159)).
The boundary evaluates with the kernel's default duration policy
([boundary implementation](./src/scientia/authorization_boundary.py#L165)); matching
policy-version labels do not establish policy integrity or ratification
([boundary implementation](./src/scientia/authorization_boundary.py#L124)).

Unavailable or inconsistent identity, policy, clock/time, membership, resource,
grant/assignment, audit, or provider facts must fail closed. A denial from the
current pure evaluator does not itself enforce a hold in an absent service;
the [integration readiness audit](./AUTHORIZATION-INTEGRATION-READINESS-AUDIT.md#6-security-critical-dependency-graph)
and [boundary integration plan](./AUTHORIZATION-BOUNDARY-INTEGRATION-PLAN.md#5-service-enforcement-and-unavailable-operations)
describe the required future controls.

## 5. Ratification and change-record procedure

No decision in this register is approved. A future authoritative decision
record should contain, for each decision or policy section:

1. **Stable decision ID** and the exact policy section(s) affected.
2. **Decision text:** explicit answer, scope, exceptions, and effective
   conditions; unresolved parts must remain explicitly open.
3. **Options considered**, if any, and the selected option or a clear
   statement that no option was selected. Do not infer a choice from
   implementation behavior.
4. **Rationale** and relevant security, operational, legal, and evidence
   basis.
5. **Authorized decision-maker:** ratifier/approver identity and the basis
   for authority. This field must not be populated by this register.
6. **Decision date**, approved policy version, and effective date if distinct.
7. **Amendment/supersession record:** previous version, changed text, reason,
   approval identity/date, and traceable relation to affected decisions.
8. **Evidence provenance:** source artifact and any verification of the
   original historical record. If unverifiable, say so; do not reconstruct
   wording or numbering.
9. **Implementation disposition:** capabilities blocked or enabled only
   after matching engineering controls and verification evidence exist.

The complete policy should be ratified as one versioned record or through an
explicitly authorized amendment process. Until then, preserve
**`DRAFT — PENDING OWNER RATIFICATION`** and keep applicable operations
disabled or denied.

## 6. Historical decision limitation

The available draft identifies Decisions 1–10 as recoverable only from
conversation-derived summaries, not verified from a repository policy file.
Decisions 11–36 remain **`NOT VERIFIABLE AS NUMBERED`** because the original
text, numbering, provenance, and supersession history have not been verified
([draft §7](./AUTHORIZATION-POLICY-DRAFT.md#7-decision-history-and-record-integrity);
[ratification package](./AUTHORIZATION-RATIFICATION-PACKAGE.md#historical-evidence-limitation)).

This register does not recover, reconstruct, renumber, or replace those
decisions. The `HIST-1` identifier is a local tracking ID only, not a
historical decision number. If the original source is unavailable, only an
explicitly owner-ratified replacement record can establish policy text; this
register itself is not that replacement.

## 7. Audit findings and correction record

The cross-document audit found that high-stakes review, adjudication, and
classification authority had been subsumed under the general role/action
matrix instead of being separately traceable. It is now identified as
**POL-3**, with its conversation-derived constraints, ratification status,
dependencies, and hold stated explicitly. Legal-hold, deployment, and
recovery entries now distinguish source-recorded constraints from expanded
follow-up questions rather than presenting those subquestions as prior
selections. No owner decision or historical wording was resolved by this
correction.
