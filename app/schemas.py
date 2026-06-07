from pydantic import BaseModel
from typing import List

# ===== Problem Schemas =====
class ProblemBase(BaseModel):
    title: str
    description: str
    difficulty: str
    sample_input: str = ""
    sample_output: str = ""
    hint: str = ""

class ProblemCreate(ProblemBase):
    pass

class Problem(ProblemBase):
    id: int

    class Config:
        orm_mode = True

# ===== Test Case Schemas =====
class TestCaseBase(BaseModel):
    input_data: str = ""
    expected_output: str
    is_hidden: bool = False

class TestCaseCreate(TestCaseBase):
    problem_id: int

class TestCase(TestCaseBase):
    id: int
    problem_id: int

    class Config:
        orm_mode = True

# ===== Submission Schemas =====
class SubmissionCreate(BaseModel):
    problem_id: int
    source_code: str
    language: str = "python"

class TestCaseResult(BaseModel):
    test_case_number: int
    input_data: str
    expected_output: str
    actual_output: str
    passed: bool
    error: str = ""

class SubmissionResult(BaseModel):
    status: str
    passed_cases: int
    total_cases: int
    results: List[TestCaseResult]
    explanation: str = ""

# ===== Code Run Schemas =====
class CodeRunRequest(BaseModel):
    source_code: str
    input_data: str = ""
    language: str = "python"

class CodeRunResult(BaseModel):
    success: bool
    output: str
    error: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserOut