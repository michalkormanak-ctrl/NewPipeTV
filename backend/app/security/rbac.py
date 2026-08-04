"""Role-based access control - princíp najmenších oprávnení (sekcia 16.2).

Pilot: zjednodušená verzia bez MFA/IAM federácie (viď docs/security.md,
známe obmedzenia). Produkcia: Cloud IAP / Identity Platform."""
from __future__ import annotations

from fastapi import Depends, HTTPException, Header, status

ROLES = (
    "citizen_readonly",
    "legislator",
    "constitutional_reviewer",
    "eu_law_reviewer",
    "data_protection_reviewer",
    "security_reviewer",
    "red_team_reviewer",
    "admin",
)


def get_current_user_roles(x_user_roles: str | None = Header(default=None)) -> list[str]:
    """Pilot placeholder: role sa čítajú z hlavičky nastavenej reverzným proxy
    po overení identity. V produkcii nahradiť overením JWT/IAP tokenu."""
    if not x_user_roles:
        return ["citizen_readonly"]
    return [r.strip() for r in x_user_roles.split(",") if r.strip() in ROLES]


def require_role(*allowed_roles: str):
    def dependency(roles: list[str] = Depends(get_current_user_roles)) -> list[str]:
        if "admin" in roles:
            return roles
        if not set(roles) & set(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Vyžaduje sa jedna z rolí: {allowed_roles}",
            )
        return roles

    return dependency
