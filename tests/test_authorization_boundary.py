from dataclasses import replace
from datetime import UTC, datetime, timedelta, tzinfo

import pytest

import scientia.authorization_boundary as authorization_boundary_module
from scientia.authorization import (
    AccessGrant,
    Action,
    Assignment,
    AuthorizationContext,
    AuthorizationDecision,
    AuthorizationReason,
    Membership,
    Principal,
    Resource,
    ResourceSensitivity,
    Role,
)
from scientia.authorization_boundary import (
    AuthorizationBoundary,
    AuthorizationBoundaryResult,
    BoundaryFailure,
    LoadedAuthorizationFacts,
    PolicyVersion,
    ResourceSelector,
)

NOW = datetime(2026, 10, 17, 12, tzinfo=UTC)
ORG = "org-a"
WORKSPACE = "workspace-a"
RESOURCE_ID = "research-a"
SUBJECT = "user-a"


class FixedClock:
    def __init__(self, value):
        self.value = value

    def now(self):
        return self.value


class FixedPolicyVersionSource:
    def __init__(self, value):
        self.value = value

    def current_version(self):
        return self.value


class FixedFactsSource:
    def __init__(self, context):
        self.context = context
        self.calls = []

    def load(self, selector, action, *, evaluated_at, policy_version):
        self.calls.append((selector, action, evaluated_at, policy_version))
        if isinstance(self.context, AuthorizationContext):
            return LoadedAuthorizationFacts(self.context, policy_version)
        return self.context


def _selector():
    return ResourceSelector(ORG, WORKSPACE, RESOURCE_ID)


def _context(
    *,
    roles=frozenset({Role.RESEARCHER}),
    action=Action.READ_RESEARCH,
    sensitivity=ResourceSensitivity.PUBLIC,
    assignment=None,
    grant=None,
    evaluated_at=NOW,
):
    return AuthorizationContext(
        principal=Principal(SUBJECT, "test-issuer", True),
        membership=Membership(
            SUBJECT,
            ORG,
            WORKSPACE,
            frozenset(roles),
            True,
        ),
        resource=Resource(
            RESOURCE_ID,
            ORG,
            WORKSPACE,
            sensitivity,
        ),
        action=action,
        evaluated_at=evaluated_at,
        assignment=assignment,
        grant=grant,
    )


def _assignment(*, expires_at=NOW + timedelta(days=1)):
    return Assignment(
        SUBJECT,
        ORG,
        WORKSPACE,
        RESOURCE_ID,
        NOW - timedelta(hours=1),
        expires_at,
    )


def _grant(action=Action.READ_RESEARCH):
    return AccessGrant(
        SUBJECT,
        ORG,
        WORKSPACE,
        RESOURCE_ID,
        action,
        "issuer",
        "approver",
        "synthetic test fact",
        NOW - timedelta(hours=1),
        NOW + timedelta(days=1),
    )


def _boundary(context, *, now=NOW, policy_version=None):
    facts = FixedFactsSource(context)
    boundary = AuthorizationBoundary(
        facts_source=facts,
        clock=FixedClock(now),
        policy_version_source=FixedPolicyVersionSource(
            policy_version or PolicyVersion("test-version")
        ),
    )
    return boundary, facts


def test_boundary_requires_a_policy_version_before_loading_facts():
    boundary, facts = _boundary(
        _context(roles={Role.RESEARCH_LEAD}),
        policy_version=None,
    )
    boundary = AuthorizationBoundary(
        facts_source=facts,
        clock=FixedClock(NOW),
        policy_version_source=FixedPolicyVersionSource(None),
    )

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization == AuthorizationDecision(
        False,
        AuthorizationReason.INVALID_CONTEXT,
    )
    assert facts.calls == []


@pytest.mark.parametrize(
    "now",
    [
        None,
        "2026-10-17T12:00:00Z",
        datetime(2026, 10, 17, 12),
    ],
)
def test_boundary_denies_missing_or_malformed_server_time(now):
    boundary, facts = _boundary(
        _context(roles={Role.RESEARCH_LEAD}),
        now=now,
    )

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is False
    assert result.authorization.reason is AuthorizationReason.INVALID_CONTEXT
    assert result.failure is BoundaryFailure.INVALID_EVALUATION_TIME
    assert facts.calls == []


