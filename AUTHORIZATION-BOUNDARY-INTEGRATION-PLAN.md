# SCIENTIA Authorization Boundary Integration Plan

> **Policy status: `DRAFT — PENDING OWNER RATIFICATION`.**
>
> Decisions 11–36 remain **`NOT VERIFIABLE AS NUMBERED`** unless the original
> authoritative record is located and verified. This plan describes future
> integration work. It is not policy approval, implemented authentication,
> production authorization, or a security certification.

## 1. Current state

### Implemented code

- [`authorize`](./src/scientia/authorization.py#L254) is a pure evaluator of
  caller-supplied `AuthorizationContext` and `AuthorizationPolicy`. The
  context contains principal, membership, resource, action, time, and optional
  assignment/grant facts. It does not prove their provenance.
- The current evaluator requires a grant to be scoped, active, unrevoked,
  unexpired, and within a configured generic maximum. The default maximum is
  `None`, so grant-dependent decisions fail closed unless a policy is
  explicitly configured. Assignment-dependent decisions likewise require an
  assignment maximum ([`AuthorizationPolicy`](./src/scientia/authorization.py#L224),
  [`_validate_assignment`](./src/scientia/authorization.py#L356),
  [`_validate_grant`](./src/scientia/authorization.py#L378)).
- The current evaluator does not authorize `DELETE_RESEARCH` or
  `ADMIN_ELEVATION`. It denies grant-backed write/export, and a confidential
  research read requires the base role/assignment path and a matching read
  grant ([`authorize`](./src/scientia/authorization.py#L300)).
- [`AuthorizationBoundary`](./src/scientia/authorization_boundary.py#L159)
  accepts untrusted resource selectors and an action, obtains time and policy
  version metadata from injected providers, checks result shape and
  selector/action consistency, and invokes the evaluator. Its provider
  objects are assumed trusted; the boundary does not authenticate them.
- The boundary passes no loaded policy into `authorize()`, so evaluation
  currently uses `AuthorizationPolicy()` defaults. Its `PolicyVersion` value
  is an opaque label, not authenticated policy metadata
  ([`PolicyVersion`](./src/scientia/authorization_boundary.py#L60),
  [`evaluate`](./src/scientia/authorization_boundary.py#L186)).
- Existing boundary tests use fixed in-process clock, policy-version, and
  facts providers ([test helpers](./tests/test_authorization_boundary.py#L36));
  they exercise evaluator-layer confidential-read denial/allow cases
  ([assignment-only denial](./tests/test_authorization_boundary.py#L532),
  [grant-only denial](./tests/test_authorization_boundary.py#L549),
  [layered allow](./tests/test_authorization.py#L279)). These are synthetic
  unit tests, not evidence that production providers or an operation boundary
  are trusted.
- The boundary and evaluator are not called from application routes or
  protected-operation services. No authentication adapter, authoritative
  repository, persistence layer, queue, durable audit store, or transactional
  authorization service was found in the inspected project source
  ([readiness assessment](./AUTHORIZATION-IMPLEMENTATION-READINESS.md#2-evidence-reviewed-and-implementation-status)).

### Workflow and review models

[`prepare_research`](./src/scientia/workflow.py#L101) ingests local PDF paths
and retrieves passages; [`finalize_research`](./src/scientia/workflow.py#L191)
checks evidence provenance and synthesizes supplied assessments. These
functions are deterministic local workflow operations, not authenticated
tenant services. [`ClaimAssessment`](./src/scientia/verification.py#L111)
contains a reviewer label and `ReviewState`; the record and
`HUMAN_REVIEWED` value do not establish an authenticated independent reviewer
or a high-stakes approval workflow.

### Policy evidence and discrepancies

The policy remains **`DRAFT — PENDING OWNER RATIFICATION`**. A1, B2, U-1 and
other selections in the draft remain pending formal ratification. Numeric
grant/elevation/assignment durations, security-personnel designation and
authority, issuer/approver duties, canonical identity linkage, and complete
ratification metadata remain unresolved. Decisions 11–36 remain
**`NOT VERIFIABLE AS NUMBERED`** ([policy draft §6](./AUTHORIZATION-POLICY-DRAFT.md#6-unresolved-policy-register),
[ratification package status](./AUTHORIZATION-RATIFICATION-PACKAGE.md#status)).

Some existing documents preserve pre-Milestone-13 evaluator behavior. For
example, the ratification package's U-1 row says the current evaluator allows
a grant without role/assignment eligibility, and the gap assessment labels
some original findings as a pre-Milestone-13 baseline. Current
[`authorization.py`](./src/scientia/authorization.py#L303) is the source of
truth for present evaluator behavior: confidential reads require the base
role/assignment path plus a grant; write/export are denied even with a grant.
These evaluator safeguards do not resolve policy status or create an
application enforcement boundary.

## 2. Target request flow

The following is a target architecture, not an implemented request path.
Each transition must fail closed if its required input or authority is
missing, malformed, stale, or inconsistent.

1. **Untrusted request.** Treat body, URL, headers, cookies, resource IDs,
   requested tenant/workspace selectors, action names, timestamps, role
   claims, MFA flags, policy labels, and job parameters as untrusted. Parse
   and validate syntax only; validation does not establish authority.
2. **Authentication adapter.** Validate the presented credential/session
   according to a future owner-approved authentication contract. Reject
   invalid, expired, revoked, wrong-purpose, or wrong-audience credentials.
   Do not select an identity provider or login/session protocol in this plan.
3. **Verified identity context.** The adapter alone may create an
   internal request context from successful verification. It carries the
   canonical subject, issuer/session reference, authentication time and
   approved assurance/MFA evidence. No transport payload or generic
   deserializer may construct or override this context as verified.
4. **Tenant and resource resolution.** Derive permitted organization/workspace
   scope from authoritative membership associated with that verified
   subject. Resolve the requested resource with scope predicates in the
   repository query itself; then verify ownership and sensitivity from the
   canonical resource record. A caller-provided tenant ID is a selector, not
   proof of membership or ownership.
5. **Authoritative policy loading.** Load the owner-ratified policy artifact
   and its approval/provenance metadata from an authorized publication path.
   Validate integrity, approval state, effective/supersession state, and
   rollback authorization before using it. Bind that same policy snapshot and
   version to the facts and evaluation. Do not infer policy from a version
   label.
6. **Authorization facts and evaluation.** Obtain current role membership,
   action-specific assignment/grant, resource, and session facts from
   authoritative sources. Evaluate one explicit action using the verified
   policy object and server-controlled time. Deny on missing, contradictory,
   stale, or unverifiable state. A boundary result is permission to attempt a
   specific operation under a specific state snapshot, not a bearer
   capability reusable for unrelated resources or actions.
7. **Protected service operation.** The service—not the route or caller—
   owns the protected effect. Keep authorization and the effect in one
   transaction/snapshot where supported. Otherwise revalidate all relevant
   state immediately before the effect and define safe handling of state
   changes during streaming or long-running work.
8. **Security audit event.** Record the applicable security event with
   content-free metadata. For policy-required audited actions, do not report
   success or perform the protected effect if required durable audit fails.
   Audit access itself is a separately authorized operation.

## 3. Trust ownership

Typed values, immutable records, matching identifiers, and passing unit tests
do not establish trusted provenance. Only the owning component below may
assert the corresponding fact; consumers must verify its contract and
authoritative source.

| Fact | Owning component in target architecture | Untrusted values that do not establish it |
|---|---|---|
| Authenticated subject and credential validity | Authentication adapter, using an owner-approved verification contract | User ID, issuer string, token claims not cryptographically/session-validated, cookie/body identity |
| MFA/assurance state | Authentication adapter from verified authentication evidence under approved assurance rules | `mfa_verified` boolean or caller-supplied assurance label |
| Canonical identity and duplicate-account relationship | Owner-approved identity-linking process and authoritative identity registry | Similar names, matching emails, distinct account IDs, reviewer labels |
| Organization/workspace membership and roles | Authoritative membership service/repository, queried for the verified subject | Tenant/workspace IDs, role arrays, “admin” claims in request |
| Resource ownership and sensitivity | Authoritative resource repository and scoped object access layer | Resource IDs, sensitivity labels, metadata from request or cache without provenance |
| Assignment/grant existence, authority, lifecycle, and revocation | Approved lifecycle service and authoritative store | Caller-created `Assignment`/`AccessGrant`, actor IDs, expiry, revocation claim |
| Current evaluation time | Server-controlled clock service | Request timestamp, queued timestamp, browser clock |
| Approved policy contents and version | Ratified-policy publication and loading component | `PolicyVersion` label, caller-supplied configuration, matching version strings |
| Decision/action binding | Authorization service using verified identity, scoped facts, and verified policy | A prior allow result, action supplied by a client, decision copied across requests |
| Authorization/operation consistency | Protected-operation service and transactional persistence boundary | A standalone earlier allow, stale cache, unchecked job payload |
| Audit event authenticity and durability | Restricted audit writer and durable append-oriented store | Client event, success log without operation linkage, data copied from request |

The current `AuthorizationBoundary` injects a facts source, clock, and policy
version source. Its callable-method checks are interface checks only; they do
not prove the trust ownership described above
([provider assessment](./TRUSTED-PROVIDER-AND-POLICY-INTEGRITY-ASSESSMENT.md#2-evidence-categories)).

## 4. Policy integrity

The target loader must not treat a policy as authoritative merely because it
is parseable, has a nonblank version, matches another returned label, or
passes evaluator tests. Before a policy can influence a protected allow:

- The exact policy content must originate from a source whose write and
  publication authority is explicitly governed. The approved publication
  record must identify ratifier, approval date, version, and amendments.
- The loader must validate content integrity and provenance against the
  approved publication mechanism. A digest/signature, if later selected, can
  establish content identity/integrity only when its key/authority lifecycle
  and ratification linkage are also trusted; it cannot by itself prove owner
  approval.
- Only ratified, effective policy may load. Draft, missing, malformed,
  incomplete, superseded, or ambiguous policy must deny policy-dependent
  decisions. Do not fill missing rules with permissive defaults.
- The policy object, verified metadata, policy version, and facts used for a
  decision must be bound to one immutable snapshot or equivalent consistency
  boundary. The evaluator must receive the exact loaded rules; metadata must
  describe those rules, not a separately queried label.
- Rollback must be an explicit, authorized policy action with a durable
  record. Reject older versions unless that precise rollback is authorized
  under the ratified policy-governance process. Do not infer “latest” based
  only on lexical version ordering or accept a rollback requested by a
  caller.
- A loading, integrity, provenance, ratification, version-consistency, or
  rollback check failure must block the protected effect and produce a
  security diagnostic without exposing sensitive policy contents.

No cryptographic scheme, key management, publication authority, or rollback
rule is selected here. These owner-authority and security-design decisions
must be resolved before implementation. The existing
[`PolicyVersion`](./src/scientia/authorization_boundary.py#L60) and equality
check are metadata consistency checks, not any of the protections above.

## 5. Service enforcement and unavailable operations

Authorization must be enforced by the service that owns the data or side
effect. A route-level check alone is insufficient. Do not cache an allow
across actions, resources, tenants, sessions, policy versions, or state
changes. Bind every decision to principal, tenant/workspace, resource,
action, policy snapshot, and the relevant authorization-state version.

| Operation | Required authorization point and revalidation | Current availability |
|---|---|---|
| **Sensitive reads** | Resolve ownership in a tenant-scoped query; evaluate before data access; revalidate before releasing content. For streaming, recheck before stream start and at defined safe chunk boundaries if revocation during transfer is in scope. Never fetch via an unscoped object/cache path first. | No protected application read service exists. Confidential reads and reliance on grants must remain unavailable. |
| **Writes and durable review commits** | Check before mutation and within the same transaction/snapshot as the commit where possible. Re-check membership, assignment, policy, and target version immediately before commit; reject stale/duplicate command submissions. | No authenticated write or review-commit service exists. Application-facing mutations must remain unavailable. |
| **High-stakes review** | Revalidate reviewer eligibility and resource/review state at submission and finalization. Enforce distinct canonical people, blind second submission, abstention/disagreement handling, and authorized adjudication only after corresponding policy is ratified. Never treat `HUMAN_REVIEWED` or `reviewer_label` as identity proof. | No independent-review workflow exists. High-stakes approval/finalization must remain unavailable. |
| **Exports** | Authorize the export action before data assembly and again immediately before releasing the artifact; scope source reads, destination, and artifact to the same principal/tenant/resource/policy snapshot. Delete incomplete output on denial/failure where safely possible. | No export service exists; current evaluator denies grant-backed export. Keep unavailable. |
| **Deletion** | Authorize the exact target and deletion semantics; revalidate ownership and policy inside the transaction immediately before irreversible commit. Audit the request/outcome without recording content. | No deletion service exists; current evaluator denies deletion. Keep unavailable. |
| **Queued jobs** | Bind a job to verified initiating principal, tenant, resource, action, policy version, and idempotency identity. Reauthenticate/validate delegated execution authority as designed; rehydrate and reauthorize immediately before execution and before each sensitive side effect. Cancel or safely stop on revocation, membership loss, policy invalidation, or resource change. | No queue or job lifecycle exists. Do not add queued protected operations before this control exists. |
| **Grants, assignments, elevation, audit reads** | Enforce approved issuer/approver authority, scope, duration, separation, lifecycle, revocation, and required durable audit. Revalidate at every consuming operation. Treat audit access as its own action and record access. | No lifecycle or audit service exists. Keep grant/assignment issuance and renewal, elevation, and application audit access disabled. |

For external effects that cannot share a database transaction, define an
equivalent consistency protocol, idempotency behavior, durable handoff, and
safe stop point before enabling the operation. An initial allow must not
outlive its relevant authorization facts.

## 6. Tenant isolation

Tenant isolation is end-to-end; filtering only the top-level resource query
does not suffice.

- **Database records:** include organization/workspace predicates in every
  read, update, delete, join, and background query. Avoid globally addressable
  records unless ownership is verified in the same trusted boundary. Check
  that the affected row still belongs to the authorized scope at commit.
- **Original files:** resolve file/object handles from a scoped resource
  record. Do not accept local paths or object-store keys as authority. Enforce
  tenant scope on retrieval and on any signed/temporary handle.
- **Parsed content and passages:** carry canonical source/resource ownership
  through ingestion and retrieval. Verify passage provenance and ownership
  before returning text or using it in synthesis. Do not infer tenant from
  document metadata supplied by the file.
- **Derived artifacts:** scope indexes, summaries, embeddings, exports, and
  intermediate results to their source resources and tenant. Recheck
  authorization before reuse or release; do not expose cross-tenant
  identifiers or content through errors.
- **Caches:** include tenant/workspace, principal or applicable sharing
  scope, resource, action, policy/state version, and sensitivity in keys and
  validity checks as appropriate. A cache hit may not bypass current
  authorization or revocation checks. Invalidate or revalidate on relevant
  changes.
- **Jobs:** persist initiating and target scope from trusted server context,
  not queue payload claims. Every worker lookup and side effect is scoped and
  reauthorized.
- **Audit records:** partition or filter by authorized tenant and restrict
  privileged cross-tenant audit access. Audit queries are separately
  authorized and themselves recorded. Do not put document content or secrets
  into searchable audit metadata.

The local workflow's PDF path and provenance checks do not implement any of
these application tenant controls
([`prepare_research`](./src/scientia/workflow.py#L101),
[`_validate_assessment_provenance`](./src/scientia/workflow.py#L159)).

## 7. Identity and session lifecycle

This plan does not choose an identity provider or define login, token, cookie,
or session implementation. Before integration, owners and implementers must
establish an explicit adapter contract covering:

- Credential purpose and validation, including issuer/audience/client
  expectations, expiry, revocation/introspection strategy where applicable,
  key rotation, clock behavior, and malformed/unavailable-provider handling.
- Construction of a request-scoped verified identity context only after
  successful authentication. A user ID, role, MFA flag, tenant ID, or
  provider label in a request cannot override it.
- MFA/assurance evidence and freshness requirements consistent with an
  owner-ratified policy. The current evaluator's boolean
  `Principal.mfa_verified` is caller-supplied data, not verification
  ([`Principal`](./src/scientia/authorization.py#L73)).
- Session renewal, expiry, logout/revocation, credential rotation, account
  disablement, and behavior when identity or membership services are
  unavailable. Protected operations deny when required state cannot be
  verified.
- Mapping external identities to a stable canonical subject and handling
  linked, duplicate, merged, or disabled accounts. U-7 remains open; distinct
  account identifiers do not prove distinct people.
- Reauthentication or renewed assurance at sensitive operations only where
  approved policy requires it; do not invent intervals.

Membership and role claims should be loaded from the authoritative SCIENTIA
membership source after authentication, not accepted from an identity token
without a separately ratified trust mapping. Authentication establishes who
presented a valid credential under the chosen contract; authorization
establishes what that principal may do now.

## 8. Audit boundaries

Audit design and deployment remain future work. The audit writer should record
only security-relevant metadata needed to establish who attempted which
action, against which scoped resource, under which decision/policy version,
and with what result. Candidate fields for design review include:

- server-generated event identifier and timestamp;
- authenticated canonical subject and issuer/session correlation reference
  in a suitably protected or pseudonymous form;
- tenant/workspace and resource identifiers, action, outcome, and non-sensitive
  failure category;
- policy version and authorization-state/version references that are
  traceable to verified sources;
- grant/assignment/review lifecycle actor, scope, reason reference, expiry,
  approval, revocation, and outcome where the ratified policy requires them;
- operation/job correlation and revalidation outcome, without copying
  credentials or job secrets.

Never record document text, extracted passages, full request bodies, access
tokens, passwords, secrets, private keys, or unrestricted policy contents in
the security audit event. Keep detailed failure diagnostics access-controlled
and redact sensitive values.

Restrict audit read/query to designated, authorized roles under ratified
policy, scope access by tenant and need, and record audit access. Separate
audit writing from ordinary application mutation paths and make required
audit persistence durable before success is reported. Define integrity,
availability, retention, deletion, legal hold, jurisdiction, and access
authority before implementation; this plan chooses no retention period,
jurisdiction, or security-personnel authority.

## 9. Dependency-ordered implementation roadmap

Engineering work may proceed only when its entry conditions are met. A stage
exit is necessary, not sufficient, to enable a capability; capability-specific
policy approval and operational review remain mandatory.

| Stage | Prerequisites and entry criteria | Deliverables | Measurable exit criteria | Blocking category |
|---|---|---|---|---|
| **0 — Hold and scope** | Immediate; current repository state. | Inventory protected operations and explicitly keep absent application paths unavailable. Record current evaluator behavior separately from policy status. | No route/service exposes a protected operation; all capabilities listed in §5 remain disabled; documentation says policy remains draft and Decisions 11–36 remain unverifiable. | Existing implementation limitation; no owner decision needed to preserve denial. |
| **1 — Ratify applicable policy** | Owner review of existing draft and authoritative evidence. | Versioned, owner-ratified policy with ratifier/date/version/amendments; complete role/action rules and action-specific requirements; resolve capability-specific U-1–U-8 and high-stakes rule provenance. Locate original Decisions 11–36 if available; otherwise preserve their status. | Each rule needed by the first intended capability has explicit authoritative wording and approval metadata; no numeric value or missing decision was inferred. | **Policy/owner authority.** U-2/U-3/U-4 durations; U-5/U-6 grant authority and separation; U-7 identity linkage; U-8 historical record; whole-policy ratification. |
| **2 — Approve identity/session contract** | Stage 1 policy rules relevant to identity/MFA and explicit owner decisions; no provider choice assumed. | Authentication adapter contract, verified identity-context semantics, session lifecycle and failure behavior, MFA evidence rules, canonical identity linkage process. | Tests prove forged caller identity/role/MFA/tenant fields cannot replace verified context; expired/revoked/invalid credentials and unavailable required identity state deny; U-7 rules are represented. | **Owner authority plus engineering.** Provider selection and assurance/identity-linking rules require decision; adapter implementation follows. |
| **3 — Establish provider composition and authoritative repositories** | Stage 2 contract and defined trust ownership; repository/data-store architecture selected through normal engineering review. | Controlled composition root; server-side membership, resource, assignment/grant and ownership lookups; tenant-scoped queries and access paths. | Startup fails on absent/ambiguous required providers; request data cannot select providers; integration tests cover each resource/storage layer and cross-tenant denial. | **Engineering**, with policy-dependent grant/assignment repositories gated on Stage 1 decisions. |
| **4 — Authoritative policy loading and binding** | Ratified policy and owner-authorized publication, integrity, supersession, and rollback process. | Policy publication/loading contract; integrity/provenance and ratification verification; explicit policy object/version bound to facts/evaluation; controlled rollback. | Missing, draft, tampered, superseded, inconsistent, or unauthorized-rollback policy denies. Tested decision metadata identifies the exact verified policy used. No version-label-only allow. | **Owner authority and security architecture** for publication/rollback; then engineering. |
| **5 — Operation service and consistency boundary** | Stages 1–4 complete for the intended action; persistence consistency semantics and data ownership defined. | Service-level authorize/operate interface; transaction or equivalent snapshot/revalidation; scoped access for DB, files, parsed/derived data, cache; safe streaming/job policy. | Each sensitive operation has authorization immediately before its side effect; integration/concurrency tests prove stale state, changed ownership, and revocation cannot pass the commit/release boundary. No direct bypass path. | **Engineering**, plus per-capability owner policy. |
| **6 — Audit and capability lifecycle** | Ratified audit authority, required event model, and unresolved retention/jurisdiction/security authority decisions resolved for the capability; stages 1–5. | Restricted durable audit writer/query service and only the explicitly approved grant, assignment, elevation, export, deletion, or review lifecycle needed. | Required audit write failure blocks the associated success/effect; access is authorized and recorded; actor/scope/expiry/revocation/separation rules tested. Content/secret exclusion verified. | **Owner authority** for retention, access, authority, and lifecycle; engineering afterward. |
| **7 — Independent verification and controlled enablement** | All previous applicable stages exited; target deployment configuration exists and is reviewed. | End-to-end threat-driven tests, operational monitoring/failure procedures, independent security review, per-capability enablement record. | Every test in §10 passes against assembled providers and persistence; reviewers document evidence and residual risks; enable only the individually accepted capability. Tests do not constitute certification. | **Engineering and independent review**, with continuing owner approval. |

No protected operation should be enabled by completing Stage 0 or by passing
unit tests. If any applicable stage regresses or an authoritative dependency
is unavailable, keep the affected capability disabled or deny.

## 10. Threat-driven verification plan

Test unit-level behavior, integration among actual adapters/providers and
repositories, and operation-boundary behavior. Synthetic unit tests alone
are not production-security evidence.

| Threat / test | Adversarial setup | Required result |
|---|---|---|
| **Spoofed identity or claims** | Caller submits a privileged user ID, role, tenant, `mfa_verified=true`, issuer, or policy label differing from verified session. | Only adapter-verified identity is used; caller claims are ignored or rejected; no protected data/effect occurs. |
| **Cross-tenant access** | Substitute organization/workspace/resource IDs, exploit an unscoped join/object key, or collide cache entries across tenants. | Scoped repository returns no foreign resource; files/passages/derived results/cache/job/audit paths disclose nothing cross-tenant. |
| **Policy tampering and rollback** | Alter policy content while retaining its label; serve an unratified draft, stale/superseded version, or unauthorized prior version; report inconsistent policy/facts versions. | Deny before the operation; no matching label or caller-selected rollback can bypass provenance/integrity checks. |
| **Stale authorization facts** | Cache prior membership, role, resource ownership, sensitivity, grant, or assignment after a change. | Revalidation detects state change before data release or durable effect; stale cache cannot authorize. |
| **Revoked membership or grant** | Revoke membership/grant after admission but before read release, commit, export, or job execution. | Operation denies or safely stops before next protected effect; no success-shaped response or artifact is released. |
| **Provider failure and malformed values** | Make identity, membership, resource, policy, clock, grant, or audit provider unavailable, throw, or return malformed/contradictory records. | Fail closed; no fallback to caller data, cached allow, default permissive policy, or success. Required audit failure blocks applicable completion. |
| **TOCTOU / concurrency** | Race authorization against role removal, resource transfer, policy change, expiry/revocation, transaction retry, or streaming/job side effects. | Transaction/version checks or immediate revalidation serialize or detect changes; no effect occurs using stale authorization. |
| **High-stakes review independence** | Reuse account aliases for one person; alter reviewer identity after first submission; submit a non-blind second review; revoke eligibility before finalization; trigger abstention/disagreement paths. | Canonical identity and independent-person rules are enforced; blind submissions and ratified abstention/adjudication rules apply; finalization revalidates and rejects unauthorized/stale reviewers. |
| **Action confusion and replay** | Reuse a read decision for write/export/delete, alter resource/action after authorization, or replay a mutation/review command. | Decision is bound to one principal/scope/resource/action/policy state; wrong-action reuse denies; idempotency prevents conflicting duplicate effects without bypassing fresh authorization. |
| **Audit disclosure/tampering** | Attempt cross-tenant audit queries, inject secrets/content into metadata, or modify/delete events through ordinary application roles. | Queries require separately authorized scope and are recorded; event schemas reject/redact prohibited content; unauthorized alteration is prevented/detected under approved controls. |

Acceptance requires evidence for all layers exercised: identity adapter,
composition root, policy loader, repository queries, caches/storage, service
side effects, and audit writer. Record the exact configuration and behavior
under test. Do not claim that the current synthetic tests validate these
future controls.

## 11. Explicit non-goals and unresolved decisions

### Non-goals

This plan does not implement or select:

- authentication, login/session handling, an identity provider, token
  contract, or MFA assurance level;
- API routes, service/persistence architecture, database, queue, object
  store, deployment model, or jurisdiction;
- grant issuance/approval/revocation, assignment lifecycle, administrator
  elevation, export, deletion, audit storage, or high-stakes review workflow;
- cryptographic policy-signing scheme, key management, rollback authority,
  audit retention period, or a new role/action permission;
- owner ratification, recovery of missing historical policy, or security
  certification.

### Unresolved owner decisions and fail-closed requirements

The policy draft's exact status remains **`DRAFT — PENDING OWNER RATIFICATION`**.
Decisions 11–36 remain **`NOT VERIFIABLE AS NUMBERED`** unless the original
authoritative source is found; do not reconstruct their text or numbering.
The following remain unresolved or unratified:

- Whole-policy ratifier, date, approved version, and amendment record.
- Formal ratification of A1, B2, U-1, duration-shape choices, F2, and other
  applicable selections.
- U-2 confidential-content grant maximum; U-3 separate elevation maximum;
  U-4 assignment default and maximum. No numeric values are supplied.
- U-5 who designates security personnel and their precise authority.
- U-6 issuer/approver separation of operational duties beyond distinct
  identities.
- U-7 canonical identity/account-linking evidence, duplicate-account
  treatment, and distinct-person proof.
- U-8 original authoritative Decisions 1–36 record and its approval and
  supersession provenance.
- Complete role/action matrix, action-specific assignment requirements, and
  high-stakes review rules confirmed in an authoritative ratified record.
- Identity-provider and MFA/session assurance decisions.
- Policy publication, integrity, supersession, and rollback authority.
- Audit access authority, retention, legal hold, and deployment jurisdiction.

Until applicable owner decisions and technical controls are complete, keep
protected reads/writes, confidential content, grants, assignments, elevation,
review finalization, exports, deletion, audit queries, and queued protected
work unavailable. The current facade is an internal evaluation seam only; it
must not be represented or used as a production security boundary.
