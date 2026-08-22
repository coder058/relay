"""Policies API Endpoint."""

from fastapi import APIRouter
from app.core.policy_engine import policy_engine
from app.models.policy import PolicyConfig

router = APIRouter(prefix="/policy", tags=["Policy Engine"])


@router.get("", response_model=PolicyConfig)
async def get_policy():
    """Retrieve current security policy rules and budget ceilings."""
    return policy_engine.get_config()


@router.put("", response_model=PolicyConfig)
async def update_policy(config: PolicyConfig):
    """Update active security policy rules and budget configuration."""
    policy_engine.set_config(config)
    return policy_engine.get_config()