def test_boundary_denies_when_clock_raises():
    boundary, facts = _boundary(_context(roles={Role.RESEARCH_LEAD}))

    class RaisingClock:
        def now(self):
            raise RuntimeError("clock unavailable")

    boundary = AuthorizationBoundary(
        facts_source=facts,
        clock=RaisingClock(),
        policy_version_source=FixedPolicyVersionSource(PolicyVersion("v1")),
    )

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is False
    assert result.authorization.reason is AuthorizationReason.INVALID_CONTEXT
    assert result.failure is BoundaryFailure.CLOCK_FAILURE
    assert facts.calls == []


def test_boundary_denies_when_clock_datetime_timezone_raises():
    class BrokenTimezone(tzinfo):
        def utcoffset(self, value):
            raise RuntimeError("timezone unavailable")

        def dst(self, value):
            return None

        def tzname(self, value):
            return "broken"

    broken_time = datetime(2026, 10, 17, 12, tzinfo=BrokenTimezone())
    boundary, facts = _boundary(
        _context(roles={Role.RESEARCH_LEAD}),
        now=broken_time,
    )

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is False
    assert result.authorization.reason is AuthorizationReason.INVALID_CONTEXT
    assert result.failure is BoundaryFailure.INVALID_EVALUATION_TIME
    assert facts.calls == []


def test_boundary_denies_when_policy_version_source_raises():
    boundary, facts = _boundary(_context(roles={Role.RESEARCH_LEAD}))

    class RaisingPolicyVersionSource:
        def current_version(self):
            raise RuntimeError("policy metadata unavailable")

    boundary = AuthorizationBoundary(
        facts_source=facts,
        clock=FixedClock(NOW),
        policy_version_source=RaisingPolicyVersionSource(),
    )

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is False
    assert result.authorization.reason is AuthorizationReason.INVALID_CONTEXT
    assert result.failure is BoundaryFailure.POLICY_VERSION_SOURCE_FAILURE
    assert facts.calls == []


def test_boundary_denies_when_facts_source_raises():
    boundary, _ = _boundary(_context(roles={Role.RESEARCH_LEAD}))

    class RaisingFactsSource:
        def load(self, selector, action, *, evaluated_at, policy_version):
            raise RuntimeError("facts unavailable")

    boundary = AuthorizationBoundary(
        facts_source=RaisingFactsSource(),
        clock=FixedClock(NOW),
        policy_version_source=FixedPolicyVersionSource(PolicyVersion("v1")),
    )

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is False
    assert result.authorization.reason is AuthorizationReason.INVALID_CONTEXT
    assert result.failure is BoundaryFailure.FACTS_SOURCE_FAILURE


def test_boundary_denies_missing_authorization_facts():
    boundary, _ = _boundary(None)

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is False
    assert result.authorization.reason is AuthorizationReason.INVALID_CONTEXT


def test_boundary_denies_a_non_context_facts_result():
    boundary, _ = _boundary({"principal": SUBJECT})

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is False
    assert result.authorization.reason is AuthorizationReason.INVALID_CONTEXT


def test_boundary_denies_corrupted_loaded_facts_without_raising():
    corrupted_facts = object.__new__(LoadedAuthorizationFacts)
    object.__setattr__(corrupted_facts, "context", None)
    object.__setattr__(
        corrupted_facts,
        "policy_version",
        PolicyVersion("test-version"),
    )
    boundary, _ = _boundary(corrupted_facts)

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is False
    assert result.authorization.reason is AuthorizationReason.INVALID_CONTEXT
    assert result.failure is BoundaryFailure.INVALID_FACTS


def test_boundary_denies_when_evaluator_raises(monkeypatch):
    boundary, _ = _boundary(_context(roles={Role.RESEARCH_LEAD}))

    def fail_evaluation(context):
        raise RuntimeError("evaluation failed")

    monkeypatch.setattr(authorization_boundary_module, "authorize", fail_evaluation)

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is False
    assert result.authorization.reason is AuthorizationReason.INVALID_CONTEXT
    assert result.failure is BoundaryFailure.EVALUATOR_FAILURE


def test_boundary_denies_when_evaluator_returns_invalid_value(monkeypatch):
    boundary, _ = _boundary(_context(roles={Role.RESEARCH_LEAD}))
    monkeypatch.setattr(
        authorization_boundary_module,
        "authorize",
        lambda context: None,
    )

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is False
    assert result.authorization.reason is AuthorizationReason.INVALID_CONTEXT
    assert result.failure is BoundaryFailure.INVALID_EVALUATOR_RESULT


