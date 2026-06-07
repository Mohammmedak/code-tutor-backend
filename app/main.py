from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from .database import engine, SessionLocal
from . import models, schemas, crud, code_runner
from .explainer import explain_error
from .auth import verify_password, create_access_token, decode_access_token
from .seed_data import seed_problems
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Code Tutor API 🚀")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    seed_problems()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="غير مسجل دخول")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="توكن غير صالح")

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="توكن غير صالح أو منتهي")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="توكن غير صالح")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="المستخدم غير موجود")

    return user

@app.post("/register/")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_email = crud.get_user_by_email(db, user.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="البريد مستخدم مسبقاً")

    existing_username = crud.get_user_by_username(db, user.username)
    if existing_username:
        raise HTTPException(status_code=400, detail="اسم المستخدم مستخدم مسبقاً")

    created_user = crud.create_user(db, user)

    return {
        "id": created_user.id,
        "username": created_user.username,
        "email": created_user.email,
        "is_active": created_user.is_active,
    }


@app.post("/login/")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")

    token = create_access_token({
        "user_id": db_user.id,
        "email": db_user.email,
        "username": db_user.username
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "is_active": db_user.is_active,
        }
    }
# ===== Root =====
@app.get("/")
def read_root():
    return {"message": "Code Tutor API is running 🚀"}
# ===== Root =====
@app.get("/")
def read_root():
    return {"message": "Code Tutor API is running 🚀"}

# ===== Problems =====
@app.post("/problems/", response_model=schemas.Problem)
def create_problem(problem: schemas.ProblemCreate, db: Session = Depends(get_db)):
    return crud.create_problem(db, problem)

@app.get("/problems/", response_model=list[schemas.Problem])
def read_problems(db: Session = Depends(get_db)):
    return crud.get_problems(db)

@app.get("/problems/{problem_id}", response_model=schemas.Problem)
def read_problem(problem_id: int, db: Session = Depends(get_db)):
    problem = crud.get_problem(db, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="المسألة غير موجودة")
    return problem

# ===== Test Cases =====
@app.post("/test-cases/", response_model=schemas.TestCase)
def create_test_case(test_case: schemas.TestCaseCreate, db: Session = Depends(get_db)):
    return crud.create_test_case(db, test_case)

# ===== Code Run =====
@app.post("/run/", response_model=schemas.CodeRunResult)
def run_code(request: schemas.CodeRunRequest):
    result = code_runner.run_code(
        source_code=request.source_code,
        input_data=request.input_data,
        language=request.language
    )
    return result

# ===== Submit Solution =====
@app.post("/submit/", response_model=schemas.SubmissionResult)
def submit_solution(
    submission: schemas.SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # جلب المسألة
    problem = crud.get_problem(db, submission.problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="المسألة غير موجودة")

    # جلب test cases
    test_cases = crud.get_test_cases(db, submission.problem_id)
    if not test_cases:
        raise HTTPException(status_code=400, detail="لا يوجد test cases لهذه المسألة")

    results = []
    passed_count = 0
    last_error = ""
    last_explanation = ""

    for i, tc in enumerate(test_cases):
        run_result = code_runner.run_code(
            source_code=submission.source_code,
            input_data=tc.input_data,
            language=submission.language
        )

        actual_output = run_result["output"].strip()
        expected_output = tc.expected_output.strip()
        error = run_result["error"]
        passed = (actual_output == expected_output) and run_result["success"]

        if passed:
            passed_count += 1
        else:
            last_error = error
            last_explanation = explain_error(error, expected_output, actual_output)

        results.append(schemas.TestCaseResult(
            test_case_number=i + 1,
            input_data=tc.input_data if not tc.is_hidden else "🔒 Hidden",
            expected_output=expected_output if not tc.is_hidden else "🔒 Hidden",
            actual_output=actual_output if not tc.is_hidden else "🔒 Hidden",
            passed=passed,
            error=error
        ))

    total = len(test_cases)

    if passed_count == total:
        status = "✅ Accepted"
    elif passed_count == 0:
        status = "❌ Wrong Answer"
    else:
        status = f"⚠️ Partial ({passed_count}/{total})"

    crud.create_submission(
        db=db,
        user_id=current_user.id,
        problem_id=submission.problem_id,
        source_code=submission.source_code,
        language=submission.language,
        status=status,
        passed=passed_count,
        total=total,
        error=last_error
    )
    
@app.get("/me/")
def get_profile(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stats = crud.get_user_stats(db, current_user.id)

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "stats": stats
    }


@app.get("/my-submissions/")
def get_my_submissions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    submissions = crud.get_user_submissions(db, current_user.id)

    return [
        {
            "id": s.id,
            "problem_id": s.problem_id,
            "problem_title": s.problem.title if s.problem else "Unknown",
            "language": s.language,
            "status": s.status,
            "passed_cases": s.passed_cases,
            "total_cases": s.total_cases,
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else ""
        }
        for s in submissions
    ]
    return schemas.SubmissionResult(
        status=status,
        passed_cases=passed_count,
        total_cases=total,
        results=results,
        explanation=last_explanation
    )

@app.get("/leaderboard/")
def get_leaderboard(db: Session = Depends(get_db)):
    users = db.query(models.User).all()

    leaderboard = []

    for user in users:
        submissions = db.query(models.Submission).filter(
            models.Submission.user_id == user.id
        ).all()

        total = len(submissions)
        accepted = len([s for s in submissions if "Accepted" in s.status])
        solved = len(set(s.problem_id for s in submissions if "Accepted" in s.status))
        success_rate = round((accepted / total * 100), 1) if total > 0 else 0

        leaderboard.append({
            "username": user.username,
            "solved_problems": solved,
            "accepted_submissions": accepted,
            "total_submissions": total,
            "success_rate": success_rate,
        })

    leaderboard.sort(key=lambda x: (-x["solved_problems"], -x["success_rate"]))

    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1

    return leaderboard

@app.get("/problems-with-status/")
def get_problems_with_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    problems = db.query(models.Problem).all()
    result = []

    for p in problems:
        solved = db.query(models.Submission).filter(
            models.Submission.user_id == current_user.id,
            models.Submission.problem_id == p.id,
            models.Submission.status.like("%Accepted%")
        ).first() is not None

        result.append({
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "difficulty": p.difficulty,
            "sample_input": p.sample_input,
            "sample_output": p.sample_output,
            "hint": p.hint,
            "is_solved": solved
        })

    return result

@app.post("/import-codeforces/")
def import_from_codeforces(limit: int = 500):
    from .codeforces_importer import import_codeforces_problems
    import threading
    thread = threading.Thread(
        target=import_codeforces_problems,
        args=(limit,)
    )
    thread.start()
    return {"message": f"بدأ استيراد {limit} مسألة من Codeforces في الخلفية ✅"}