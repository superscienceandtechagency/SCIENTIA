# SCIENTIA Authorization Policy

> **DRAFT — PENDING OWNER RATIFICATION**

| Field | Value |
|---|---|
| Version | `0.1.0-draft` |
| Draft date | 2026-10-14 |
| Status | Non-authoritative draft for owner review |
| Ratification | Pending |

This draft records policy decisions available in the conversation history and
the owner's subsequent selections A–F. It is not approved policy and does not
authorize implementation of policy-sensitive functionality. No missing
historical decision text or numbering has been reconstructed.

## 1. Purpose and authority

This document is prepared under the owner's selection of option F2: prepare a
new owner-ratified, versioned policy record while keeping Decisions 11–36
marked `NOT VERIFIABLE AS NUMBERED` unless the original authoritative record
is found.

The rules below have different evidence status:

- **Conversation-derived approved rules** were explicitly approved in prior
  conversation context. They are not currently recorded in a repository policy
  file and are not thereby made authoritative by this draft.
- **Owner-selected draft decisions** are the A–F options selected for inclusion
  in this draft. The selections are recorded, but the policy document itself
  remains pending owner ratification.
- **Repository-verified facts** describe current code and documentation, not
  policy approval.
- **Unresolved items** remain open; no implementation may assume a value or
  interpretation for them.

Only an explicit owner ratification should change this document's status.
Ratification should identify the ratifier and date and establish the approved
version. Until then, treat it as a review artifact only.

## 2. Owner-selected decisions A–F

These options were selected by the owner in conversation on 2026-10-14. They
are reproduced as draft policy pending ratification.

### A. Grant recipient eligibility and authority

1. **A1 selected:** A grant may authorize only actions already permitted by
   the recipient's base role.
2. Only designated security personnel may issue or approve grants.
3. The issuer, approver, and recipient must be three distinct identities.

The selection does not define how security personnel are designated, whether
issuer and approver must hold separate sub-roles, or how base-role eligibility
is evaluated for confidentiality-specific permission. U-1 records the owner's
selected clarification for confidential reads, pending formal ratification.

### B. Confidential resources and assignments

**B2 selected:** A research or review assignment alone does not authorize
reading confidential content. A separate confidential-content grant is
required.

U-1 records the owner's selected clarification for how B2 and A1 interact on
confidential reads, pending formal ratification. It does not collapse task
assignment and confidential-content permission into one concept.

### C. Confidential-content grant maximum

Confidential-content grants will use **one fixed maximum duration**. The
numeric maximum is pending formal security and operational assessment and
owner approval. No value is approved by this draft.

### D. Administrator-elevation maximum

Administrator elevation will have a **separate fixed maximum duration**,
distinct from the confidential-content grant maximum. The numeric maximum is
pending formal security and operational assessment and owner approval. No
value is approved by this draft.

### E. Research-assignment duration and renewal

Research assignments will use **one default duration plus one maximum
duration**. Both numeric values are pending formal security and operational
assessment and owner approval.

Every assignment renewal requires an audit record identifying the requester,
approver, scope, reason, and new expiry.

### F. Authoritative policy record

**F2 selected:** Prepare a new owner-ratified, versioned policy record.
Decisions 11–36 remain `NOT VERIFIABLE AS NUMBERED` unless the original
authoritative record is located and verified.

This draft does not recreate missing decision text, numbering, dates, approval
provenance, or supersession history.

## 3. Conversation-derived approved rules

The following rules were explicitly approved in the available conversation
record. They are listed here as historical conversation-derived rules, not as
repository-verified policy and not as a substitute for the unavailable full
numbered source.

### 3.1 Recoverable numbered rules 1–10

1. **Tenant-scoped documents:** Public documents remain
   tenant/workspace-scoped.
