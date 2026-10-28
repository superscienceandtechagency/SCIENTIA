# SCIENTIA Trusted Authorization Boundary Design

> **Status: DESIGN FOR REVIEW — NOT IMPLEMENTED**
>
> Authorization policy remains **`DRAFT — PENDING OWNER RATIFICATION`**.
> This design is not policy approval, is not an implemented production
> security boundary, and is not a security certification.

## 1. Purpose and design principles

Define a trusted application boundary that can use the existing pure
authorization evaluator without treating its inputs as authenticated facts.
The boundary must establish identity, membership, tenant/workspace/resource
ownership, and current policy state from trusted sources; authorize each
protected operation; and preserve the decision through the operation's
security-relevant side effects.

The design is intentionally provider- and persistence-neutral. It does not
select an identity provider, database, queue, deployment model, jurisdiction,
retention period, or unresolved policy value. It preserves least privilege,
tenant isolation, separation of duties, auditability, and fail-closed behavior.
No production-sensitive capability is enabled by this document.

## 2. Current architecture and evaluator limits

The repository currently contains a pure Python authorization module,
evidence/research domain records, and deterministic local research workflows.
The declared dependencies include FastAPI and Pydantic, but the inspected
source has no application routes, authentication adapter, persistence layer,
queue, audit store, or protected-operation authorization service.

