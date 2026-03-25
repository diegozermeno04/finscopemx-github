from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_admin, get_current_user
from app.core.models import ETLRun, User
from app.core.schemas import (
    AdminRoleUpdateRequest,
    AdminUserResponse,
    ETLStatusResponse,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=List[AdminUserResponse])
async def list_users(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    users = result.scalars().all()

    return [
        AdminUserResponse(
            id=u.id,
            username=u.username,
            role=u.role,
            created_at=u.created_at,
            last_login=u.last_login,
        )
        for u in users
    ]


@router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
async def update_user_role(
    user_id: int,
    payload: AdminRoleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = payload.role
    await db.commit()
    await db.refresh(user)

    return AdminUserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.get("/etl/runs", response_model=List[ETLStatusResponse])
async def list_etl_runs(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(
        select(ETLRun)
        .order_by(ETLRun.started_at.desc())
        .limit(limit)
    )
    runs = result.scalars().all()

    return [
        ETLStatusResponse(
            id=r.id,
            run_type=r.run_type,
            status=r.status,
            tickers_processed=r.tickers_processed,
            rows_inserted=r.rows_inserted,
            rows_failed=r.rows_failed,
            started_at=r.started_at,
            completed_at=r.completed_at,
            error_log=r.error_log,
        )
        for r in runs
    ]


@router.post("/etl/trigger")
async def trigger_etl(
    run_type: str = "manual",
    years: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if run_type not in ("manual", "scheduled"):
        raise HTTPException(status_code=400, detail="Invalid run_type")

    from app.tasks.etl_tasks import run_full_etl
    task = run_full_etl.delay(years=years)

    return {"message": "ETL task queued", "task_id": task.id}
