"""Typed, non-authenticating interfaces for authorization evaluation.

This module is an internal seam, not an authentication or application
authorization service. Its facts source is a privileged in-process dependency
and must eventually be bound to verified authentication and authoritative
repositories. These Python types do not prove the provenance of their values.
No verified-principal value is introduced: without an authentication adapter,
a local wrapper could not establish identity or safely distinguish verified
claims from arbitrary ones.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
from typing import Protocol

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
    authorize,
)

_ALLOW_REASONS = frozenset(
    {
        AuthorizationReason.ASSIGNED_RESEARCH,
        AuthorizationReason.EXPLICIT_GRANT,
        AuthorizationReason.RESEARCH_LEAD_READ,
        AuthorizationReason.SECURITY_AUDITOR,
    }
)


@dataclass(frozen=True)
class ResourceSelector:
    """Untrusted identifiers used only to request a scoped resource lookup."""

    organization_id: str
    workspace_id: str
    resource_id: str

    def __post_init__(self) -> None:
        for name in ("organization_id", "workspace_id", "resource_id"):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string")
            if not value.strip():
                raise ValueError(f"{name} must not be blank")


@dataclass(frozen=True)
class PolicyVersion:
    """Opaque policy-version metadata, not evidence of ratification or trust."""

    identifier: str

    def __post_init__(self) -> None:
        if not isinstance(self.identifier, str):
            raise TypeError("identifier must be a string")
        if not self.identifier.strip():
            raise ValueError("identifier must not be blank")


class EvaluationClock(Protocol):
    """Internal source of server-controlled authorization time."""

    def now(self) -> datetime: ...


class PolicyVersionSource(Protocol):
    """Internal source of metadata for the current policy version."""

    def current_version(self) -> PolicyVersion | None: ...


class AuthorizationFactsSource(Protocol):
    """Request-scoped source of current principal and resource authorization facts.

    Implementations must be trusted internal dependencies bound to the
    authenticated request, not request-provided objects. This interface does
    not authenticate an identity or establish that returned facts are
    authoritative; no implementation is provided in this milestone.
    """

    def load(
        self,
        selector: ResourceSelector,
        action: Action,
        *,
        evaluated_at: datetime,
        policy_version: PolicyVersion,
    ) -> LoadedAuthorizationFacts | None: ...


class BoundaryFailure(str, Enum):
    """Non-sensitive diagnostic category for a fail-closed boundary result."""

    INVALID_REQUEST = "invalid_request"
    CLOCK_FAILURE = "clock_failure"
    INVALID_EVALUATION_TIME = "invalid_evaluation_time"
    POLICY_VERSION_SOURCE_FAILURE = "policy_version_source_failure"
    INVALID_POLICY_VERSION = "invalid_policy_version"
    FACTS_SOURCE_FAILURE = "facts_source_failure"
    INVALID_FACTS = "invalid_facts"
    POLICY_VERSION_MISMATCH = "policy_version_mismatch"
    SCOPE_OR_ACTION_MISMATCH = "scope_or_action_mismatch"
    EVALUATOR_FAILURE = "evaluator_failure"
    INVALID_EVALUATOR_RESULT = "invalid_evaluator_result"


@dataclass(frozen=True)
class LoadedAuthorizationFacts:
    """Facts returned with the metadata version requested for their lookup.

    Matching this label detects accidental stale-version results; it does not
    prove policy integrity, ratification, or provider trust.
    """

    context: AuthorizationContext
    policy_version: PolicyVersion

    def __post_init__(self) -> None:
        if not isinstance(self.context, AuthorizationContext):
            raise TypeError("context must be an AuthorizationContext")
        if not isinstance(self.policy_version, PolicyVersion):
            raise TypeError("policy_version must be a PolicyVersion")


@dataclass(frozen=True)
class AuthorizationBoundaryResult:
    """Evaluator result accompanied by the time and policy metadata used."""

    authorization: AuthorizationDecision
    evaluated_at: datetime | None
    policy_version: PolicyVersion | None
    failure: BoundaryFailure | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.authorization, AuthorizationDecision):
            raise TypeError("authorization must be an AuthorizationDecision")
        if self.evaluated_at is not None:
            _require_aware_datetime(self.evaluated_at)
        if self.policy_version is not None and not isinstance(
            self.policy_version, PolicyVersion
        ):
            raise TypeError("policy_version must be a PolicyVersion or None")
        if self.failure is not None and not isinstance(self.failure, BoundaryFailure):
            raise TypeError("failure must be a BoundaryFailure or None")


class AuthorizationBoundary:
    """Evaluate one scoped action using injected internal security sources.

    The boundary accepts only untrusted resource selectors and an action. It
    obtains time and policy metadata internally, requires server-loaded facts
    to match the selector and action, and overwrites their evaluation time.
    Evaluations use the kernel's default policy, so unresolved duration
    requirements remain denied. No operation is performed or enabled here.
    """

    def __init__(
        self,
        *,
        facts_source: AuthorizationFactsSource,
        clock: EvaluationClock,
        policy_version_source: PolicyVersionSource,
    ) -> None:
        if not _has_callable_method(facts_source, "load"):
            raise TypeError("facts_source must provide load()")
        if not _has_callable_method(clock, "now"):
            raise TypeError("clock must provide now()")
        if not _has_callable_method(policy_version_source, "current_version"):
            raise TypeError("policy_version_source must provide current_version()")
        self._facts_source = facts_source
        self._clock = clock
        self._policy_version_source = policy_version_source

    def evaluate(
        self,
        selector: ResourceSelector,
        action: Action,
    ) -> AuthorizationBoundaryResult:
        if type(selector) is not ResourceSelector or not isinstance(action, Action):
            return _deny(failure=BoundaryFailure.INVALID_REQUEST)

        try:
            evaluated_at = self._clock.now()
        except Exception:
            return _deny(failure=BoundaryFailure.CLOCK_FAILURE)
        if not _is_aware_datetime(evaluated_at):
            return _deny(failure=BoundaryFailure.INVALID_EVALUATION_TIME)

        try:
            policy_version = self._policy_version_source.current_version()
        except Exception:
            return _deny(
                evaluated_at=evaluated_at,
                failure=BoundaryFailure.POLICY_VERSION_SOURCE_FAILURE,
            )
        if not _is_valid_policy_version(policy_version):
            return _deny(
                evaluated_at=evaluated_at,
                failure=BoundaryFailure.INVALID_POLICY_VERSION,
            )

        try:
            loaded_facts = self._facts_source.load(
                selector,
                action,
                evaluated_at=evaluated_at,
                policy_version=policy_version,
            )
        except Exception:
            return _deny(
                evaluated_at=evaluated_at,
                policy_version=policy_version,
                failure=BoundaryFailure.FACTS_SOURCE_FAILURE,
            )
        if type(loaded_facts) is not LoadedAuthorizationFacts:
            return _deny(
                evaluated_at=evaluated_at,
                policy_version=policy_version,
                failure=BoundaryFailure.INVALID_FACTS,
            )
        try:
            context = loaded_facts.context
            loaded_policy_version = loaded_facts.policy_version
        except Exception:
            return _deny(
                evaluated_at=evaluated_at,
                policy_version=policy_version,
                failure=BoundaryFailure.INVALID_FACTS,
            )
        if type(loaded_policy_version) is not PolicyVersion:
            return _deny(
                evaluated_at=evaluated_at,
                policy_version=policy_version,
                failure=BoundaryFailure.INVALID_FACTS,
            )
        if loaded_policy_version != policy_version:
            return _deny(
                evaluated_at=evaluated_at,
                policy_version=policy_version,
                failure=BoundaryFailure.POLICY_VERSION_MISMATCH,
            )

        try:
            if not _is_valid_context_shape(context):
                return _deny(
                    evaluated_at=evaluated_at,
                    policy_version=policy_version,
                    failure=BoundaryFailure.INVALID_FACTS,
                )
            if context.action is not action or not _resource_matches_selector(
                context.resource,
                selector,
            ):
                return _deny(
                    evaluated_at=evaluated_at,
                    policy_version=policy_version,
                    failure=BoundaryFailure.SCOPE_OR_ACTION_MISMATCH,
                )
        except Exception:
            return _deny(
                evaluated_at=evaluated_at,
                policy_version=policy_version,
                failure=BoundaryFailure.INVALID_FACTS,
            )

        try:
            decision = authorize(
                _validated_context(context, evaluated_at=evaluated_at)
            )
        except Exception:
            return _deny(
                evaluated_at=evaluated_at,
                policy_version=policy_version,
                failure=BoundaryFailure.EVALUATOR_FAILURE,
            )
        if not _is_valid_decision(decision):
            return _deny(
                evaluated_at=evaluated_at,
                policy_version=policy_version,
                failure=BoundaryFailure.INVALID_EVALUATOR_RESULT,
            )
        return AuthorizationBoundaryResult(decision, evaluated_at, policy_version)


def _is_valid_policy_version(value: object) -> bool:
    try:
        return (
            type(value) is PolicyVersion
            and isinstance(value.identifier, str)
            and bool(value.identifier.strip())
        )
    except Exception:
        return False


def _is_valid_decision(value: object) -> bool:
    if (
        type(value) is not AuthorizationDecision
        or type(value.allowed) is not bool
        or type(value.reason) is not AuthorizationReason
    ):
        return False
    return (value.reason in _ALLOW_REASONS) is value.allowed


def _has_callable_method(value: object, name: str) -> bool:
    try:
        return callable(getattr(value, name, None))
    except Exception:
        return False


def _resource_matches_selector(
    resource: Resource,
    selector: ResourceSelector,
) -> bool:
    return (
        resource.resource_id == selector.resource_id
        and resource.organization_id == selector.organization_id
        and resource.workspace_id == selector.workspace_id
    )


def _is_valid_context_shape(context: object) -> bool:
    return (
        type(context) is AuthorizationContext
        and type(context.principal) is Principal
        and type(context.membership) is Membership
        and type(context.resource) is Resource
        and type(context.action) is Action
        and (
            context.assignment is None
            or type(context.assignment) is Assignment
        )
        and (context.grant is None or type(context.grant) is AccessGrant)
    )


def _validated_context(
    context: AuthorizationContext,
    *,
    evaluated_at: datetime,
) -> AuthorizationContext:
    return replace(
        context,
        principal=replace(context.principal),
        membership=replace(context.membership),
        resource=replace(context.resource),
        assignment=(
            replace(context.assignment)
            if context.assignment is not None
            else None
        ),
        grant=replace(context.grant) if context.grant is not None else None,
        evaluated_at=evaluated_at,
    )


def _is_aware_datetime(value: object) -> bool:
    try:
        return (
            isinstance(value, datetime)
            and value.tzinfo is not None
            and value.utcoffset() is not None
        )
    except Exception:
        return False


def _require_aware_datetime(value: datetime) -> None:
    if not _is_aware_datetime(value):
        raise ValueError("evaluated_at must be a timezone-aware datetime")


def _deny(
    *,
    evaluated_at: datetime | None = None,
    policy_version: PolicyVersion | None = None,
    failure: BoundaryFailure = BoundaryFailure.INVALID_FACTS,
) -> AuthorizationBoundaryResult:
    return AuthorizationBoundaryResult(
        AuthorizationDecision(False, AuthorizationReason.INVALID_CONTEXT),
        evaluated_at,
        policy_version,
        failure,
    )
