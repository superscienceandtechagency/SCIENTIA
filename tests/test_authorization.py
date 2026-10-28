from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from scientia.authorization import (
    AccessGrant,
    Action,
    Assignment,
    AuthorizationContext,
    AuthorizationPolicy,
    AuthorizationReason,
    Membership,
    Principal,
    Resource,
    ResourceSensitivity,
    Role,
    authorize,
)

NOW = datetime(2026, 10, 13, 12, tzinfo=UTC)
ORG = "org-a"
WORKSPACE = "workspace-a"
RESOURCE_ID = "research-a"
SUBJECT = "user-a"
MAX_DURATION = timedelta(days=7)


def _context(
    *,
    roles=frozenset({Role.RESEARCHER}),
    action=Action.READ_RESEARCH,
    sensitivity=ResourceSensitivity.PUBLIC,
    active=True,
    principal_id=SUBJECT,
    membership_id=SUBJECT,
    organization_id=ORG,
    workspace_id=WORKSPACE,
    resource_organization_id=ORG,
    resource_workspace_id=WORKSPACE,
    resource_id=RESOURCE_ID,
    assignment=None,
    grant=None,
    mfa_verified=True,
):
    return AuthorizationContext(
        principal=Principal(
            subject_id=principal_id,
            issuer="test-issuer",
            mfa_verified=mfa_verified,
        ),
        membership=Membership(
            subject_id=membership_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            roles=frozenset(roles),
            active=active,
        ),
        resource=Resource(
            resource_id=resource_id,
            organization_id=resource_organization_id,
            workspace_id=resource_workspace_id,
            sensitivity=sensitivity,
        ),
        action=action,
        evaluated_at=NOW,
        assignment=assignment,
        grant=grant,
    )


def _assignment(*, subject_id=SUBJECT, expires_at=NOW + timedelta(days=2)):
    return Assignment(
        subject_id=subject_id,
        organization_id=ORG,
        workspace_id=WORKSPACE,
        resource_id=RESOURCE_ID,
        assigned_at=NOW - timedelta(hours=1),
        expires_at=expires_at,
    )


def _grant(action, *, subject_id=SUBJECT, expires_at=NOW + timedelta(days=2)):
    return AccessGrant(
        subject_id=subject_id,
        organization_id=ORG,
        workspace_id=WORKSPACE,
        resource_id=RESOURCE_ID,
        action=action,
        granted_by="grantor",
        approved_by="approver",
        reason="Approved for this research task",
        issued_at=NOW - timedelta(hours=1),
        expires_at=expires_at,
    )


def _policy():
    return AuthorizationPolicy(
        maximum_assignment_duration=MAX_DURATION,
        maximum_grant_duration=MAX_DURATION,
    )


def test_research_lead_can_read_nonconfidential_workspace_research():
    decision = authorize(
        _context(roles={Role.RESEARCH_LEAD}),
    )

    assert decision.allowed is True
    assert decision.reason is AuthorizationReason.RESEARCH_LEAD_READ


