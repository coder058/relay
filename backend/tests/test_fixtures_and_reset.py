"""Tests for Safe Local Demo Fixture mutations and resets."""

import pytest
from app.services.demo_fixtures import (
    create_fixture_record,
    delete_fixture_record,
    get_fixture_record,
    list_fixture_records,
    reset_fixtures,
)


@pytest.mark.asyncio
async def test_fixture_lifecycle_and_reset():
    # 1. Start with initial records
    records = await reset_fixtures()
    initial_count = len(records)
    assert initial_count > 0

    # 2. Mutate fixture (delete one record)
    await delete_fixture_record("CUST-1001")
    after_del = await list_fixture_records()
    assert len(after_del) == initial_count - 1
    assert await get_fixture_record("CUST-1001") is None

    # 3. Add a new temporary record
    await create_fixture_record(
        customer_id="CUST-9999",
        name="Temp Person",
        email="temp@example.com",
    )
    assert await get_fixture_record("CUST-9999") is not None

    # 4. Reset fixture back to pristine baseline
    restored = await reset_fixtures()
    assert len(restored) == initial_count
    assert await get_fixture_record("CUST-1001") is not None
    assert await get_fixture_record("CUST-9999") is None
