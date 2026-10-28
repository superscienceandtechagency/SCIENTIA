# SCIENTIA Authorization Ratification Package

## Status

**Policy status: `DRAFT — PENDING OWNER RATIFICATION`.**

This package is for owner review only. It does not ratify policy, change the
status of [AUTHORIZATION-POLICY-DRAFT.md](./AUTHORIZATION-POLICY-DRAFT.md), or
authorize policy-sensitive implementation. The current draft remains
version `0.1.0-draft`, dated 2026-10-14, and non-authoritative until the owner
ratifies a versioned record.

This package summarizes recorded selections and unresolved decisions; it
supplies no numeric duration values and does not reconstruct absent policy
text.

## Recorded selections

The following are recorded as owner-selected draft options, not approved
policy. Formal ratification of the complete policy remains pending.

- **A1 — Grant eligibility:** A grant may authorize only actions already
  permitted by the recipient's base role.
- **B2 — Confidential resources:** An assignment alone does not authorize
  reading confidential content; a separate confidential-content grant is
  required.
- **Confidential-content grant duration:** One fixed maximum; its numeric
  value remains unapproved.
- **Administrator-elevation duration:** A separate fixed maximum, distinct
  from the confidential-content grant maximum; its numeric value remains
  unapproved.
- **Research-assignment duration:** One default and one maximum; both values
  remain unapproved.
- **Assignment renewals:** Every renewal requires an audit record identifying
  requester, approver, scope, reason, and new expiry.
- **F2 — Authoritative policy record:** Prepare a new owner-ratified,
  versioned record. Decisions 11–36 remain `NOT VERIFIABLE AS NUMBERED`
  unless the original authoritative record is located and verified.
- **U-1 — Confidentiality-only grant:** A separate confidential-content
  grant may satisfy the confidentiality condition for `READ_RESEARCH` only
  when the recipient's base role and assignment already permit that action.
  It must not add an action and cannot authorize write, export, deletion,
  audit access, or administrator elevation. This clarification was selected
  on 2026-10-14 and remains pending formal ratification.

The draft records A1 and B2 in Section 2 of
[AUTHORIZATION-POLICY-DRAFT.md](./AUTHORIZATION-POLICY-DRAFT.md)
and U-1 in
[Section 6](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register).
U-1's current recorded answer is **yes** to the confidentiality-only grant
question above; its status is not formal approval.

## Owner decision workflow

For each item, the owner should provide only the input requested below. The
evidence and blocking conditions are included to support review, not to
recommend or preselect a policy answer.

