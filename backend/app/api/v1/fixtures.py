"""Demo Fixtures API Endpoint."""

from fastapi import APIRouter
from app.services.demo_fixtures import list_fixture_records, reset_fixtures, seed_fixtures_if_empty

router = APIRouter(prefix="/fixtures", tags=["Fixtures"])


@router.get("/records")
async def get_fixture_records():
    """Retrieve all records in the safe local fixture database."""
    await seed_fixtures_if_empty()
    records = await list_fixture_records()
    return {"count": len(records), "records": records}


@router.post("/reset")
async def reset_demo_fixtures():
    """Reset all demo fixture records to baseline pristine state."""
    records = await reset_fixtures()
    return {"status": "success", "message": "Demo fixtures reset to baseline", "records": records}