2. **Administrator content access:** Organization administrators have
   restricted default content access. Elevated confidential access requires
   explicit permission, a reason, and audit records. Later approved
   conversation rules further require a different authorized grantor, explicit
   scope, nonblank reason, independent approval, mandatory expiry, and
   prohibit self-grants.
3. **High-stakes review:** High-stakes findings require two distinct
   authenticated reviewers. The second reviewer submits independently before
   seeing the first review. Disagreement remains unresolved pending separately
   authorized third-person adjudication. Abstention is not approval.
4. **High-stakes classification:** A research lead proposes classification
   and an authorized high-stakes approver confirms it. Reasons, identities,
   timestamps, and changes are recorded.
5. **Exports:** Exports follow existing role/resource permissions.
   Confidential-content exports by administrators require a separate reasoned
   and audited grant.
6. **Deletion and restore:** An authorized deletion request immediately denies
   access, followed by controlled purge. Backup restoration reapplies deletion
   records.
7. **PDF processing:** PDF limits are established from representative workload
   and deployment-capacity testing; parsing is isolated and bounded.
8. **Identity and MFA:** Use a replaceable OIDC-compatible identity boundary.
   Require MFA for administrators, reviewers, and high-stakes approvers;
   prefer MFA for all users where feasible.
9. **Audit metadata:** Audit metadata access is restricted to explicitly
   designated security/audit personnel; audit reads are themselves audited;
   audit events exclude document text and secrets. The later, explicit
   conversation clarification is the wording retained here. The historical
   repository does not contain a record documenting its numbering or
   supersession.
10. **Deployment selection:** Compare managed cloud and client-controlled /
    self-hosted options using documented criteria before selecting a deployment
    model.

These numbers are only the recoverable numbered decisions in the available
conversation summary. They do not validate a complete historical Decisions
1–36 record.

### 3.2 Additional approved rules with unverified historical numbering

The following were explicitly stated as approved in later conversation
context, but their original decision numbers and complete approval history are
not available:

- Reviewers see assigned research by default. Broader access requires separate
  explicit, scoped permission.
- Research leads have read-only default visibility for non-confidential
  research in their workspace. Other actions require separate permission.
- Research leads manage routine assignments and revocations. Designated
  security personnel control revocation of confidential-content and
  administrator-elevation grants.
- Users may hold multiple roles, but each action is authorized independently.
  Self-review is prohibited. High-stakes review independence and distinct
  identities must be enforced.
- Canonical identity mapping must prevent duplicate accounts from counting as
  separate reviewers.
- Assignment revocation blocks new access and submissions, cancels queued
  review tasks, and prevents revoked authorization from starting new protected
  operations. Running jobs stop at a safe boundary.
- A review submitted while its reviewer was eligible remains historically
  valid, but finalization revalidates high-stakes reviewer independence and
  eligibility.
- Before queued job execution and at sensitive operation boundaries, revalidate
  membership, resource ownership, and authorization. Revoked access stops or
  safely cancels affected work.
- Confidential-content grants and administrator elevation require independent
  approval, explicit scope, reason, audit records, and mandatory expiry.
  Issuance remains disabled until required maximum durations are formally
  approved.
- Research assignments require explicit expiry. Assignment creation remains
  disabled until the default and maximum durations are approved.

Do not assign these additional rules historical numbers without locating and
verifying their original numbered source.

## 4. Repository-verified implementation facts

The current [README](./README.md) describes the authorization module as a pure
policy function. [authorization.py](./src/scientia/authorization.py) accepts
caller-supplied principal, membership, resource, assignment, grant, action,
evaluation time, and optional duration-policy facts. It does not authenticate
identity, verify MFA, validate grantor authority, or prove that identities
represent distinct people.

The evaluator defaults to denial for unknown/unsupported actions and
scope/context failures. It requires configured maximum durations for
assignment- or grant-based decisions. The module does not implement grant or
assignment management workflows, API routes, persistence, audit storage,
queues, or production tenant isolation. Its tests use synthetic inputs.

