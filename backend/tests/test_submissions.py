import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from app.services.execution import BatchExecutionResult, SingleTestCaseResult
from app.models.submission import SubmissionStatus


@pytest.mark.asyncio
async def test_run_sample_code(async_client: AsyncClient, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    
    p_res = await async_client.get("/api/v1/problems/two-sum", headers=headers)
    prob_id = p_res.json()["id"]

    mock_batch_res = BatchExecutionResult(
        overall_status=SubmissionStatus.ACCEPTED,
        passed_test_cases=2,
        total_test_cases=2,
        execution_time_ms=15,
        memory_kb=1024,
        test_case_results=[
            SingleTestCaseResult(
                passed=True,
                input_data="[2,7,11,15]\n9",
                expected_output="[0, 1]",
                actual_output="[0, 1]",
                status=SubmissionStatus.ACCEPTED,
                execution_time_ms=15,
                memory_kb=1024
            )
        ]
    )

    with patch("app.services.execution.Judge0ExecutionService.run_sample_test_cases", new=AsyncMock(return_value=mock_batch_res)):
        res = await async_client.post(
            "/api/v1/submissions/run-sample",
            json={
                "problem_id": prob_id,
                "language": "python",
                "code": "def two_sum(nums, target):\n    return [0, 1]"
            },
            headers=headers
        )
        assert res.status_code == 200
        data = res.json()
        assert data["overall_status"] == "ACCEPTED"
        assert data["passed_test_cases"] == 2


@pytest.mark.asyncio
async def test_submit_solution_and_progress_update(async_client: AsyncClient, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    
    p_res = await async_client.get("/api/v1/problems/two-sum", headers=headers)
    prob_id = p_res.json()["id"]

    mock_batch_res = BatchExecutionResult(
        overall_status=SubmissionStatus.ACCEPTED,
        passed_test_cases=4,
        total_test_cases=4,
        execution_time_ms=22,
        memory_kb=2048
    )

    with patch("app.services.execution.Judge0ExecutionService.execute_submission", new=AsyncMock(return_value=mock_batch_res)):
        res = await async_client.post(
            "/api/v1/submissions/submit",
            json={
                "problem_id": prob_id,
                "language": "python",
                "code": "def two_sum(nums, target):\n    lookup = {}\n    for i, num in enumerate(nums):\n        diff = target - num\n        if diff in lookup:\n            return [lookup[diff], i]\n        lookup[num] = i\n    return []"
            },
            headers=headers
        )
        assert res.status_code == 200
        sub = res.json()
        assert sub["status"] == "ACCEPTED"
        assert sub["passed_test_cases"] == 4

    # Verify problem status is now SOLVED in problem catalog/detail
    p_detail = await async_client.get("/api/v1/problems/two-sum", headers=headers)
    assert p_detail.json()["user_status"] == "SOLVED"

    # Verify submission history endpoint
    hist_res = await async_client.get(f"/api/v1/submissions/problem/{prob_id}", headers=headers)
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert hist["total"] >= 1
    assert hist["items"][0]["status"] == "ACCEPTED"
