from fastapi import HTTPException, status


ROLE_PERMISSIONS = {
    "user": {
        "prices:read",
        "rankings:read",
        "predictions:run",
        "predictions:history",
        "simulation:write",
        "simulation:read_own",
        "game:play",
        "game:leaderboard",
        "extended:read",
        "extended:request",
    },
    "admin": {
        "prices:read",
        "rankings:read",
        "predictions:run",
        "predictions:history",
        "simulation:write",
        "simulation:read_own",
        "simulation:read_all",
        "game:play",
        "game:leaderboard",
        "extended:read",
        "extended:request",
        "admin:users",
        "admin:etl",
        "admin:content",
    },
}


def require_permission(role: str, permission: str):
    allowed = ROLE_PERMISSIONS.get(role, set())
    if permission not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{role}' does not have permission '{permission}'",
        )
