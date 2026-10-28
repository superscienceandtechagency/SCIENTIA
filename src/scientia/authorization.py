"""Pure, fail-closed authorization policy evaluation.

All identity and policy facts are supplied by a trusted caller. This module
does not authenticate identities, persist policy, or create assignments or
grants.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum


class Role(str, Enum):
    """Roles recognized by the limited authorization kernel."""

    RESEARCHER = "researcher"
    REVIEWER = "reviewer"
    RESEARCH_LEAD = "research_lead"
    HIGH_STAKES_APPROVER = "high_stakes_approver"
    ORGANIZATION_ADMINISTRATOR = "organization_administrator"
    SECURITY_AUDITOR = "security_auditor"


class Action(str, Enum):
    """Independently authorized operations understood by the kernel."""

    READ_RESEARCH = "read_research"
    WRITE_RESEARCH = "write_research"
    SUBMIT_REVIEW = "submit_review"
    EXPORT_RESEARCH = "export_research"
    DELETE_RESEARCH = "delete_research"
    READ_AUDIT_METADATA = "read_audit_metadata"
    ADMIN_ELEVATION = "admin_elevation"


class ResourceSensitivity(str, Enum):
    """Sensitivity label used for policy evaluation."""

    PUBLIC = "public"
    CONFIDENTIAL = "confidential"


class AuthorizationReason(str, Enum):
    """Stable reason categories returned by :func:`authorize`."""

    ASSIGNED_RESEARCH = "assigned_research"
    EXPLICIT_GRANT = "explicit_grant"
    GRANT_REQUIRED = "grant_required"
    GRANT_SCOPE_MISMATCH = "grant_scope_mismatch"
    GRANT_EXPIRED = "grant_expired"
    GRANT_NOT_ACTIVE = "grant_not_active"
    GRANT_REVOKED = "grant_revoked"
    GRANT_ACTOR_CONFLICT = "grant_actor_conflict"
    ASSIGNMENT_REQUIRED = "assignment_required"
    ASSIGNMENT_SCOPE_MISMATCH = "assignment_scope_mismatch"
    ASSIGNMENT_NOT_ACTIVE = "assignment_not_active"
    ASSIGNMENT_EXPIRED = "assignment_expired"
    ASSIGNMENT_REVOKED = "assignment_revoked"
    DURATION_POLICY_UNCONFIGURED = "duration_policy_unconfigured"
    DURATION_EXCEEDS_MAXIMUM = "duration_exceeds_maximum"
    INACTIVE_MEMBERSHIP = "inactive_membership"
    PRINCIPAL_MISMATCH = "principal_mismatch"
    RESOURCE_SCOPE_MISMATCH = "resource_scope_mismatch"
    MFA_REQUIRED = "mfa_required"
    PERMISSION_REQUIRED = "permission_required"
    RESEARCH_LEAD_READ = "research_lead_read"
    SECURITY_AUDITOR = "security_auditor"
    UNKNOWN_ACTION = "unknown_action"
    INVALID_CONTEXT = "invalid_context"


@dataclass(frozen=True)
class Principal:
    """Identity context asserted by a trusted caller, not authenticated here."""

    subject_id: str
    issuer: str
    mfa_verified: bool

    def __post_init__(self) -> None:
        _require_nonblank(self.subject_id, "subject_id")
        _require_nonblank(self.issuer, "issuer")
        if not isinstance(self.mfa_verified, bool):
            raise TypeError("mfa_verified must be a bool")


@dataclass(frozen=True)
class Membership:
    """Active role membership for one organization and workspace."""

    subject_id: str
    organization_id: str
    workspace_id: str
    roles: frozenset[Role]
    active: bool

    def __post_init__(self) -> None:
        _require_nonblank(self.subject_id, "subject_id")
        _require_nonblank(self.organization_id, "organization_id")
        _require_nonblank(self.workspace_id, "workspace_id")
        if not isinstance(self.roles, frozenset):
            raise TypeError("roles must be a frozenset")
        if any(not isinstance(role, Role) for role in self.roles):
            raise TypeError("roles must contain only Role values")
        if not isinstance(self.active, bool):
            raise TypeError("active must be a bool")


@dataclass(frozen=True)
class Resource:
    """Authoritative organization/workspace ownership and sensitivity facts."""

    resource_id: str
    organization_id: str
    workspace_id: str
    sensitivity: ResourceSensitivity

    def __post_init__(self) -> None:
        _require_nonblank(self.resource_id, "resource_id")
        _require_nonblank(self.organization_id, "organization_id")
        _require_nonblank(self.workspace_id, "workspace_id")
        if not isinstance(self.sensitivity, ResourceSensitivity):
            raise TypeError("sensitivity must be a ResourceSensitivity")


@dataclass(frozen=True)
class Assignment:
    """An existing assignment fact; this record does not create assignments."""

    subject_id: str
    organization_id: str
    workspace_id: str
    resource_id: str
    assigned_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "subject_id",
            "organization_id",
            "workspace_id",
            "resource_id",
        ):
            _require_nonblank(getattr(self, field_name), field_name)
        _require_aware_datetime(self.assigned_at, "assigned_at")
        _require_aware_datetime(self.expires_at, "expires_at")
        if _as_utc(self.expires_at) <= _as_utc(self.assigned_at):
            raise ValueError("expires_at must be after assigned_at")
        if self.revoked_at is not None:
            _require_aware_datetime(self.revoked_at, "revoked_at")


@dataclass(frozen=True)
class AccessGrant:
    """An existing, independently approved, single-action grant fact.

    Grant creation, approval, renewal, and revocation workflows are outside
    this module. The fact must include an expiry and explicit resource scope.
    """

    subject_id: str
    organization_id: str
    workspace_id: str
    resource_id: str
    action: Action
    granted_by: str
    approved_by: str
    reason: str
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "subject_id",
            "organization_id",
            "workspace_id",
            "resource_id",
            "granted_by",
            "approved_by",
        ):
            _require_nonblank(getattr(self, field_name), field_name)
        _require_nonblank(self.reason, "reason")
        if not isinstance(self.action, Action):
            raise TypeError("action must be an Action")
        _require_aware_datetime(self.issued_at, "issued_at")
        _require_aware_datetime(self.expires_at, "expires_at")
        if _as_utc(self.expires_at) <= _as_utc(self.issued_at):
            raise ValueError("expires_at must be after issued_at")
        if self.revoked_at is not None:
            _require_aware_datetime(self.revoked_at, "revoked_at")


@dataclass(frozen=True)
class AuthorizationContext:
    """All facts required for one independent authorization decision."""

    principal: Principal
    membership: Membership
    resource: Resource
    action: Action | str
    evaluated_at: datetime
    assignment: Assignment | None = None
    grant: AccessGrant | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.principal, Principal):
            raise TypeError("principal must be a Principal")
        if not isinstance(self.membership, Membership):
            raise TypeError("membership must be a Membership")
        if not isinstance(self.resource, Resource):
            raise TypeError("resource must be a Resource")
        if not isinstance(self.action, (Action, str)):
            raise TypeError("action must be an Action or string")
        _require_aware_datetime(self.evaluated_at, "evaluated_at")
        if self.assignment is not None and not isinstance(self.assignment, Assignment):
            raise TypeError("assignment must be an Assignment or None")
        if self.grant is not None and not isinstance(self.grant, AccessGrant):
            raise TypeError("grant must be an AccessGrant or None")


@dataclass(frozen=True)
class AuthorizationPolicy:
    """Approved duration bounds supplied by policy configuration.

    ``None`` means the relevant maximum has not been approved and therefore
    assignment- or grant-dependent authorization fails closed.
    """

    maximum_assignment_duration: timedelta | None = None
    maximum_grant_duration: timedelta | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "maximum_assignment_duration",
            "maximum_grant_duration",
        ):
            value = getattr(self, field_name)
            if value is not None and (
                not isinstance(value, timedelta) or value <= timedelta(0)
            ):
                raise ValueError(f"{field_name} must be a positive timedelta or None")


@dataclass(frozen=True)
class AuthorizationDecision:
    """Deterministic allow/deny result and stable reason category."""

    allowed: bool
    reason: AuthorizationReason


def authorize(
    context: AuthorizationContext | None,
    *,
    policy: AuthorizationPolicy = AuthorizationPolicy(),
) -> AuthorizationDecision:
    """Evaluate one action using only the supplied immutable policy facts.

    The evaluator does not authenticate the principal, verify that role or
    grant facts came from an authoritative store, or establish distinct-human
    identity. Callers must obtain all facts from trusted boundaries.
    """
    if not isinstance(context, AuthorizationContext) or not isinstance(
        policy, AuthorizationPolicy
    ):
        return _deny(AuthorizationReason.INVALID_CONTEXT)
    if not isinstance(context.action, Action):
        return _deny(AuthorizationReason.UNKNOWN_ACTION)

    principal = context.principal
    membership = context.membership
    resource = context.resource

    if principal.subject_id != membership.subject_id:
        return _deny(AuthorizationReason.PRINCIPAL_MISMATCH)
    if not membership.active:
        return _deny(AuthorizationReason.INACTIVE_MEMBERSHIP)
    if (
        membership.organization_id != resource.organization_id
        or membership.workspace_id != resource.workspace_id
    ):
        return _deny(AuthorizationReason.RESOURCE_SCOPE_MISMATCH)
    if membership.roles & {
        Role.REVIEWER,
        Role.HIGH_STAKES_APPROVER,
        Role.ORGANIZATION_ADMINISTRATOR,
    } and not principal.mfa_verified:
        return _deny(AuthorizationReason.MFA_REQUIRED)

    action = context.action
    roles = membership.roles

    if action is Action.READ_AUDIT_METADATA:
        if Role.SECURITY_AUDITOR in roles:
            return _allow(AuthorizationReason.SECURITY_AUDITOR)
        return _deny(AuthorizationReason.PERMISSION_REQUIRED)

    if action in {Action.DELETE_RESEARCH, Action.ADMIN_ELEVATION}:
        return _deny(AuthorizationReason.PERMISSION_REQUIRED)

    if action is Action.READ_RESEARCH:
        if context.grant is not None:
            grant_result = _validate_grant(context, policy)
            if grant_result is not None:
                return grant_result
            if context.grant.action is not action:
                return _deny(AuthorizationReason.GRANT_SCOPE_MISMATCH)

        if (
            Role.RESEARCH_LEAD in roles
            and resource.sensitivity is ResourceSensitivity.PUBLIC
        ):
            base_decision = _allow(AuthorizationReason.RESEARCH_LEAD_READ)
        elif roles & {Role.RESEARCHER, Role.REVIEWER}:
            base_decision = _validate_assignment(context, policy)
            if not base_decision.allowed:
                return base_decision
        elif (
            Role.ORGANIZATION_ADMINISTRATOR in roles
            or Role.RESEARCH_LEAD in roles
        ) and context.grant is None:
            return _deny(AuthorizationReason.GRANT_REQUIRED)
        else:
            return _deny(AuthorizationReason.PERMISSION_REQUIRED)

        if resource.sensitivity is ResourceSensitivity.CONFIDENTIAL:
            if context.grant is None:
                return _deny(AuthorizationReason.GRANT_REQUIRED)
            return _allow(AuthorizationReason.EXPLICIT_GRANT)
        if context.grant is not None:
            return _allow(AuthorizationReason.EXPLICIT_GRANT)
        return base_decision

    if action is Action.SUBMIT_REVIEW:
        if Role.REVIEWER not in roles:
            return _deny(AuthorizationReason.PERMISSION_REQUIRED)
        return _validate_assignment(context, policy)

    if action in {Action.WRITE_RESEARCH, Action.EXPORT_RESEARCH}:
        if context.grant is None:
            return _deny(AuthorizationReason.PERMISSION_REQUIRED)
        grant_result = _validate_grant(context, policy)
        if grant_result is not None:
            return grant_result
        if context.grant.action is not action:
            return _deny(AuthorizationReason.GRANT_SCOPE_MISMATCH)
        # No role-only permission path exists for these actions in this kernel.
        return _deny(AuthorizationReason.PERMISSION_REQUIRED)

    return _deny(AuthorizationReason.PERMISSION_REQUIRED)


def _validate_assignment(
    context: AuthorizationContext,
    policy: AuthorizationPolicy,
) -> AuthorizationDecision:
    assignment = context.assignment
    if assignment is None:
        return _deny(AuthorizationReason.ASSIGNMENT_REQUIRED)
    if (
        assignment.subject_id != context.principal.subject_id
        or assignment.organization_id != context.resource.organization_id
        or assignment.workspace_id != context.resource.workspace_id
        or assignment.resource_id != context.resource.resource_id
    ):
        return _deny(AuthorizationReason.ASSIGNMENT_SCOPE_MISMATCH)
    evaluated_at = _as_utc(context.evaluated_at)
    assigned_at = _as_utc(assignment.assigned_at)
    expires_at = _as_utc(assignment.expires_at)
    if assigned_at > evaluated_at:
        return _deny(AuthorizationReason.ASSIGNMENT_NOT_ACTIVE)
    if (
        assignment.revoked_at is not None
        and _as_utc(assignment.revoked_at) <= evaluated_at
    ):
        return _deny(AuthorizationReason.ASSIGNMENT_REVOKED)
    if expires_at <= evaluated_at:
        return _deny(AuthorizationReason.ASSIGNMENT_EXPIRED)
    maximum = policy.maximum_assignment_duration
    if maximum is None:
        return _deny(AuthorizationReason.DURATION_POLICY_UNCONFIGURED)
    if expires_at - assigned_at > maximum:
        return _deny(AuthorizationReason.DURATION_EXCEEDS_MAXIMUM)
    return _allow(AuthorizationReason.ASSIGNED_RESEARCH)


def _validate_grant(
    context: AuthorizationContext,
    policy: AuthorizationPolicy,
) -> AuthorizationDecision | None:
    grant = context.grant
    if grant is None:
        return _deny(AuthorizationReason.GRANT_REQUIRED)
    if (
        grant.subject_id != context.principal.subject_id
        or grant.organization_id != context.resource.organization_id
        or grant.workspace_id != context.resource.workspace_id
        or grant.resource_id != context.resource.resource_id
    ):
        return _deny(AuthorizationReason.GRANT_SCOPE_MISMATCH)
    if (
        grant.granted_by == grant.subject_id
        or grant.approved_by == grant.subject_id
        or grant.granted_by == grant.approved_by
    ):
        return _deny(AuthorizationReason.GRANT_ACTOR_CONFLICT)
    evaluated_at = _as_utc(context.evaluated_at)
    issued_at = _as_utc(grant.issued_at)
    expires_at = _as_utc(grant.expires_at)
    if issued_at > evaluated_at:
        return _deny(AuthorizationReason.GRANT_NOT_ACTIVE)
    if grant.revoked_at is not None and _as_utc(grant.revoked_at) <= evaluated_at:
        return _deny(AuthorizationReason.GRANT_REVOKED)
    if expires_at <= evaluated_at:
        return _deny(AuthorizationReason.GRANT_EXPIRED)
    maximum = policy.maximum_grant_duration
    if maximum is None:
        return _deny(AuthorizationReason.DURATION_POLICY_UNCONFIGURED)
    if expires_at - issued_at > maximum:
        return _deny(AuthorizationReason.DURATION_EXCEEDS_MAXIMUM)
    return None


def _as_utc(value: datetime) -> datetime:
    return value.astimezone(UTC)


def _require_nonblank(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def _require_aware_datetime(value: datetime, field_name: str) -> None:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _allow(reason: AuthorizationReason) -> AuthorizationDecision:
    return AuthorizationDecision(allowed=True, reason=reason)


def _deny(reason: AuthorizationReason) -> AuthorizationDecision:
    return AuthorizationDecision(allowed=False, reason=reason)