These facts describe implementation only. They do not establish that the
system is production-secure or that the conversation-derived rules have been
fully encoded.

## 5. Policy Requirements vs Current Implementation Enforcement

The owner-selected A1, B2, and U-1 rules remain pending formal ratification.
Current source implements conservative versions of these constraints in the
pure evaluator only; this does not make the draft authoritative, establish a
complete approved role/action policy, or enforce any application operation.
The evaluator is not wired to application routes or protected services.

- **A1 — Base-role grant eligibility.** The current evaluator denies
  grant-backed `WRITE_RESEARCH` and `EXPORT_RESEARCH`; it has no independent
  role-only allow path for these actions
  ([`authorization.py`](./src/scientia/authorization.py#L341);
  [regression test](./tests/test_authorization.py#L331)). This is a
  conservative evaluator ceiling, not a ratified base-role/action matrix.
- **B2 — Confidential-resource access.** The current evaluator denies a
  confidential `READ_RESEARCH` when only an assignment is present. A
  separate valid read grant is required in addition to the applicable
  role/assignment path
  ([`authorize`](./src/scientia/authorization.py#L303);
  [assignment-only denial test](./tests/test_authorization.py#L308)).
- **U-1 — Confidentiality-only grant.** The current evaluator denies a read
  grant that lacks the underlying role/assignment eligibility; an eligible
  confidential read uses the grant only to satisfy the confidentiality
  condition ([grant-only denial test](./tests/test_authorization.py#L265);
  [layered allow test](./tests/test_authorization.py#L279)). The selected
  clarification remains pending formal ratification.
- **Historical baseline.** Before the Milestone 13 evaluator update, the
  evaluator allowed grant-backed write/export, assignment-only confidential
  reading, and grant-only reading. Those are historical findings, not
  current evaluator behavior; see the
  [enforcement-gap assessment](./AUTHORIZATION-ENFORCEMENT-GAP-ASSESSMENT.md#milestone-13-evaluator-update).
- **Fail-closed hold and enforcement boundary.** Section 6 records policy
  holds; this draft cannot block an application operation. The evaluator's
  current denials are in-process decision behavior only. No application
  route or protected service invokes it, and there is no authentication or
  trusted fact-acquisition boundary. Do not treat evaluator behavior or this
  documentation as production enforcement.
- **Test evidence.** The cited tests demonstrate synthetic evaluator inputs
  and outputs. They do not establish trusted identity, ratified policy,
  provider provenance, service-level enforcement, or production security.

## 6. Unresolved-policy register

The following must be resolved before the corresponding functionality is
enabled.

| ID | Unresolved question / value | Required disposition |
|---|---|---|
| U-1 | **OWNER-SELECTED — PENDING FORMAL RATIFICATION.** Yes: a separate confidential-content grant may satisfy the confidentiality condition for `READ_RESEARCH` only when the recipient's base role and assignment already permit that action. It must not add any action beyond the recipient's base-role permissions, and cannot authorize write, export, deletion, audit access, or administrator elevation. | Owner selected this clarification on 2026-10-14. It remains pending formal ratification with the complete policy. |
| U-2 | What is the fixed maximum duration for confidential-content grants? | Formal security and operational assessment, followed by explicit owner approval of the value. |
| U-3 | What is the separate fixed maximum duration for administrator elevation? | Formal security and operational assessment, followed by explicit owner approval of the value. |
| U-4 | What are the research-assignment default and maximum durations? | Formal security and operational assessment, followed by explicit owner approval of both values. |
| U-5 | How are designated security personnel designated, and what authority may they exercise? | Define the designation authority and scope. The recorded choice limits grant issuing/approval to designated security personnel but does not define the designation process or role model. |
| U-6 | Must grant issuer and approver be separate designated security personnel with distinct operational duties, beyond the requirement that issuer, approver, and recipient be distinct identities? | Clarify the exact separation-of-duties rule before grant workflow design. |
| U-7 | What identity-linking evidence and process establish canonical identity across accounts? | Define before relying on identity uniqueness for independent high-stakes reviews. |
| U-8 | What complete, authoritative Decisions 1–36 record, including version, approval provenance, and supersession history, can be verified? | Locate the original record if available. Until verified, Decisions 11–36 remain `NOT VERIFIABLE AS NUMBERED`. |

### Policy fail-closed hold (not a runtime control)

The following are policy requirements for future implementation and operation.
This draft does not enforce them: it does not disable current evaluator
behavior or block an application service. See Section 5 for the evaluator's
specific current limitations against A1 and B2.

- Do not issue, approve, renew, or operationally rely on confidential-content
  grants until U-1 is formally ratified, U-2, U-5, and U-6 are resolved, and
  the approved maximum is configured.
- Do not issue, approve, renew, or operationally rely on administrator-
  elevation grants until U-1 is formally ratified, U-3, U-5, and U-6 are
  resolved, and the separate approved maximum is configured.
- Do not create or renew research assignments until the default and maximum
  in U-4 are approved and enforced.
- The current pure evaluator denies confidential reads based on assignment
  alone and denies a grant-only read without the underlying role/assignment
  path (Section 5). Do not treat this evaluator behavior as application
  authorization; confidential-content use remains on hold until the policy is
  formally ratified and trusted service-level enforcement is implemented.
- Do not treat absent duration configuration as unlimited.
- Do not infer that a grant adds a role permission.
- Do not rely on identity uniqueness for independent high-stakes review until
  U-7 is resolved and enforced.
- Continue to deny undefined permissions. Do not implement policy-sensitive
  behavior based on unverified historical rules from Decisions 11–36.

## 7. Decision history and record integrity

| Item | Record status |
|---|---|
| Decisions 1–10 | Recoverable as numbered from conversation-derived summaries; not verified from a repository policy file. |
| Decisions 11–36 | `NOT VERIFIABLE AS NUMBERED`; exact source text, original numbering, provenance, and supersession history are unavailable in the inspected repository/context. |
| A–F selections | Owner-selected options recorded in conversation on 2026-10-14 and transcribed in Section 2; policy-document ratification remains pending. |
| Numeric grant/elevation/assignment duration values | Pending formal assessment and explicit approval; no numeric limits are supplied here. |
| U-1 A1/B2 clarification | Owner-selected on 2026-10-14: confidentiality-only grant for an otherwise permitted `READ_RESEARCH`; pending formal ratification. |
| This document | Version `0.1.0-draft`, dated 2026-10-14; non-authoritative until owner ratification. |

No missing historical wording, number, approval event, date, or supersession has
been reconstructed. A later ratified version should record its approver, date,
version change, and a traceable rationale for changes.

## 8. Owner ratification checklist

Before ratifying this draft, the owner should:

- [ ] Confirm or amend decisions A1, B2, C fixed maximum, D separate fixed
  maximum, E one default plus maximum with every renewal audited, and F2.
- [ ] Confirm or amend the U-1 confidentiality-only grant decision as part of
  full policy ratification.
- [ ] Approve the confidential-content grant maximum after formal assessment.
- [ ] Approve the separate administrator-elevation maximum after formal
  assessment.
- [ ] Approve the assignment default and maximum durations after formal
  assessment.
- [ ] Define the designation authority and operating scope for security
  personnel and confirm grant issuer/approver separation of duties.
- [ ] Define how canonical identities are established and linked before
  high-stakes independent-review enforcement is relied upon.
- [ ] Confirm whether the original Decisions 1–36 record can be located; if
  not, expressly retain Decisions 11–36 as `NOT VERIFIABLE AS NUMBERED`.
- [ ] Record the ratifier, ratification date, approved version, and any
  corrections to this draft.

**Ratification status: PENDING.** This draft alone authorizes no
policy-sensitive implementation.