@pytest.mark.parametrize(
    "decision",
    [
        AuthorizationDecision(True, AuthorizationReason.INVALID_CONTEXT),
        AuthorizationDecision("not-a-bool", AuthorizationReason.RESEARCH_LEAD_READ),
        AuthorizationDecision(False, AuthorizationReason.RESEARCH_LEAD_READ),
    ],
)
def test_boundary_denies_malformed_or_contradictory_evaluator_decision(
    monkeypatch,
    decision,
):
    boundary, _ = _boundary(_context(roles={Role.RESEARCH_LEAD}))
    monkeypatch.setattr(
        authorization_boundary_module,
        "authorize",
        lambda context: decision,
    )

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is False
    assert result.authorization.reason is AuthorizationReason.INVALID_CONTEXT
    assert result.failure is BoundaryFailure.INVALID_EVALUATOR_RESULT


def test_facts_result_binds_context_to_the_requested_policy_version():
    loaded_facts_type = getattr(
        authorization_boundary_module,
        "LoadedAuthorizationFacts",
        None,
    )
    assert loaded_facts_type is not None, (
        "facts result must carry the version used to load authorization facts"
    )

    requested_version = PolicyVersion("current-version")
    returned_version = PolicyVersion("stale-cached-version")
    context = _context(roles={Role.RESEARCH_LEAD})
    facts = FixedFactsSource(loaded_facts_type(context, returned_version))
    boundary = AuthorizationBoundary(
        facts_source=facts,
        clock=FixedClock(NOW),
        policy_version_source=FixedPolicyVersionSource(requested_version),
    )

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is False
    assert result.authorization.reason is AuthorizationReason.INVALID_CONTEXT
    assert result.failure is BoundaryFailure.POLICY_VERSION_MISMATCH


def test_boundary_denies_malformed_selector_and_action():
    boundary, facts = _boundary(_context(roles={Role.RESEARCH_LEAD}))

    malformed_selector = boundary.evaluate(
        {"organization_id": ORG, "workspace_id": WORKSPACE, "resource_id": RESOURCE_ID},
        Action.READ_RESEARCH,
    )
    malformed_action = boundary.evaluate(_selector(), "read_research")

    assert (
        malformed_selector.authorization.reason
        is AuthorizationReason.INVALID_CONTEXT
    )
    assert malformed_action.authorization.reason is AuthorizationReason.INVALID_CONTEXT
    assert facts.calls == []


def test_boundary_denies_malformed_policy_version_metadata():
    boundary, facts = _boundary(
        _context(roles={Role.RESEARCH_LEAD}),
        policy_version="version-from-untrusted-payload",
    )

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.reason is AuthorizationReason.INVALID_CONTEXT
    assert facts.calls == []


@pytest.mark.parametrize(
    "missing_dependency",
    ["facts_source", "clock", "policy_version_source"],
)
def test_boundary_rejects_missing_dependencies(missing_dependency):
    dependencies = {
        "facts_source": FixedFactsSource(_context(roles={Role.RESEARCH_LEAD})),
        "clock": FixedClock(NOW),
        "policy_version_source": FixedPolicyVersionSource(PolicyVersion("v1")),
    }
    dependencies[missing_dependency] = None

    with pytest.raises(TypeError):
        AuthorizationBoundary(**dependencies)


def test_boundary_rejects_provider_with_raising_method_attribute():
    class BrokenFactsSource:
        @property
        def load(self):
            raise RuntimeError("provider registration failed")

    with pytest.raises(TypeError, match="facts_source"):
        AuthorizationBoundary(
            facts_source=BrokenFactsSource(),
            clock=FixedClock(NOW),
            policy_version_source=FixedPolicyVersionSource(PolicyVersion("v1")),
        )


@pytest.mark.parametrize(
    "resource",
    [
        Resource("other-resource", ORG, WORKSPACE, ResourceSensitivity.PUBLIC),
        Resource(RESOURCE_ID, "other-org", WORKSPACE, ResourceSensitivity.PUBLIC),
        Resource(RESOURCE_ID, ORG, "other-workspace", ResourceSensitivity.PUBLIC),
    ],
)
def test_boundary_denies_facts_outside_the_untrusted_selector_scope(resource):
    context = _context(roles={Role.RESEARCH_LEAD})
    boundary, _ = _boundary(replace(context, resource=resource))

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is False
    assert result.authorization.reason is AuthorizationReason.INVALID_CONTEXT


