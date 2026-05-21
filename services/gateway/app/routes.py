"""Route table — maps URL prefixes to downstream service URLs and auth policy.

Per Plan §4.1:
  /api/v1/admin/*     -> admin-service        always auth required
  /api/v1/search/*    -> search-service       optional (token = 15% discount)
  /api/v1/bookings/*  -> booking-service      always auth required
  /api/v1/comments/*  -> comments-service     auth req for POST/DELETE only
  /api/v1/agent/*     -> ai-agent-service     optional (token = act as user)
"""
from __future__ import annotations

from dataclasses import dataclass

from app.config import settings


@dataclass(frozen=True)
class RouteRule:
    prefix: str
    target_base_url: str
    # HTTP methods that REQUIRE a valid Firebase token. {"*"} means all methods.
    auth_required_methods: frozenset[str]

    def applies_to(self, path: str) -> bool:
        return path.startswith(self.prefix)

    def requires_auth(self, method: str) -> bool:
        return "*" in self.auth_required_methods or method.upper() in self.auth_required_methods


# Order matters only when prefixes overlap — they don't here, so any order is fine.
# Prefixes are bare (no trailing slash) so they match both the bare endpoint
# (e.g. "/api/v1/search") and sub-paths ("/api/v1/search/hotels/{id}").
ROUTE_RULES: list[RouteRule] = [
    RouteRule(
        prefix="/api/v1/admin",
        target_base_url=settings.admin_service_url,
        auth_required_methods=frozenset({"*"}),
    ),
    RouteRule(
        prefix="/api/v1/search",
        target_base_url=settings.search_service_url,
        auth_required_methods=frozenset(),  # token optional (= 15% discount)
    ),
    RouteRule(
        prefix="/api/v1/bookings",
        target_base_url=settings.booking_service_url,
        auth_required_methods=frozenset({"*"}),
    ),
    RouteRule(
        prefix="/api/v1/comments",
        target_base_url=settings.comments_service_url,
        auth_required_methods=frozenset({"POST", "DELETE"}),
    ),
    RouteRule(
        prefix="/api/v1/agent",
        target_base_url=settings.agent_service_url,
        auth_required_methods=frozenset(),
    ),
]


def match_rule(path: str) -> RouteRule | None:
    for rule in ROUTE_RULES:
        if rule.applies_to(path):
            return rule
    return None
