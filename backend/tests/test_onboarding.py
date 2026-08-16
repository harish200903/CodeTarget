import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_me_unauthenticated(async_client: AsyncClient):
    response = await async_client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_onboarding_and_profile_flow(async_client: AsyncClient):
    # 1. Register candidate
    reg_payload = {
        "full_name": "Onboarding Candidate",
        "email": "onboarding@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }
    reg_res = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get /me (should have onboarding_completed = False)
    me_res = await async_client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["onboarding_completed"] is False

    # 3. Get list of companies
    comp_res = await async_client.get("/api/v1/companies")
    assert comp_res.status_code == 200
    companies = comp_res.json()
    assert len(companies) >= 1

    company_ids = [c["id"] for c in companies[:3]]
    primary_id = company_ids[0]

    # 4. Perform Onboarding
    onboarding_payload = {
        "target_company_ids": company_ids,
        "primary_company_id": primary_id,
        "preferred_language": "python",
        "skill_level": "INTERMEDIATE",
        "daily_goal_minutes": 45
    }
    onboard_res = await async_client.patch("/api/v1/users/onboarding", json=onboarding_payload, headers=headers)
    assert onboard_res.status_code == 200
    onboard_data = onboard_res.json()
    assert onboard_data["onboarding_completed"] is True
    assert onboard_data["preferred_language"] == "python"
    assert onboard_data["skill_level"] == "INTERMEDIATE"
    assert onboard_data["daily_goal_minutes"] == 45
    assert len(onboard_data["target_companies"]) == 3

    # Verify primary company priority = 1
    primary_targets = [tc for tc in onboard_data["target_companies"] if tc["priority"] == 1]
    assert len(primary_targets) == 1
    assert primary_targets[0]["company_id"] == primary_id


@pytest.mark.asyncio
async def test_onboarding_validation_rules(async_client: AsyncClient):
    # Register & get token
    reg_payload = {
        "full_name": "Validation User",
        "email": "validation@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }
    reg_res = await async_client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    comp_res = await async_client.get("/api/v1/companies")
    valid_id = comp_res.json()[0]["id"]

    # Test invalid language
    bad_lang_payload = {
        "target_company_ids": [valid_id],
        "primary_company_id": valid_id,
        "preferred_language": "javascript",  # Not supported in v1
        "skill_level": "BEGINNER",
        "daily_goal_minutes": 30
    }
    res1 = await async_client.patch("/api/v1/users/onboarding", json=bad_lang_payload, headers=headers)
    assert res1.status_code == 422

    # Test primary company not in target_company_ids
    random_uuid = str(uuid.uuid4())
    bad_primary_payload = {
        "target_company_ids": [valid_id],
        "primary_company_id": random_uuid,
        "preferred_language": "python",
        "skill_level": "BEGINNER",
        "daily_goal_minutes": 30
    }
    res2 = await async_client.patch("/api/v1/users/onboarding", json=bad_primary_payload, headers=headers)
    assert res2.status_code == 422
