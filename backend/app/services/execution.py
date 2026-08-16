import asyncio
import httpx
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel
from app.core.config import settings
from app.models.submission import SubmissionStatus

# Language mapping for Judge0 API
JUDGE0_LANGUAGE_IDS = {
    "python": 71,  # Python 3.8.1
    "java": 62,    # Java OpenJDK 13.0.1
    "cpp": 54,     # C++ GCC 9.2.0
}

# Status mapping from Judge0 status IDs to CodeTarget internal statuses
JUDGE0_STATUS_MAP = {
    1: SubmissionStatus.QUEUED,
    2: SubmissionStatus.RUNNING,
    3: SubmissionStatus.ACCEPTED,
    4: SubmissionStatus.WRONG_ANSWER,
    5: SubmissionStatus.TIME_LIMIT_EXCEEDED,
    6: SubmissionStatus.COMPILE_ERROR,
    7: SubmissionStatus.RUNTIME_ERROR,  # SIGSEGV
    8: SubmissionStatus.RUNTIME_ERROR,  # SIGXFSZ
    9: SubmissionStatus.RUNTIME_ERROR,  # SIGFPE
    10: SubmissionStatus.RUNTIME_ERROR, # SIGABRT
    11: SubmissionStatus.RUNTIME_ERROR, # NZEC
    12: SubmissionStatus.RUNTIME_ERROR, # Other
    13: SubmissionStatus.SYSTEM_ERROR,  # Internal Error
    14: SubmissionStatus.MEMORY_LIMIT_EXCEEDED,
}


class SingleTestCaseResult(BaseModel):
    passed: bool
    input_data: str
    expected_output: str
    actual_output: str
    status: SubmissionStatus
    execution_time_ms: Optional[int] = None
    memory_kb: Optional[int] = None
    error_message: Optional[str] = None


class BatchExecutionResult(BaseModel):
    overall_status: SubmissionStatus
    passed_test_cases: int
    total_test_cases: int
    execution_time_ms: Optional[int] = None
    memory_kb: Optional[int] = None
    error_output: Optional[str] = None
    test_case_results: List[SingleTestCaseResult] = []


class ExecutionService(ABC):
    """Abstract interface for decoupled code execution backend."""
    
    @abstractmethod
    async def run_sample_test_cases(
        self, language: str, source_code: str, test_cases: List[Dict[str, str]]
    ) -> BatchExecutionResult:
        pass

    @abstractmethod
    async def execute_submission(
        self, language: str, source_code: str, test_cases: List[Dict[str, str]]
    ) -> BatchExecutionResult:
        pass


class Judge0ExecutionService(ExecutionService):
    """Judge0 API backend implementation for safe code execution."""

    def __init__(self, base_url: str = settings.JUDGE0_URL, api_key: str = settings.JUDGE0_API_KEY):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}
        if self.api_key:
            self.headers["X-Auth-Token"] = self.api_key

    def _get_judge0_language_id(self, language: str) -> int:
        lang_id = JUDGE0_LANGUAGE_IDS.get(language.lower())
        if not lang_id:
            raise ValueError(f"Unsupported programming language: {language}")
        return lang_id

    async def _execute_single_test_case(
        self, client: httpx.AsyncClient, lang_id: int, source_code: str, input_data: str, expected_output: str
    ) -> SingleTestCaseResult:
        payload = {
            "language_id": lang_id,
            "source_code": source_code,
            "stdin": input_data,
            "expected_output": expected_output
        }
        
        try:
            # Submit to Judge0 (wait=true for fast synchronous response)
            url = f"{self.base_url}/submissions?wait=true"
            response = await client.post(url, json=payload, headers=self.headers, timeout=10.0)
            
            if response.status_code not in (200, 201):
                return SingleTestCaseResult(
                    passed=False,
                    input_data=input_data,
                    expected_output=expected_output,
                    actual_output="",
                    status=SubmissionStatus.SYSTEM_ERROR,
                    error_message="The code execution service is temporarily unavailable. Your submission was not graded."
                )

            data = response.json()
            j0_status_id = data.get("status", {}).get("id", 13)
            internal_status = JUDGE0_STATUS_MAP.get(j0_status_id, SubmissionStatus.SYSTEM_ERROR)
            
            stdout = (data.get("stdout") or "").strip()
            stderr = (data.get("stderr") or "").strip()
            compile_output = (data.get("compile_output") or "").strip()

            error_msg = stderr or compile_output or data.get("status", {}).get("description")
            time_sec = float(data.get("time") or 0.0)
            time_ms = int(time_sec * 1000)
            memory_kb = int(data.get("memory") or 0)

            passed = (internal_status == SubmissionStatus.ACCEPTED) and (stdout == expected_output.strip())

            return SingleTestCaseResult(
                passed=passed,
                input_data=input_data,
                expected_output=expected_output.strip(),
                actual_output=stdout,
                status=internal_status,
                execution_time_ms=time_ms,
                memory_kb=memory_kb,
                error_message=error_msg if not passed else None
            )
        except Exception as e:
            return SingleTestCaseResult(
                passed=False,
                input_data=input_data,
                expected_output=expected_output.strip(),
                actual_output="",
                status=SubmissionStatus.SYSTEM_ERROR,
                error_message="The code execution service is temporarily unavailable. Your submission was not graded."
            )

    async def run_sample_test_cases(
        self, language: str, source_code: str, test_cases: List[Dict[str, str]]
    ) -> BatchExecutionResult:
        lang_id = self._get_judge0_language_id(language)
        results: List[SingleTestCaseResult] = []
        
        async with httpx.AsyncClient() as client:
            for tc in test_cases:
                res = await self._execute_single_test_case(
                    client, lang_id, source_code, tc["input_data"], tc["expected_output"]
                )
                results.append(res)

        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)
        
        # Determine overall status
        first_failure = next((r for r in results if not r.passed), None)
        overall_status = SubmissionStatus.ACCEPTED if passed_count == total_count else (first_failure.status if first_failure else SubmissionStatus.WRONG_ANSWER)
        max_time = max((r.execution_time_ms or 0 for r in results), default=0)
        max_mem = max((r.memory_kb or 0 for r in results), default=0)

        return BatchExecutionResult(
            overall_status=overall_status,
            passed_test_cases=passed_count,
            total_test_cases=total_count,
            execution_time_ms=max_time,
            memory_kb=max_mem,
            error_output=first_failure.error_message if first_failure else None,
            test_case_results=results
        )

    async def execute_submission(
        self, language: str, source_code: str, test_cases: List[Dict[str, str]]
    ) -> BatchExecutionResult:
        return await self.run_sample_test_cases(language, source_code, test_cases)


# Global ExecutionService Dependency Injector
def get_execution_service() -> ExecutionService:
    return Judge0ExecutionService()