| Item | Evidence and current status | What the decision blocks | Exact owner input needed |
|---|---|---|---|
| **U-1 — Confidentiality-only grant** | The draft records the owner-selected clarification, pending ratification ([draft §6](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register)). Current evaluator source requires the underlying role/assignment path before a confidential read grant can satisfy confidentiality ([`authorize`](./src/scientia/authorization.py#L303)); synthetic tests cover [grant-only denial](./tests/test_authorization.py#L265), [assignment-only denial](./tests/test_authorization.py#L308), and [layered allow](./tests/test_authorization.py#L279). | Confidential-content grants and reads remain unavailable for application use until formal ratification, U-2/U-5/U-6 resolution, and trusted service-level enforcement. The evaluator denial is not an application control. | Confirm or amend the recorded rule as part of whole-policy ratification: may this grant satisfy confidentiality only for an otherwise role- and assignment-permitted `READ_RESEARCH`, without adding any action? |
| **U-2 — Confidential-content grant maximum** | The draft selects one fixed maximum but records no value (draft §§2.C and 6 in [AUTHORIZATION-POLICY-DRAFT.md](./AUTHORIZATION-POLICY-DRAFT.md)). The evaluator has only a generic `maximum_grant_duration`; an absent value denies grant-dependent decisions ([authorization.py:224–232, 401–405](./src/scientia/authorization.py#L224)). | Confidential-content grant issuance, approval, renewal, and operational reliance remain on hold until an assessed value is approved and enforced. | Provide the approved fixed maximum after formal security and operational assessment. |
| **U-3 — Administrator-elevation maximum** | The draft requires a separate fixed maximum and records no value (draft §§2.D and 6 in [AUTHORIZATION-POLICY-DRAFT.md](./AUTHORIZATION-POLICY-DRAFT.md)). The evaluator has no separate elevation maximum; `ADMIN_ELEVATION` is currently denied ([authorization.py:300](./src/scientia/authorization.py#L300)). | Administrator-elevation grants and any elevation workflow remain disabled. | Provide the approved separate fixed maximum after formal security and operational assessment. Do not assume it equals U-2. |
| **U-4 — Assignment default and maximum** | The draft requires both values and audited renewals but approves neither (draft §§2.E and 6 in [AUTHORIZATION-POLICY-DRAFT.md](./AUTHORIZATION-POLICY-DRAFT.md)). The evaluator accepts only a generic optional maximum and has no default-duration or renewal workflow ([authorization.py:224–232, 344–372](./src/scientia/authorization.py#L344)). | Assignment creation and renewal remain disabled until both values and their enforcement are approved. | Provide the default and maximum durations after assessment, and confirm that every renewal must record requester, approver, scope, reason, and new expiry. |
| **U-5 — Security-personnel designation and authority** | The draft restricts grant issue/approval to designated security personnel but leaves designation authority, role model, and scope open (draft §§2.A and 6 in [AUTHORIZATION-POLICY-DRAFT.md](./AUTHORIZATION-POLICY-DRAFT.md)). `AccessGrant` contains caller-supplied issuer and approver identifiers; the evaluator does not verify their authority ([authorization.py:155–185, 375–405](./src/scientia/authorization.py#L155)). | Grant issue, approval, and revocation must not rely on unverified caller-supplied designation or authority claims. | Specify who designates security personnel, how designation is represented, and the scope of their grant and revocation authority. |
| **U-6 — Issuer/approver separation** | The draft requires issuer, approver, and recipient to be distinct identities, but leaves open whether the issuer and approver need separate designated roles or duties (draft §§2.A and 6 in [AUTHORIZATION-POLICY-DRAFT.md](./AUTHORIZATION-POLICY-DRAFT.md)). Code checks identifier inequality only ([authorization.py:389–395](./src/scientia/authorization.py#L389)); a synthetic test covers the distinct-issuer/approver check ([test_authorization.py](./tests/test_authorization.py#L782)). | Grant workflows remain disabled until the required separation rule and its enforceable authority checks are settled. | Decide whether issuer and approver must be separately designated security personnel with distinct operational duties; if so, state those duties. |
| **U-7 — Canonical identity/account linking** | The draft records a prior-conversation requirement that duplicate accounts must not count as separate high-stakes reviewers, but the linking evidence and process are unresolved ([draft §3.2 and §6](./AUTHORIZATION-POLICY-DRAFT.md#3-conversation-derived-approved-rules)). `Principal` accepts a subject identifier, and the evaluator does not authenticate identities or establish distinct humans ([authorization.py:73–85, 254–263](./src/scientia/authorization.py#L254)); the README states account linking is not verified ([README.md §Pure authorization kernel](./README.md#pure-authorization-kernel)). | Do not rely on account identifiers alone to establish independent reviewers or distinct people. | Define the authoritative evidence and process for linking accounts to canonical identities, including how duplicate accounts are treated. |
| **U-8 — Original numbered policy record** | The draft says Decisions 11–36 are `NOT VERIFIABLE AS NUMBERED` because the source text, numbering, provenance, and supersession history are unavailable ([draft §§2.F, 7](./AUTHORIZATION-POLICY-DRAFT.md#7-decision-history-and-record-integrity)). The retained checkpoint likewise records that gap ([checkpoint 005](../../.copilot/session-state/ad3d50ed-bfd7-4a03-9879-1d3ac90766fa/checkpoints/005-authorization-policy-draft-rev.md)). | Do not reconstruct missing wording or numbering, or implement policy-sensitive behavior based on unverified Decisions 11–36. Undefined permissions remain denied. | Locate and verify the original authoritative record, if available. If it cannot be found, explicitly retain the `NOT VERIFIABLE AS NUMBERED` status in the ratified record. |
| **Whole-policy ratification metadata** | The draft is non-authoritative and its Section 8 checklist requests ratifier, date, approved version, and corrections ([draft §§1, 8](./AUTHORIZATION-POLICY-DRAFT.md#8-owner-ratification-checklist)). | No policy selection in the draft becomes approved by this package; policy-sensitive implementation remains unauthorized by the draft alone. | Ratify or amend the complete policy and record the ratifier, ratification date, approved version, and amendments/corrections. |

## Historical evidence limitation

Decisions 11–36 remain **`NOT VERIFIABLE AS NUMBERED`** unless the original
authoritative record is found and verified. The draft identifies Decisions
1–10 as recoverable only from conversation-derived summaries, not from a
repository policy record. Neither this package nor the retained authorization
checkpoints reconstruct missing text, numbering, approval provenance, dates,
or supersession history.

The draft's statements about additional prior-conversation approvals are
historical evidence summaries, not repository-verified policy. See
[AUTHORIZATION-POLICY-DRAFT.md, Sections 3 and 7](./AUTHORIZATION-POLICY-DRAFT.md#3-conversation-derived-approved-rules)
and the retained [authorization policy checkpoint](../../.copilot/session-state/ad3d50ed-bfd7-4a03-9879-1d3ac90766fa/checkpoints/005-authorization-policy-draft-rev.md).

## Implementation gaps and evidence boundaries

**Milestone 13 update:** The evaluator-level A1/B2/U-1 gaps described below
were subsequently addressed within the pure evaluator. The original bullets
are a baseline snapshot from this package's review and must not be read as
current evaluator behavior. Confidential grants, action grants, assignments,
and high-stakes review remain subject to the policy and service-boundary holds
below; this change did not ratify the draft or add application enforcement.
Current behavior is visible in [`authorize`](./src/scientia/authorization.py#L303),
with regression cases for [valid layered confidential reading](./tests/test_authorization.py#L279),
[read-grant-only denial](./tests/test_authorization.py#L265), and
[grant-backed write/export denial](./tests/test_authorization.py#L331).

The current evaluator is a deterministic function over caller-supplied facts,
not an authentication or application service. Its code and tests do not
establish production security.

- **A1 baseline finding (pre-Milestone 13):** the grant branches allowed
  write/export without a base-role check. The current evaluator denies these
  grant-backed actions because no independent role-only allow path is defined.
- **B2 baseline finding (pre-Milestone 13):** an assignment could authorize a
  confidential read without a grant. The current evaluator requires both the
  existing role/assignment path and a valid read grant for confidential reads.
- **U-1 baseline finding (pre-Milestone 13):** a read grant could bypass
  role/assignment eligibility. The current evaluator validates role and
  assignment eligibility before the grant can satisfy confidential reading.
- The baseline behavior and remediation status are detailed in the
  [authorization enforcement gap assessment](./AUTHORIZATION-ENFORCEMENT-GAP-ASSESSMENT.md).
- **Other service controls are absent.** The evaluator does not authenticate
  identity, verify MFA or account linking, validate issuer/approver authority,
  manage grants or assignments, or provide API routes, persistence, audit
  storage, or production tenant isolation ([README.md §Pure authorization kernel](./README.md#pure-authorization-kernel);
  [authorization.py:254–263](./src/scientia/authorization.py#L254)).
- **Tests are not production evidence.** The cited tests assert behavior on
  synthetic inputs. They were inspected for this package but **were not run**
  for this documentation-only milestone.

The draft's fail-closed hold is a policy instruction, **not a runtime control**.
It does not disable current evaluator behavior or block an application service
([AUTHORIZATION-POLICY-DRAFT.md, Sections 5–6](./AUTHORIZATION-POLICY-DRAFT.md#5-policy-requirements-vs-current-implementation-enforcement)).

## Safety holds pending decisions and enforcement

These are holds to preserve until both the required policy decisions are
ratified and enforceable controls exist. The current repository does not
implement all of these holds at a service boundary.

- **All grant-backed actions:** Do not issue, approve, renew, or operationally
  rely on grants for write, export, or other actions until A1 is ratified and
  a complete base-role/action policy is approved. The evaluator denies
  grant-backed write/export today; apply the additional U-2/U-3 duration and
  U-5/U-6 authority holds where relevant.
- **Confidential-content grants:** Keep issue, approval, renewal, and
  operational reliance disabled until U-1 is ratified, U-2 is approved and
  enforced, and U-5/U-6 are resolved and enforceable.
- **Administrator elevation:** Keep grant issuance, approval, renewal, and
  operational reliance disabled until the separate U-3 maximum is approved
  and enforced and U-5/U-6 are resolved. `ADMIN_ELEVATION` currently denies
  in the evaluator, but this does not implement an elevation workflow or
  service-level guard.
- **Research assignments:** Keep assignment creation and renewal disabled
  until both U-4 durations are approved and enforced. Do not treat a
  caller-supplied generic maximum as an approved default or renewal workflow.
- **Confidential reads:** Do not authorize confidential content based on
  assignment alone. Do not rely on a read grant to replace an otherwise
  missing role or assignment permission. These are now evaluator-level
  denials, but no service boundary exists here to ensure every operation uses
  the evaluator.
- **Independent high-stakes review:** Keep any approval or finalization path
  that depends on distinct reviewers disabled or fail closed until U-7 is
  resolved and canonical identity/account-linking enforcement exists. Do not
  rely on account identifiers alone as proof of distinct people.
- **Unverified permissions and history:** Continue denying undefined
  permissions. Do not implement policy-sensitive behavior based on
  unverified Decisions 11–36.

## Verification scope

This package was prepared by inspecting the policy draft, evaluator,
authorization tests, README, and retained authorization checkpoints. Its
original source/test references describe the baseline code and expectations at
that review; they are not a production-security assessment. No tests were run
for that package milestone. In Milestone 13, the authorization module and its
tests were changed; the authorization module reported 66 passed, the full
suite reported 252 passed, and Ruff reported all checks passed. Those results
do not establish production security or policy ratification.
