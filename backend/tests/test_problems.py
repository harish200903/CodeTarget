import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.problem import Problem, Topic, DifficultyLevel
from app.models.company import Company


@pytest.mark.asyncio
async def test_list_topics(async_client: AsyncClient):
    response = await async_client.get("/api/v1/problems/topics")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_problems_and_filtering(async_client: AsyncClient, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    
    # List all problems
    res = await async_client.get("/api/v1/problems", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1

    # Filter by search
    search_res = await async_client.get("/api/v1/problems?search=Two Sum", headers=headers)
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert len(search_data["items"]) >= 1
    assert "Two Sum" in search_data["items"][0]["title"]

    # Filter by difficulty
    diff_res = await async_client.get("/api/v1/problems?difficulty=EASY", headers=headers)
    assert diff_res.status_code == 200
    diff_data = diff_res.json()
    assert all(p["difficulty"] == "EASY" for p in diff_data["items"])


@pytest.mark.asyncio
async def test_get_problem_detail_and_hidden_case_protection(async_client: AsyncClient, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    
    # Fetch details for two-sum
    res = await async_client.get("/api/v1/problems/two-sum", headers=headers)
    assert res.status_code == 200
    p = res.json()

    assert p["title"] == "Two Sum"
    assert p["slug"] == "two-sum"
    assert "description_markdown" in p
    assert "starter_code" in p
    assert "sample_test_cases" in p
    
    # CRITICAL: Verify hidden test cases and reference solution are NOT present in JSON response
    assert "hidden_test_cases" not in p
    assert "solution_editorial" not in p
    
    # All returned sample test cases must have is_sample == True
    for tc in p["sample_test_cases"]:
        assert tc["is_sample"] is True


@pytest.mark.asyncio
async def test_unlock_hints_flow(async_client: AsyncClient, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    
    # Get problem details
    p_res = await async_client.get("/api/v1/problems/two-sum", headers=headers)
    prob_id = p_res.json()["id"]

    # Unlock Hint 1
    h1_res = await async_client.post(f"/api/v1/problems/{prob_id}/hints/unlock", headers=headers)
    assert h1_res.status_code == 200
    h1 = h1_res.json()
    assert h1["step_number"] == 1

    # Unlock Hint 2
    h2_res = await async_client.post(f"/api/v1/problems/{prob_id}/hints/unlock", headers=headers)
    assert h2_res.status_code == 200
    h2 = h2_res.json()
    assert h2["step_number"] == 2

    # Unlock Hint 3
    h3_res = await async_client.post(f"/api/v1/problems/{prob_id}/hints/unlock", headers=headers)
    assert h3_res.status_code == 200
    h3 = h3_res.json()
    assert h3["step_number"] == 3

    # Attempting 4th hint should fail with 400 Bad Request
    h4_res = await async_client.post(f"/api/v1/problems/{prob_id}/hints/unlock", headers=headers)
    assert h4_res.status_code == 400


@pytest.mark.asyncio
async def test_bookmark_and_notes(async_client: AsyncClient, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    
    p_res = await async_client.get("/api/v1/problems/two-sum", headers=headers)
    prob_id = p_res.json()["id"]

    # Toggle bookmark
    bm_res = await async_client.patch(
        f"/api/v1/problems/{prob_id}/bookmark",
        json={"is_bookmarked": True},
        headers=headers
    )
    assert bm_res.status_code == 200
    assert bm_res.json()["is_bookmarked"] is True

    # Save notes
    notes_res = await async_client.patch(
        f"/api/v1/problems/{prob_id}/notes",
        json={"personal_notes": "Remember O(N) hash map solution!"},
        headers=headers
    )
    assert notes_res.status_code == 200
    assert notes_res.json()["personal_notes"] == "Remember O(N) hash map solution!"

    # Verify problem detail reflects updated notes and bookmark
    p_res_updated = await async_client.get("/api/v1/problems/two-sum", headers=headers)
    p_updated = p_res_updated.json()
    assert p_updated["is_bookmarked"] is True
    assert p_updated["personal_notes"] == "Remember O(N) hash map solution!"