`scientia.authorization.authorize` evaluates immutable
`Principal`, `Membership`, `Resource`, `Assignment`, and `AccessGrant` values
([authorization.py:73](./src/scientia/authorization.py#L73),
[authorization.py:88](./src/scientia/authorization.py#L88),
[authorization.py:110](./src/scientia/authorization.py#L110),
[authorization.py:127](./src/scientia/authorization.py#L127),
[authorization.py:155](./src/scientia/authorization.py#L155),
[authorization.py:254](./src/scientia/authorization.py#L254)).
It checks supplied principal/membership subject equality, active membership,
organization/workspace equality, a supplied MFA boolean, assignment and grant
scope and state, and the actions currently represented in the kernel
([authorization.py:272](./src/scientia/authorization.py#L272),
[authorization.py:303](./src/scientia/authorization.py#L303),
[authorization.py:355](./src/scientia/authorization.py#L355),
[authorization.py:386](./src/scientia/authorization.py#L386)).
It also trusts the caller-supplied `evaluated_at` value used for expiry and
revocation comparisons ([authorization.py:196](./src/scientia/authorization.py#L196),
[authorization.py:369](./src/scientia/authorization.py#L369),
[authorization.py:406](./src/scientia/authorization.py#L406)); the evaluator
does not establish a trusted clock.
For confidential reads, the current evaluator requires the existing
role/assignment path and a valid scoped read grant; grant-only write/export,
deletion, and administrator elevation do not authorize access. Those are
evaluator-level behaviors, not authentication or application-boundary
enforcement ([README.md, “Pure authorization kernel”](./README.md#pure-authorization-kernel);
[authorization tests](./tests/test_authorization.py#L265)).

The evaluator does not verify where any input came from, authenticate a person,
verify OIDC claims or MFA, verify issuer/approver authority, link duplicate
accounts, or prove two identities represent different people. Its immutable
records do not protect the caller that constructs them. Supplying an
`AuthorizationPolicy` or a synthetic duration does not make that value an
approved policy. There are no current service callers that enforce a decision
at data-access or operation boundaries.

Research workflows are local orchestration over PDFs, passages, and supplied
assessments ([prepare_research](./src/scientia/workflow.py#L101),
[finalize_research](./src/scientia/workflow.py#L191)). The
`HUMAN_REVIEWED` assessment state is a record state, not a two-person,
authenticated high-stakes approval workflow
([ReviewState](./src/scientia/verification.py#L33),
[synthesis.py:39](./src/scientia/synthesis.py#L39)).

## 3. Threat model

| Threat | Example and impact | Required design control |
|---|---|---|
| Forged identity or role | A request submits another user's ID, role, tenant, or `mfa_verified=true`, impersonating a privileged actor. | Derive principal only from a successfully validated authentication result. Load membership and roles server-side. Ignore caller-supplied identity, role, and MFA claims as authorization facts. |
| Token confusion or session abuse | An ID token is accepted as an API access token, a token for another client is replayed, or a session is fixed/reused after logout. | Enforce distinct token purposes, issuer, audience, and client/flow contracts; bind and validate session lifecycle; apply transport-appropriate CSRF/session protections. Reject invalid or revoked sessions. |
| Cross-tenant access | A caller supplies a resource ID from another organization/workspace, exploits an unscoped lookup, or receives another tenant's shared-cache entry. | Treat requested tenant/workspace IDs only as selectors. Verify active membership and load the resource with organization/workspace constraints in the same trusted repository boundary. Scope cache keys and cached values by tenant, workspace, resource, action, and relevant state/version; never let cache hits bypass authorization. |
| Privilege escalation | A grant, assignment, or role is used to obtain an unrelated action, confidential content, export, deletion, or elevation. | Evaluate one explicit action at a time; enforce the ratified role/action policy and scoped assignment/grant requirements. Unknown or unsupported actions deny. Do not infer permission from a grant or caller claims. |
| Stale assignment or membership | A user's membership or assignment has expired, changed, or been revoked after a decision was cached. | Read current authoritative state at each protected operation boundary or use a consistency/version mechanism that detects changes before side effects. Missing, stale, or unverifiable state denies. |
| Revoked grant | A confidential-content or elevation grant is revoked while a request or job is pending. | Rehydrate current grant state before access and again before sensitive side effects. Revoke/cancel queued work; running work stops at the next safe boundary before further protected effects. |
| Replayed request | A previously authorized mutation or review submission is resent, creating duplicate or stale effects. | Authenticate and authorize every attempt. Use durable, scoped idempotency/command identity for state changes and reject conflicting reuse. Idempotency is not authentication or authorization; do not replay cached sensitive responses after access is withdrawn. |
| Time-of-check/time-of-use race | Authorization is checked, then membership, resource ownership, grant, or assignment changes before read/write/export/finalization commits. | Bind state read and protected effect to one transaction/snapshot with appropriate row locks or version checks. For external/long-running effects, revalidate immediately before each sensitive boundary and use an outbox or equivalent durable handoff. |
| Untrusted evaluation time | A caller or queued payload backdates `evaluated_at`, making an expired or revoked grant/assignment appear active. | Obtain evaluation time only from a server-controlled trusted clock at the authorization boundary. Treat missing/unreliable time as denial; define clock-health and comparison behavior without inventing a policy skew allowance. |
| Policy substitution or rollback | A stale, tampered, unratified, or superseded policy bundle is loaded while the application believes it is using the current approved rules. | Load only an integrity- and provenance-verified ratified policy version from a trusted publication path. Pin the version to the decision/operation; reject unapproved versions and unauthorized rollback. The authority and format of ratification remain owner-governed. |
| Forged or duplicate reviewer accounts | One person uses multiple accounts to appear as independent reviewers. | Use authenticated identities and an approved canonical-account-linking process. Until that process is authoritative and enforced, do not enable high-stakes finalization based on distinct account IDs. |
| Audit disclosure or tampering | Logs expose document contents, credentials, tokens, or grant reasons; unauthorized users read audit history. | Record content-free, structured metadata; restrict audit access; audit audit reads; protect event integrity and fail closed when mandatory audit persistence fails. Retention and jurisdiction remain unselected. |

The model assumes the identity provider, application runtime, trusted
repositories, transaction manager, and audit sink are configured and operated
as trusted components. Their compromise remains an infrastructure/security
operations risk and requires deployment-specific controls outside this design.

## 4. Trusted principal and authentication boundary

### 4.1 Replaceable OIDC-compatible adapter

Put authentication behind an adapter interface so a standards-compatible
provider can be replaced without changing authorization policy or domain
operations. Specify the supported client types and protocol flows before
implementation. Validate the token type and intended use, signature using an
explicitly allowed algorithm and current trusted issuer keys, exact issuer,
expected audience/client, time-validity, and all flow-specific protections.
Keep token purposes distinct: an ID token used to establish a login is not an
API bearer access token; validate API access tokens against their intended
resource audience and token-use contract. For signed tokens, validate the
signature and claims under the configured issuer trust. If the selected
provider uses opaque access tokens, use its authenticated introspection or
equivalent validation mechanism instead of assuming JWT format; any lookup
failure or inactive response denies.
For an authorization-code browser flow, this includes exact redirect URI
validation and applicable state, nonce, and PKCE checks. Handle signing-key
rotation without accepting unknown keys or silently weakening validation.
Reject missing, invalid, ambiguous, expired, or incorrectly purposed
authentication evidence. The application does not accept a username, subject
ID, role, tenant, or MFA assertion from a request body as proof of identity.

Each request must also establish that its server-side session/token remains
valid for the intended client and operation. Define logout, session
revocation, expiration, refresh, and provider-unavailability behavior for the
chosen transport. If current authentication status cannot be established when
required, deny; do not convert an identity-provider outage into anonymous or
cached authorization success.

Apply session controls appropriate to the selected transport. For
cookie-authenticated browser requests, require secure cookie attributes,
session identifier rotation at authentication/privilege changes, and CSRF
protection for state-changing requests. For bearer-token clients, prevent
token leakage through URLs, logs, or untrusted storage. Add abuse controls for
authentication endpoints without choosing numeric rate limits in this
design.

On successful authentication, the adapter issues an internal, session-bound
trusted-principal value carrying the verified issuer/subject pair and an
authentication/session reference. Only the trusted adapter path may create
that value from verified authentication; transport-facing code must not
construct it from request fields. A language-level private constructor is
defense in depth, not a security boundary by itself. Enforce the trust
boundary structurally: protected handlers receive the adapter's verified
principal type, and untrusted transport values cannot be passed as trusted
facts. Recheck session validity and required assurance at every new request;
do not treat an already-constructed principal or queued payload as a durable
authentication proof. An internal canonical-person key may be attached only
after the approved account-linking service establishes it. Authentication
identifiers alone must not be used to claim distinct-human independence while
U-7 is unresolved.

### 4.2 MFA

The policy draft records a conversation-derived requirement to use a
replaceable OIDC-compatible boundary, require MFA for administrators,
reviewers, and high-stakes approvers, and prefer it for all users where
feasible ([policy draft §3.1](./AUTHORIZATION-POLICY-DRAFT.md#3-conversation-derived-approved-rules)).
The evaluator currently checks only a caller-supplied boolean for some roles
([authorization.py:286](./src/scientia/authorization.py#L286)); this is not
proof of MFA.

The authentication adapter must verify provider-supported MFA
assurance/evidence for the authenticated session and map it to an internal
verified authentication context. It must validate the issuer's assurance
semantics rather than trusting an arbitrary `amr`/`acr` string as proof.
Authorization consumes that verified context, never a request claim or an
unchecked boolean. If required MFA evidence is absent, invalid, unverifiable,
or not at the approved assurance level, deny the protected action. Do not
invent an assurance class, step-up interval, session age, or all-users MFA
mandate; those values/interpretations require authoritative policy and owner
input.

### 4.3 Authentication versus authorization responsibilities

- **Authentication adapter:** validates the OIDC-compatible response,
  establishes the verified provider subject and session, and supplies verified
  MFA evidence.
- **Identity/membership service:** resolves the subject to an active
  application account and organization/workspace membership using trusted
  records. It supplies roles and any canonical identity mapping only from
  authoritative records.
- **Resource repository:** resolves ownership, workspace, sensitivity, and
  current resource state without trusting caller-supplied ownership facts.
- **Authorization facade:** builds one immutable context for one action from
  those trusted records, calls the pure evaluator, and returns a typed
  decision. It does not authenticate or make unratified policy choices.
- **Operation service:** requires an allow decision and performs the
  protected operation with the same scope and current state. No controller,
  job handler, or domain caller may bypass this service to access protected
  data or mutate protected state.

## 5. Tenant/workspace-scoped authorization flow

1. Authenticate the request and obtain a verified internal principal; check
   session validity and required assurance for this request.
2. Parse requested organization/workspace/resource identifiers as untrusted
   selectors only. Do not treat them as membership or ownership proof.
3. Resolve active organization and workspace membership for the authenticated
   principal from the authoritative membership source. Reject inactive,
   missing, ambiguous, or mismatched membership.
4. Fetch the resource through a scoped repository operation constrained by
   organization, workspace, and resource identifiers. Do not first fetch by
   globally supplied resource ID and authorize afterward. Confirm the
   returned resource's ownership and sensitivity from persisted state.
   Apply equivalent ownership scoping to any backing object/blob store,
   passage/evidence store, search index, cache, and derived artifact store;
   never authorize access based only on a client-supplied storage key.
5. Load current role assignments, specific research assignment, scoped
   grants, and the ratified policy version from trusted stores. Verify the
   policy artifact's ratification provenance and integrity, reject
   unauthorized rollback or unapproved/superseded versions, and bind the
   accepted version to the decision. Do not accept these facts from request
   parameters, client tokens, cached job payloads, or arbitrary
   caller-created evaluator records.
6. Construct the evaluator context for exactly one action and one resource.
   Obtain `evaluated_at` from a server-controlled trusted clock at the
   decision boundary; never copy it from the request or job payload. Apply
   the least-privilege decision. Missing/unreliable time, missing policy
   version/configuration, unknown action, stale facts, repository errors, or
   scope inconsistency deny and produce an operationally appropriate error
   without revealing protected resource existence. Internal monitoring must
   distinguish dependency failures from ordinary policy denials without
   exposing protected data.
7. Carry the scoped resource reference, principal, policy version, and
   authorization-relevant state versions into the operation. Revalidate
   current state at the transactional side-effect boundary as specified below.

Protected services should expose scoped operations rather than unrestricted
resource lookups. Tenant/workspace constraints must apply to reads, lists,
mutations, audit queries, exports, ingestion and derived-content retrieval,
object/blob access, caches, and background-job rehydration. Where supported
by the selected persistence technology, enforce tenant/resource relationships
with database constraints or row-level controls as defense in depth; these do
not replace application authorization or scoped queries.

## 6. Protected operation boundaries

Every protected operation is checked at the boundary that can disclose or
change protected state. A successful check for one action does not authorize a
different action. Until a trusted application boundary is implemented and
verified, do not expose application-facing protected operations at all—not
even public-resource reads or ordinary review submissions. This hold is
separate from the pure evaluator's limited synthetic allow decisions.

| Operation | Required checks and enforcement boundary | Current hold |
|---|---|---|
| **Read research** | Authenticate; resolve current membership and resource ownership; authorize `READ_RESEARCH`; enforce sensitivity, role, assignment, and confidentiality requirements; read through the same scoped snapshot. For streaming/long reads, revalidate before later protected chunks or stop safely if state changed. | Keep confidential reads denied unless ratified policy and trusted enforcement are complete. Evaluator-level U-1 behavior is not a service boundary. |
| **Ordinary review submission** | Authenticate; resolve current membership, reviewer authority and resource scope; check active assignment and policy eligibility at submission; bind the submission to the authorized resource and audit metadata. | No submission endpoint/workflow currently exists. Keep all application-facing submissions disabled until trusted identity and operation-boundary enforcement are in place; high-stakes review has additional holds below. |
| **Write research** | Authorize the exact write against the approved role/action policy and current scope inside the transaction that commits the mutation. Validate resource version/state and required audit before commit. | Deny; no approved complete role/action matrix or service operation currently exists. A matching grant is not sufficient. |
| **Export research** | Authorize the export action and each included resource before rendering; scope the export query; for asynchronous/streamed exports, revalidate before generation and before release. Record metadata, not content. | Deny until the applicable policy, workflow, and operation-boundary enforcement are approved and implemented. |
| **Deletion and restore** | Authorize the specific deletion request; atomically record a deny-access tombstone and required event before asynchronous purge; restore must reapply deletion state before content is served. Revalidate state at purge/restore boundaries. | Deletion is currently denied by the evaluator. Keep deletion/restore disabled until authoritative policy, lifecycle, recovery, and audit controls exist. |
| **Administrative elevation** | Use a separate elevation action and maximum, authenticated MFA step-up, designated authority, independent approval as approved, narrowly scoped and time-bounded elevated state, revocation, and per-operation revalidation. | Current evaluator denies elevation. Do not add an elevation path until U-3, designation/separation decisions, policy ratification, and enforcement are complete. |
| **High-stakes classification** | A research lead may propose a sensitivity/classification change and an authorized high-stakes approver confirms it, with required reason, identities, timestamp, and change history; apply the update and event atomically, then re-evaluate existing access under the new classification. | This workflow is recorded only as conversation-derived policy in the draft. Do not permit classification changes through an application until ratified authority, exact transition rules, trusted identity, and audit enforcement are defined and tested. |
| **High-stakes review** | Authenticate each reviewer; check assignment and eligibility at submission and finalization; prevent self-review; keep the second submission blind to the first; treat abstention as non-approval; disagreement remains unresolved until separately authorized third-person adjudication; revalidate reviewer independence and eligibility before finalization. | No such workflow exists. `HUMAN_REVIEWED` is not this control. Keep high-stakes approval/finalization disabled pending authoritative policy and canonical identity enforcement. |
| **Audit metadata** | Authorize a narrowly scoped metadata query; apply tenant/workspace filters; record the audit read itself through a separate durable event path; never return document text or secrets as audit metadata. | Evaluator's `SECURITY_AUDITOR` role check does not itself implement restricted audit storage, query scoping, or read-event recording. |

High-stakes review (including blind second review, abstention, disagreement,
and third-person adjudication) and research-lead proposal/authorized
high-stakes-approver confirmation for classification changes are recorded in
the draft as conversation-derived rules, not as an independently recovered
Decisions 11–36 source
([policy draft §3.1](./AUTHORIZATION-POLICY-DRAFT.md#3-conversation-derived-approved-rules)).
Do not treat that historical record as formal ratification.

## 7. Transactional consistency, replay, revocation, and jobs

### 7.1 Consistency and TOCTOU

For database-backed changes, authorization-relevant reads and the durable
protected mutation should share one transaction and a consistency strategy
appropriate to the chosen store: for example, serializable/consistent
transactions, row locks, or explicit version checks. The chosen implementation
must prove that a concurrent membership, assignment, grant, resource ownership,
sensitivity, or policy-version change cannot slip between authorization and
commit. Define the operation's linearization point so a revocation and a
concurrent protected mutation cannot both be treated as having taken effect
first; after a revocation is committed, no later protected side effect may
rely on the revoked state. For a read, bytes already disclosed cannot be
recalled; revocation must prevent later chunks/releases and future reads.
Required audit/outbox records must be committed atomically with the state
transition; if the required event cannot be durably recorded, abort the
protected transition.

Reads must use a tenant-scoped query and a consistent authorization/resource
snapshot. Long-running streams and external side effects cannot hold one
database transaction for their full duration; bind them to an immutable job
or command identity, revalidate immediately before each sensitive release or
side effect, and provide a tested stop/cancel point. Do not claim transaction
atomicity across a third-party system; use an idempotent outbox/worker protocol
and explicit reconciliation where needed.

### 7.2 Request replay and idempotency

Authentication and authorization are required for every request, including a
retry. Mutating, deletion, export-generation, elevation, and review-submission
commands should use a durable idempotency key or unique command ID scoped to
the authenticated principal, tenant/workspace, action, and target. Store a
request digest and final command status, not document contents or credentials.
The same key with a conflicting command is rejected. A retry must still pass
current authorization; cached results must not disclose protected data after
revocation. OIDC flow replay protection and application command idempotency
address different threats and are both required where applicable. No
time-window value is set here.

### 7.3 Revocation and queued/running work

Revocation or membership change must make subsequent protected operations
deny. Any cache must have a documented invalidation/version check that detects
authorization-relevant changes before a protected boundary; absent a proven
freshness guarantee, read current authoritative state instead of relying on a
stale allow. Do not reuse or cache an `AuthorizationDecision` as a transferable
permit; a decision is bound to its principal, action, resource, policy version,
evaluation time, and state snapshot.

Queue payloads contain an opaque job/command reference, initiating principal
reference, tenant/workspace/resource scope, requested action, and
correlation/idempotency reference—not a reusable allow decision or unverified
role, grant, assignment, or MFA facts. Before execution, a worker rehydrates
current identity/account, membership, resource ownership, policy version,
assignment, and grant, then evaluates again. It repeats the check immediately
before export release, deletion, write commit, review finalization, or another
sensitive side effect. Revocation cancels queued work; running work stops at
the next safe boundary and emits a content-free outcome event. No queue is
currently present in the repository.

## 8. Audit-event design

### 8.1 Content-free event envelope

Use structured, append-oriented security events for authentication outcomes,
authorization decisions, grant/assignment lifecycle, policy changes,
administrative elevation, export, deletion, review submission/finalization,
revocation, and audit reads. A minimal event envelope may contain:

- event type, event ID, timestamp, and correlation/command reference;
- authenticated internal actor reference and, where applicable, approver
  reference;
- organization/workspace and opaque resource reference;
- requested action, allow/deny outcome, stable reason category, and policy
  version;
- relevant state/version references and lifecycle transition metadata,
  including before/after classification labels when a classification change
  is authorized.

Exclude document text, passage text, request/response bodies, credentials,
tokens, session secrets, private keys, and arbitrary exception contents.
Avoid copying free-form grant reasons into general logs; if a policy-approved
workflow requires a reason, store it only in the protected record with
separately controlled access and a safe audit reference. Treat opaque IDs and
reason metadata as sensitive metadata, not as public data.

### 8.2 Durability and access control

Where policy requires an audit event, the protected action must not be
acknowledged or committed until the event is durably accepted in the same
transaction or an equivalent transactional-outbox mechanism. Audit write
failure fails closed for the associated sensitive operation. Outbox delivery
must be idempotent and observable; do not silently drop or success-fallback.

Audit metadata access is a separate permission, restricted to explicitly
designated security/audit personnel under a least-privilege scope. Every audit
read must itself generate a durable, content-free event. Caller-visible
responses and routine logs must avoid revealing whether a protected resource
exists when the requester is not authorized. Who designates auditors, exact
access scope, retention, integrity controls, and jurisdiction are not settled
by this design.

## 9. Dependency-ordered implementation roadmap

This roadmap is a design sequence, not authorization to implement unresolved
policy or enable the listed capabilities.

| Order | Workstream | Depends on | Exit criteria |
|---|---|---|---|
| 0 | Establish policy authority and blockers: ratify a versioned policy; resolve capability-specific selections and owner-authority items; retain Decisions 11–36 as unverifiable unless the original is found. | Owner decision and authoritative record. | Ratifier/date/version/amendments recorded; role/action and capability-specific rules defined; no numeric value inferred. |
| 1 | Implement replaceable OIDC-compatible authentication adapter and trusted-principal construction; verify MFA evidence for the policy-required roles and selected transport. | Approved provider/client/flow configuration and MFA assurance requirements; canonical identity policy before identity-independence use. | Forged request identity/role/MFA fields cannot affect the trusted principal; protocol, session, logout/revocation, and required MFA failures deny. |
| 2 | Implement authoritative account, organization/workspace membership, and canonical identity resolution; build tenant-scoped resource repositories. | Trusted-principal contract; approved U-7 evidence/process before canonical-person assertions. | No unscoped protected repository lookup; cross-tenant and inactive-membership tests deny. |
| 3 | Add a single application authorization facade that constructs evaluator facts and trusted evaluation time from trusted repositories and approved policy configuration. | Orders 0–2; ratified role/action matrix; verified, non-rollbackable policy publication/versioning. | No request or job path can construct its own trusted facts or bypass the facade; unknown/missing/stale/unapproved policy or unreliable time denies. |
| 4 | Add transactional operation primitives and content-free audit/outbox persistence, including audit-read authorization and audit-of-audit. | Chosen persistence/transaction technology, audit authority, retention/jurisdiction decisions, and policy event requirements. | Required state and event commit atomically or neither commits; audit failure aborts; audit payload tests prove content/secret exclusion. |
| 5 | Integrate application-facing public/confidential reads, ordinary review submissions, writes, and exports; apply specific scope, sensitivity, approved role/action, assignment, and confidentiality rules. Keep unsupported operations denied. | Orders 0–4 and relevant ratified role/action/confidentiality/reviewer policy; U-2/U-4 where applicable. | Boundary integration tests prove least privilege and tenant scope at request admission, data retrieval, review submission, and export release. |
| 6 | Implement deletion/restore and elevation only as separately approved workflows; include tombstones, recovery handling, step-up MFA, authority, distinct approval, revocation, and audit. | Orders 0–4; deletion policy and recovery plan; U-3, U-5, U-6 and approved authority model. | Revoked/expired/unapproved actions deny; restore cannot resurrect deleted access; elevation expires/revokes at approved bounds. |
| 7 | Implement high-stakes classification changes and high-stakes review as distinct workflows. Classification requires proposal/confirmation authority and atomic change history. Review requires blind independent submissions, explicit abstention, unresolved disagreement, adjudication, and finalization revalidation. | Ratified classification/review rules; Orders 0–4; U-7 canonical identity and resolved reviewer/approver eligibility and authority. | Unauthorized classification changes deny and updated sensitivity immediately affects access; duplicate-account/self-review denies; second reviewer cannot access first submission before their own; adjudication and finalization checks pass. |
| 8 | Add job dispatch, revalidation, cancellation, safe stops, replay/idempotency, and concurrency verification for operations that require asynchronous work. | Orders 0–7 as applicable; chosen queue/transaction/outbox contracts. | Stale/revoked work cannot start or perform later sensitive effects; duplicate commands do not duplicate side effects; race tests pass. |
| 9 | Perform integration, concurrency, failure-injection, deployment, and independent security verification; update implementation-status documentation only after evidence. | All applicable prior work and deployment-specific threat analysis. | Acceptance criteria below pass in the actual configured runtime; remaining risks and evidence are documented. |

Policy-independent scaffolding may be considered separately, but no step may
enable a capability before its listed authority, enforcement, and verification
conditions are satisfied.

## 10. Unresolved owner-authority decisions and fail-closed conditions

The current draft remains `DRAFT — PENDING OWNER RATIFICATION`
([policy draft status](./AUTHORIZATION-POLICY-DRAFT.md#L1)). The ratification
package is explicitly for review only
([ratification package status](./AUTHORIZATION-RATIFICATION-PACKAGE.md#status)).
At minimum, these decisions remain unresolved or unratified:

1. **Whole-policy ratification and U-1/A1/B2:** confirm/amend recorded
   selections and record ratifier, date, approved version, and amendments.
   U-1 is selected as a confidentiality-only `READ_RESEARCH` condition, not
   an action grant, but remains pending formal ratification.
2. **U-2:** numeric maximum for confidential-content grants.
3. **U-3:** separate numeric maximum for administrator elevation.
4. **U-4:** assignment default and maximum durations.
5. **U-5:** who designates security personnel/auditors and the scope of their
   issue, approval, revocation, and audit authority.
6. **U-6:** whether grant issuer and approver require separate operational
   duties beyond distinct identities.
7. **U-7:** canonical identity/account-linking evidence and process, including
   duplicate-account treatment.
8. **U-8:** locate and verify the original Decisions 1–36 record. Decisions
   11–36 remain **`NOT VERIFIABLE AS NUMBERED`**; do not reconstruct or
   renumber them.
9. **Base-role/action policy:** define the full role/action matrix and which
   actions require resource assignments. A1 constrains grants but is not a
   complete permission matrix.
10. **High-stakes review authority:** confirm applicable reviewer eligibility,
    classification proposal/confirmation, abstention, disagreement, and
    third-person adjudication rules in the authoritative policy. Existing
    draft text is conversation-derived, not a recovered complete numbered
    source.
11. **MFA policy detail:** confirm required assurance/evidence and any
    step-up/session freshness conditions; do not infer these from the current
    boolean evaluator input.
12. **Audit and deployment governance:** identify authorized audit roles,
    event retention period, integrity/access requirements, and deployment
    jurisdiction/model. No retention duration or jurisdiction is selected
    here.
13. **Policy publication authority:** establish how an owner-ratified,
    versioned policy artifact is published and how its approval provenance,
    integrity, supersession, and any rollback authorization are verified.
    Until that evidence is trusted, the corresponding policy must not be
    loaded as an authorization allow configuration.
14. **Authentication transport details:** select supported client/flow
    types and define their verified token, session, CSRF, logout, and
    revocation semantics. Do not accept an ID token as an API access token or
    infer MFA assurance from an unverified claim.

**Global fail-closed gate:** no application-facing protected operation may be
enabled—including public-resource reads, ordinary review submissions, writes,
exports, audit queries, confidential-content reads, assignment/grant
issuance or reliance, classification changes, administrator elevation,
deletion/restore, or high-stakes review/finalization—until a trusted
authentication and tenant/resource operation boundary is implemented,
independently verified, and using an owner-ratified, provenance-verified
policy version. Each capability also remains held until its specific
authority, lifecycle, durability, and acceptance criteria below are
satisfied. Do not treat documentation, evaluator unit tests, a
caller-supplied principal, or a configured test duration as a runtime control
or production proof.

## 11. Verification plan and acceptance criteria

No tests are run as part of this design milestone. During implementation, add
and run at least these test classes:

### Authentication and principal provenance

- Reject invalid signature, issuer, audience, nonce, expired/future token,
  invalid flow response, wrong token purpose/type, unknown signing key,
  invalid redirect/CSRF/PKCE/state protections as applicable, failed or
  inactive opaque-token introspection, revoked sessions, session fixation,
  missing required MFA, and unsupported assurance.
- Prove caller-supplied user ID, roles, tenant/workspace, identity provider,
  and MFA claims cannot override trusted adapter output.
- Verify account-linking behavior against the owner-approved canonical
  identity evidence; duplicate accounts cannot satisfy independent-reviewer
  requirements.
- Prove application code cannot pass a fabricated internal principal through
  a protected handler; language-level constructor visibility alone is not
  accepted as the trust boundary.

### Tenant scope and action authorization

- Deny cross-organization/workspace resource IDs, unscoped repository
  lookups, inactive/missing memberships, stale ownership, and tampered
  request/job scopes across relational records, caches, indexes, and
  object/blob stores.
- Test every ratified role/action pair. A grant cannot create base-role
  permission; assignment alone cannot authorize confidential reading; U-1
  only adds the confidentiality condition for an otherwise permitted read.
- Keep delete/elevation/high-stakes actions denied until their dedicated
  approved paths exist. Test that audit metadata reads are scoped and do not
  reveal document content.
- Verify that no public-read, ordinary-review, or classification operation is
  reachable through an application endpoint before trusted-boundary rollout
  acceptance; classification changes update audit state and authorization
  sensitivity atomically.

### Transactions, revocation, replay, and audit

- Inject membership, assignment, grant, ownership, sensitivity, and policy
  changes between request admission and commit/release; prove the action
  denies, aborts, or stops at the required safe boundary.
- Prove caller-supplied or queued `evaluated_at` cannot affect decisions;
  unavailable or unhealthy trusted clock denies. Test policy-artifact
  tampering, unratified versions, supersession, and unauthorized rollback.
- Test expiry/revocation before queue admission, before worker execution, and
  immediately before an irreversible or externally visible side effect.
- Replay identical and conflicting command IDs; ensure no duplicate side
  effects and no sensitive cached response after revocation.
- Inject transaction, outbox, and audit-store failures; prove required
  protected operations fail closed with no partial success-shaped state.
- Assert audit events contain approved metadata only and never contain
  document/passage text, credentials, secrets, tokens, or raw request bodies.
  Verify audit-read events are durable and access-controlled.

### High-stakes review

- Verify two distinct authenticated canonical people, prohibition of
  self-review, blind second submission, reviewer eligibility at submission
  and finalization, abstention-as-not-approval, unresolved disagreement, and
  separately authorized third-person adjudication.
- Verify revocation or identity-link changes before finalization prevent an
  invalid result from becoming final.

### Acceptance criteria

The trusted boundary is ready for a specific capability only when all
applicable criteria are demonstrated:

1. No protected action derives user identity, role, membership, tenant, MFA,
   assignment, grant, resource ownership, or policy from untrusted request
   claims.
2. Every application-facing operation is routed through a mandatory boundary
   with server-side tenant/workspace and resource ownership checks. This
   includes public and confidential reads, writes, exports, deletion,
   elevation, review submission/finalization, classification change, and
   audit. Unscoped access is not available to the operation service.
3. Policy artifacts are provenance- and integrity-verified, versioned, and
   protected against unauthorized rollback; the exact ratified version and
   complete applicable role/action mapping are used. Missing, invalid,
   superseded, stale, or unknown policy denies.
4. Authorization time comes from a trusted server-side clock, not a request
   or job payload; clock failure/unreliability denies. Expiry and revocation
   checks use that trusted time.
5. Confidential reads require both ordinary entitlement and the separate
   confidentiality condition; grants add no unrelated action; assignments
   alone cannot permit confidential content.
6. Every side effect is transactionally bound to current authorization or
   revalidated immediately before the side effect. Concurrency tests cover
   TOCTOU races, defined revocation ordering, and safe stop/cancel behavior.
   Already-disclosed bytes are recognized as irreversible.
7. Revocation of membership, assignment, grant, or elevation prevents new
   operations and invalidates queued work; running work cannot perform
   subsequent sensitive effects after its required safe boundary.
8. Replay handling is durable and idempotent for state-changing operations,
   while every retry still requires current authentication and authorization.
9. Required audit is durable, content-free, access-controlled, and audited
   when read; required audit failure prevents the protected operation from
   succeeding.
10. High-stakes review cannot finalize without the ratified independent-review
   process, canonical-identity enforcement, eligibility revalidation,
   abstention handling, and separate adjudication where required.
11. High-stakes classification cannot change without authorized proposal and
    confirmation, durable change history, and immediate enforcement of the
    resulting sensitivity classification.
12. Focused unit, integration, concurrency, and failure-injection tests,
    relevant static checks, and deployment-specific security verification
    pass and their actual results are recorded. Tests alone are not
    certification.
13. Policy documents retain the pending status until formal ratification;
    Decisions 11–36 remain `NOT VERIFIABLE AS NUMBERED` unless their original
    authoritative source is found.

## 12. Evidence limitations and status

This design is based on the current evaluator, authorization tests, README,
policy draft, ratification package, enforcement-gap assessment, inspected
domain/workflow modules, and the retained “Enforcing Authorization
Invariants” checkpoint in the session checkpoint store. The checkpoint and
conversation-derived rules are contextual evidence, not the missing
authoritative Decisions 1–36 record.

The authorization tests use synthetic principals, memberships, assignments,
grants, and policy values; passing unit tests would not establish that an
identity provider, persistence store, operation boundary, or deployment is
secure. No source, test, API, persistence, queue, audit, authentication, or
policy functionality is implemented by this document.

This is a design only. It is not an implemented authentication system, not a
production security boundary, not policy ratification, and not certification.