def test_boundary_denies_facts_for_a_different_action():
    boundary, _ = _boundary(
        _context(roles={Role.RESEARCH_LEAD}, action=Action.EXPORT_RESEARCH)
    )

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is False
    assert result.authorization.reason is AuthorizationReason.INVALID_CONTEXT


def test_boundary_uses_server_time_instead_of_facts_source_time():
    context = _context(
        assignment=_assignment(expires_at=NOW - timedelta(seconds=1)),
        evaluated_at=NOW - timedelta(days=1),
    )
    boundary, facts = _boundary(context)

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is False
    assert result.authorization.reason is AuthorizationReason.ASSIGNMENT_EXPIRED
    assert result.evaluated_at == NOW
    assert facts.calls[0][2] == NOW


def test_boundary_preserves_policy_version_as_decision_metadata():
    version = PolicyVersion("metadata-version")
    boundary, facts = _boundary(
        _context(roles={Role.RESEARCH_LEAD}),
        policy_version=version,
    )

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is True
    assert result.policy_version is version
    assert facts.calls[0][3] is version


def test_boundary_does_not_accept_caller_supplied_principal_or_facts():
    boundary, _ = _boundary(_context(roles={Role.RESEARCH_LEAD}))

    with pytest.raises(TypeError):
        boundary.evaluate(
            _selector(),
            Action.READ_RESEARCH,
            principal=Principal(SUBJECT, "forged-issuer", True),
        )


def test_boundary_fails_closed_when_confidential_grant_duration_is_unconfigured():
    assignment = _assignment()
    grant = _grant()
    boundary, _ = _boundary(
        _context(
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            assignment=assignment,
            grant=grant,
        )
    )

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is False
    assert (
        result.authorization.reason
        is AuthorizationReason.DURATION_POLICY_UNCONFIGURED
    )


def test_boundary_denies_assignment_only_confidential_read():
    boundary, _ = _boundary(
        _context(
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            assignment=_assignment(),
        )
    )

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is False
    assert (
        result.authorization.reason
        is AuthorizationReason.DURATION_POLICY_UNCONFIGURED
    )


def test_boundary_denies_grant_only_confidential_read():
    boundary, _ = _boundary(
        _context(
            roles={Role.ORGANIZATION_ADMINISTRATOR},
            sensitivity=ResourceSensitivity.CONFIDENTIAL,
            grant=_grant(),
        )
    )

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is False
    assert (
        result.authorization.reason
        is AuthorizationReason.DURATION_POLICY_UNCONFIGURED
    )


def test_boundary_denies_grant_backed_export():
    boundary, _ = _boundary(
        _context(
            roles={Role.RESEARCH_LEAD},
            action=Action.EXPORT_RESEARCH,
            grant=_grant(Action.EXPORT_RESEARCH),
        )
    )

    result = boundary.evaluate(_selector(), Action.EXPORT_RESEARCH)

    assert result.authorization.allowed is False
    assert (
        result.authorization.reason
        is AuthorizationReason.DURATION_POLICY_UNCONFIGURED
    )


def test_boundary_applies_pure_evaluator_for_policy_independent_public_read():
    boundary, _ = _boundary(_context(roles={Role.RESEARCH_LEAD}))

    result = boundary.evaluate(_selector(), Action.READ_RESEARCH)

    assert result.authorization.allowed is True
    assert result.authorization.reason is AuthorizationReason.RESEARCH_LEAD_READ


def test_resource_selector_rejects_blank_and_non_string_identifiers():
    with pytest.raises(ValueError):
        ResourceSelector(" ", WORKSPACE, RESOURCE_ID)
    with pytest.raises(TypeError):
        ResourceSelector(ORG, WORKSPACE, None)


def test_policy_version_rejects_blank_and_non_string_identifiers():
    with pytest.raises(ValueError):
        PolicyVersion(" ")
    with pytest.raises(TypeError):
        PolicyVersion(None)


def test_boundary_result_requires_aware_evaluation_time():
    with pytest.raises(ValueError):
        AuthorizationBoundaryResult(
            AuthorizationDecision(False, AuthorizationReason.INVALID_CONTEXT),
            datetime(2026, 10, 17, 12),
            None,
        )
