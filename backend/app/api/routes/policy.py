from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_superuser
from app.core.casbin import enforcer

router = APIRouter(tags=["Policy"], prefix="/policies")


class Policy(BaseModel):
    sub: str
    obj: str
    act: str


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[Policy],
    summary="Retrieve all policies",
)
def read_policies() -> Any:
    """
    Retrieve all policies.
    """
    # enforcer.get_policy() returns a list of lists: [['sub', 'obj', 'act'], ...]
    policies = enforcer.get_policy()
    return [Policy(sub=p[0], obj=p[1], act=p[2]) for p in policies]


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=bool, summary="Add a policy"
)
def add_policy(policy: Policy) -> Any:
    """
    Add a policy.
    """
    res = enforcer.add_policy(policy.sub, policy.obj, policy.act)
    return res


@router.delete(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=bool, summary="Remove a policy"
)
def remove_policy(policy: Policy) -> Any:
    """
    Remove a policy.
    """
    res = enforcer.remove_policy(policy.sub, policy.obj, policy.act)
    return res