def test_research_lead_cannot_read_confidential_research_by_default():
    decision = authorize(
        _context(
            roles={Role.RESEARCH_LEAD},
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
        ),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.GRANT_REQUIRED


def test_researcher_can_read_only_an_explicit_active_assignment():
    decision = authorize(
        _context(assignment=_assignment()),
        policy=_policy(),
    )

    assert decision.allowed is True
    assert decision.reason is AuthorizationReason.ASSIGNED_RESEARCH


def test_researcher_without_assignment_is_denied():
    decision = authorize(_context())

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.ASSIGNMENT_REQUIRED


def test_reviewer_can_submit_review_only_for_assigned_research():
    decision = authorize(
        _context(
            roles={Role.REVIEWER},
            action=Action.SUBMIT_REVIEW,
            assignment=_assignment(),
        ),
        policy=_policy(),
    )

    assert decision.allowed is True
    assert decision.reason is AuthorizationReason.ASSIGNED_RESEARCH


def test_workspace_membership_does_not_imply_reviewer_assignment():
    decision = authorize(
        _context(
            roles={Role.REVIEWER},
            action=Action.SUBMIT_REVIEW,
        ),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.ASSIGNMENT_REQUIRED


@pytest.mark.parametrize(
    "assignment",
    [
        _assignment(subject_id="different-user"),
        replace(_assignment(), organization_id="different-org"),
        replace(_assignment(), workspace_id="different-workspace"),
        replace(_assignment(), resource_id="different-research"),
    ],
)
def test_assignment_must_match_principal_and_full_resource_scope(assignment):
    decision = authorize(
        _context(
            roles={Role.REVIEWER},
            action=Action.SUBMIT_REVIEW,
            assignment=assignment,
        ),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.ASSIGNMENT_SCOPE_MISMATCH


def test_organization_administrator_role_does_not_grant_confidential_read():
    decision = authorize(
        _context(
            roles={Role.ORGANIZATION_ADMINISTRATOR},
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
        ),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.GRANT_REQUIRED


def test_confidential_read_grant_does_not_authorize_export():
    decision = authorize(
        _context(
            roles={Role.ORGANIZATION_ADMINISTRATOR},
            action=Action.EXPORT_RESEARCH,
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            grant=_grant(Action.READ_RESEARCH),
        ),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.GRANT_SCOPE_MISMATCH


@pytest.mark.parametrize(
    "action",
    [
        Action.WRITE_RESEARCH,
        Action.SUBMIT_REVIEW,
        Action.DELETE_RESEARCH,
        Action.READ_AUDIT_METADATA,
    ],
)
def test_read_grant_does_not_authorize_other_permissions(action):
    decision = authorize(
        _context(
            roles={Role.ORGANIZATION_ADMINISTRATOR},
            action=action,
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            grant=_grant(Action.READ_RESEARCH),
        ),
        policy=_policy(),
    )

    assert decision.allowed is False


@pytest.mark.parametrize(
    "grant",
    [
        replace(_grant(Action.READ_RESEARCH), subject_id="different-user"),
        replace(_grant(Action.READ_RESEARCH), organization_id="different-org"),
        replace(_grant(Action.READ_RESEARCH), workspace_id="different-workspace"),
        replace(_grant(Action.READ_RESEARCH), resource_id="different-research"),
    ],
)
def test_grant_must_match_principal_and_full_resource_scope(grant):
    decision = authorize(
        _context(
            roles={Role.ORGANIZATION_ADMINISTRATOR},
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            grant=grant,
        ),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.GRANT_SCOPE_MISMATCH


def test_confidential_read_grant_does_not_replace_base_role_or_assignment():
    decision = authorize(
        _context(
            roles={Role.ORGANIZATION_ADMINISTRATOR},
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            grant=_grant(Action.READ_RESEARCH),
        ),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.PERMISSION_REQUIRED


def test_confidential_read_grant_allows_read_with_role_and_assignment():
    decision = authorize(
        _context(
            roles={Role.RESEARCHER},
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            assignment=_assignment(),
            grant=_grant(Action.READ_RESEARCH),
        ),
        policy=_policy(),
    )

    assert decision.allowed is True
    assert decision.reason is AuthorizationReason.EXPLICIT_GRANT


def test_confidential_read_grant_does_not_replace_missing_assignment():
    decision = authorize(
        _context(
            roles={Role.RESEARCHER},
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            grant=_grant(Action.READ_RESEARCH),
        ),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.ASSIGNMENT_REQUIRED


def test_confidential_assignment_without_grant_does_not_allow_read():
    decision = authorize(
        _context(
            roles={Role.RESEARCHER},
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            assignment=_assignment(),
        ),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.GRANT_REQUIRED


@pytest.mark.parametrize(
    ("action", "roles"),
    [
        (Action.WRITE_RESEARCH, {Role.RESEARCHER}),
        (Action.EXPORT_RESEARCH, {Role.RESEARCHER}),
        (Action.WRITE_RESEARCH, {Role.ORGANIZATION_ADMINISTRATOR}),
        (Action.EXPORT_RESEARCH, {Role.ORGANIZATION_ADMINISTRATOR}),
    ],
)
def test_grant_does_not_authorize_action_without_base_role_permission(action, roles):
    decision = authorize(
        _context(
            roles=roles,
            action=action,
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            grant=_grant(action),
        ),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.PERMISSION_REQUIRED


@pytest.mark.parametrize(
    ("resource_organization_id", "resource_workspace_id", "sensitivity"),
    [
        ("org-b", WORKSPACE, ResourceSensitivity.PUBLIC),
        (ORG, "workspace-b", ResourceSensitivity.PUBLIC),
        ("org-b", "workspace-b", ResourceSensitivity.PUBLIC),
    ],
)
def test_public_resources_remain_tenant_and_workspace_scoped(
    resource_organization_id, resource_workspace_id, sensitivity
):
    decision = authorize(
        _context(
            roles={Role.RESEARCH_LEAD},
            resource_organization_id=resource_organization_id,
            resource_workspace_id=resource_workspace_id,
            sensitivity=sensitivity,
        ),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.RESOURCE_SCOPE_MISMATCH


def test_inactive_membership_is_denied():
    decision = authorize(_context(roles={Role.RESEARCH_LEAD}, active=False))

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.INACTIVE_MEMBERSHIP


def test_principal_and_membership_subject_must_match():
    decision = authorize(
        _context(
            roles={Role.RESEARCH_LEAD},
            principal_id="user-a",
            membership_id="user-b",
        ),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.PRINCIPAL_MISMATCH


def test_unknown_action_fails_closed():
    decision = authorize(_context(roles={Role.RESEARCH_LEAD}, action="impersonate"))

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.UNKNOWN_ACTION


def test_multirole_membership_does_not_bypass_confidential_access_rule():
    decision = authorize(
        _context(
            roles={
                Role.RESEARCH_LEAD,
                Role.ORGANIZATION_ADMINISTRATOR,
            },
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
        ),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.GRANT_REQUIRED


def test_administrator_role_does_not_cancel_separate_reviewer_assignment():
    decision = authorize(
        _context(
            roles={Role.ORGANIZATION_ADMINISTRATOR, Role.REVIEWER},
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            assignment=_assignment(),
        ),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.GRANT_REQUIRED


def test_research_lead_write_requires_a_separate_scoped_permission():
    decision = authorize(
        _context(
            roles={Role.RESEARCH_LEAD},
            action=Action.WRITE_RESEARCH,
        ),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.PERMISSION_REQUIRED


def test_explicit_write_grant_does_not_imply_export_permission():
    decision = authorize(
        _context(
            roles={Role.RESEARCH_LEAD},
            action=Action.EXPORT_RESEARCH,
            grant=_grant(Action.WRITE_RESEARCH),
        ),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.GRANT_SCOPE_MISMATCH


def test_audit_access_requires_security_auditor_role():
    decision = authorize(
        _context(
            roles={Role.ORGANIZATION_ADMINISTRATOR},
            action=Action.READ_AUDIT_METADATA,
        ),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.PERMISSION_REQUIRED


def test_security_auditor_can_read_scoped_audit_metadata():
    decision = authorize(
        _context(
            roles={Role.SECURITY_AUDITOR},
            action=Action.READ_AUDIT_METADATA,
        ),
    )

    assert decision.allowed is True
    assert decision.reason is AuthorizationReason.SECURITY_AUDITOR


@pytest.mark.parametrize(
    ("action", "roles"),
    [
        (Action.DELETE_RESEARCH, {Role.RESEARCH_LEAD}),
        (Action.ADMIN_ELEVATION, {Role.ORGANIZATION_ADMINISTRATOR}),
    ],
)
def test_undefined_sensitive_permissions_fail_closed(action, roles):
    decision = authorize(_context(roles=roles, action=action))

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.PERMISSION_REQUIRED


def test_missing_assignment_duration_policy_fails_closed():
    decision = authorize(
        _context(assignment=_assignment()),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.DURATION_POLICY_UNCONFIGURED


def test_assignment_exceeding_configured_maximum_is_denied():
    decision = authorize(
        _context(
            assignment=_assignment(expires_at=NOW + timedelta(days=8)),
        ),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.DURATION_EXCEEDS_MAXIMUM


def test_assignment_duration_uses_elapsed_time_across_dst_fallback():
    new_york = ZoneInfo("America/New_York")
    assignment = Assignment(
        subject_id=SUBJECT,
        organization_id=ORG,
        workspace_id=WORKSPACE,
        resource_id=RESOURCE_ID,
        assigned_at=datetime(2026, 11, 1, 0, 30, tzinfo=new_york),
        expires_at=datetime(2026, 11, 1, 1, 30, tzinfo=new_york, fold=1),
    )
    evaluated_at = datetime(2026, 11, 1, 0, 45, tzinfo=new_york)
    context = replace(
        _context(assignment=assignment),
        evaluated_at=evaluated_at,
    )
    policy = AuthorizationPolicy(
        maximum_assignment_duration=timedelta(minutes=90),
        maximum_grant_duration=MAX_DURATION,
    )

    decision = authorize(context, policy=policy)

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.DURATION_EXCEEDS_MAXIMUM


def test_grant_duration_uses_elapsed_time_across_dst_fallback():
    new_york = ZoneInfo("America/New_York")
    issued_at = datetime(2026, 11, 1, 0, 30, tzinfo=new_york)
    expires_at = datetime(2026, 11, 1, 1, 30, tzinfo=new_york, fold=1)
    evaluated_at = datetime(2026, 11, 1, 0, 45, tzinfo=new_york)
    assignment = Assignment(
        subject_id=SUBJECT,
        organization_id=ORG,
        workspace_id=WORKSPACE,
        resource_id=RESOURCE_ID,
        assigned_at=evaluated_at - timedelta(minutes=10),
        expires_at=evaluated_at + timedelta(minutes=20),
    )
    grant = AccessGrant(
        subject_id=SUBJECT,
        organization_id=ORG,
        workspace_id=WORKSPACE,
        resource_id=RESOURCE_ID,
        action=Action.READ_RESEARCH,
        granted_by="grantor",
        approved_by="approver",
        reason="Approved for this research task",
        issued_at=issued_at,
        expires_at=expires_at,
    )
    context = replace(
        _context(
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            assignment=assignment,
            grant=grant,
        ),
        evaluated_at=evaluated_at,
    )
    policy = AuthorizationPolicy(
        maximum_assignment_duration=MAX_DURATION,
        maximum_grant_duration=timedelta(minutes=90),
    )

    decision = authorize(context, policy=policy)

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.DURATION_EXCEEDS_MAXIMUM


def test_expired_assignment_is_denied():
    decision = authorize(
        _context(assignment=_assignment(expires_at=NOW)),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.ASSIGNMENT_EXPIRED


def test_assignment_expiry_at_exact_evaluation_instant_is_denied():
    decision = authorize(
        _context(assignment=_assignment(expires_at=NOW)),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.ASSIGNMENT_EXPIRED


def test_assignment_with_exactly_configured_maximum_duration_is_allowed():
    assignment = Assignment(
        subject_id=SUBJECT,
        organization_id=ORG,
        workspace_id=WORKSPACE,
        resource_id=RESOURCE_ID,
        assigned_at=NOW + timedelta(seconds=1) - MAX_DURATION,
        expires_at=NOW + timedelta(seconds=1),
    )
    decision = authorize(_context(assignment=assignment), policy=_policy())

    assert decision.allowed is True
    assert decision.reason is AuthorizationReason.ASSIGNED_RESEARCH


def test_assignment_scope_mismatch_is_denied():
    assignment = Assignment(
        subject_id=SUBJECT,
        organization_id=ORG,
        workspace_id=WORKSPACE,
        resource_id="different-research",
        assigned_at=NOW - timedelta(hours=1),
        expires_at=NOW + timedelta(days=2),
    )
    decision = authorize(
        _context(assignment=assignment),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.ASSIGNMENT_SCOPE_MISMATCH


def test_revoked_assignment_is_denied_at_revocation_instant():
    assignment = Assignment(
        subject_id=SUBJECT,
        organization_id=ORG,
        workspace_id=WORKSPACE,
        resource_id=RESOURCE_ID,
        assigned_at=NOW - timedelta(hours=1),
        expires_at=NOW + timedelta(days=2),
        revoked_at=NOW,
    )
    decision = authorize(_context(assignment=assignment), policy=_policy())

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.ASSIGNMENT_REVOKED


def test_future_assignment_is_not_active():
    assignment = Assignment(
        subject_id=SUBJECT,
        organization_id=ORG,
        workspace_id=WORKSPACE,
        resource_id=RESOURCE_ID,
        assigned_at=NOW + timedelta(hours=1),
        expires_at=NOW + timedelta(days=2),
    )
    decision = authorize(
        _context(assignment=assignment),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.ASSIGNMENT_NOT_ACTIVE


def test_missing_grant_duration_policy_fails_closed():
    decision = authorize(
        _context(
            roles={Role.ORGANIZATION_ADMINISTRATOR},
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            grant=_grant(Action.READ_RESEARCH),
        ),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.DURATION_POLICY_UNCONFIGURED


def test_grant_expiry_at_exact_evaluation_instant_is_denied():
    decision = authorize(
        _context(
            roles={Role.ORGANIZATION_ADMINISTRATOR},
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            grant=_grant(Action.READ_RESEARCH, expires_at=NOW),
        ),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.GRANT_EXPIRED


def test_confidential_read_grant_at_maximum_is_allowed_with_role_and_assignment():
    grant = AccessGrant(
        subject_id=SUBJECT,
        organization_id=ORG,
        workspace_id=WORKSPACE,
        resource_id=RESOURCE_ID,
        action=Action.READ_RESEARCH,
        granted_by="grantor",
        approved_by="approver",
        reason="Approved for this research task",
        issued_at=NOW + timedelta(seconds=1) - MAX_DURATION,
        expires_at=NOW + timedelta(seconds=1),
    )
    decision = authorize(
        _context(
            roles={Role.RESEARCHER},
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            assignment=_assignment(),
            grant=grant,
        ),
        policy=_policy(),
    )

    assert decision.allowed is True
    assert decision.reason is AuthorizationReason.EXPLICIT_GRANT


def test_revoked_grant_is_denied_at_revocation_instant():
    grant = AccessGrant(
        subject_id=SUBJECT,
        organization_id=ORG,
        workspace_id=WORKSPACE,
        resource_id=RESOURCE_ID,
        action=Action.READ_RESEARCH,
        granted_by="grantor",
        approved_by="approver",
        reason="Approved for this research task",
        issued_at=NOW - timedelta(hours=1),
        expires_at=NOW + timedelta(days=2),
        revoked_at=NOW,
    )
    decision = authorize(
        _context(
            roles={Role.ORGANIZATION_ADMINISTRATOR},
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            grant=grant,
        ),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.GRANT_REVOKED


def test_grant_resource_scope_mismatch_is_denied():
    grant = AccessGrant(
        subject_id=SUBJECT,
        organization_id=ORG,
        workspace_id=WORKSPACE,
        resource_id="different-research",
        action=Action.READ_RESEARCH,
        granted_by="grantor",
        approved_by="approver",
        reason="Approved for this research task",
        issued_at=NOW - timedelta(hours=1),
        expires_at=NOW + timedelta(days=2),
    )
    decision = authorize(
        _context(
            roles={Role.ORGANIZATION_ADMINISTRATOR},
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            grant=grant,
        ),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.GRANT_SCOPE_MISMATCH


def test_grant_exceeding_configured_maximum_is_denied():
    decision = authorize(
        _context(
            roles={Role.ORGANIZATION_ADMINISTRATOR},
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            grant=_grant(
                Action.READ_RESEARCH,
                expires_at=NOW + MAX_DURATION + timedelta(seconds=1),
            ),
        ),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.DURATION_EXCEEDS_MAXIMUM


def test_expiry_comparison_is_instant_based_across_timezones():
    local_now = NOW.astimezone(timezone(timedelta(hours=5, minutes=30)))
    assignment = Assignment(
        subject_id=SUBJECT,
        organization_id=ORG,
        workspace_id=WORKSPACE,
        resource_id=RESOURCE_ID,
        assigned_at=NOW - timedelta(hours=1),
        expires_at=local_now,
    )
    decision = authorize(
        _context(assignment=assignment),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.ASSIGNMENT_EXPIRED


def test_grant_with_blank_reason_is_rejected():
    with pytest.raises(ValueError, match="reason"):
        AccessGrant(
            subject_id=SUBJECT,
            organization_id=ORG,
            workspace_id=WORKSPACE,
            resource_id=RESOURCE_ID,
            action=Action.READ_RESEARCH,
            granted_by="grantor",
            approved_by="approver",
            reason=" ",
            issued_at=NOW - timedelta(hours=1),
            expires_at=NOW + timedelta(days=1),
        )


def test_grant_requires_independent_grantor_and_approver():
    grant = _grant(Action.READ_RESEARCH, subject_id=SUBJECT)
    context = _context(
        roles={Role.ORGANIZATION_ADMINISTRATOR},
        sensitivity=ResourceSensitivity.CONFIDENTIAL,
        grant=AccessGrant(
            subject_id=grant.subject_id,
            organization_id=grant.organization_id,
            workspace_id=grant.workspace_id,
            resource_id=grant.resource_id,
            action=grant.action,
            granted_by=SUBJECT,
            approved_by=SUBJECT,
            reason=grant.reason,
            issued_at=grant.issued_at,
            expires_at=grant.expires_at,
        ),
    )

    decision = authorize(context, policy=_policy())

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.GRANT_ACTOR_CONFLICT


def test_grant_approval_must_be_independent_from_grant_issuance():
    grant = _grant(Action.READ_RESEARCH)
    context = _context(
        roles={Role.ORGANIZATION_ADMINISTRATOR},
        sensitivity=ResourceSensitivity.CONFIDENTIAL,
        grant=AccessGrant(
            subject_id=grant.subject_id,
            organization_id=grant.organization_id,
            workspace_id=grant.workspace_id,
            resource_id=grant.resource_id,
            action=grant.action,
            granted_by="same-operator",
            approved_by="same-operator",
            reason=grant.reason,
            issued_at=grant.issued_at,
            expires_at=grant.expires_at,
        ),
    )

    decision = authorize(context, policy=_policy())

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.GRANT_ACTOR_CONFLICT


def test_future_grant_is_not_active():
    grant = AccessGrant(
        subject_id=SUBJECT,
        organization_id=ORG,
        workspace_id=WORKSPACE,
        resource_id=RESOURCE_ID,
        action=Action.READ_RESEARCH,
        granted_by="grantor",
        approved_by="approver",
        reason="Approved for this research task",
        issued_at=NOW + timedelta(hours=1),
        expires_at=NOW + timedelta(days=2),
    )
    decision = authorize(
        _context(
            roles={Role.ORGANIZATION_ADMINISTRATOR},
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            grant=grant,
        ),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.GRANT_NOT_ACTIVE


def test_reviewer_and_administrator_actions_require_mfa():
    decision = authorize(
        _context(
            roles={Role.REVIEWER},
            action=Action.SUBMIT_REVIEW,
            assignment=_assignment(),
            mfa_verified=False,
        ),
        policy=_policy(),
    )

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.MFA_REQUIRED


def test_authorization_inputs_and_decisions_are_immutable():
    context = _context(roles={Role.RESEARCH_LEAD})
    decision = authorize(context)

    with pytest.raises(FrozenInstanceError):
        context.action = Action.EXPORT_RESEARCH
    with pytest.raises(FrozenInstanceError):
        decision.allowed = False


@pytest.mark.parametrize(
    ("context", "policy"),
    [
        (None, _policy()),
        (_context(roles={Role.RESEARCH_LEAD}), None),
    ],
)
def test_missing_context_or_policy_fails_closed(context, policy):
    decision = authorize(context, policy=policy)

    assert decision.allowed is False
    assert decision.reason is AuthorizationReason.INVALID_CONTEXT


def test_denial_reason_is_stable_and_does_not_include_resource_identity():
    context = _context(
        roles={Role.RESEARCH_LEAD},
        resource_organization_id="other-org",
    )

    first = authorize(context)
    second = authorize(context)

    assert first == second
    assert first.reason is AuthorizationReason.RESOURCE_SCOPE_MISMATCH
    assert RESOURCE_ID not in first.reason.value
