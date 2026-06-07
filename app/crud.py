from sqlalchemy.orm import Session
from . import models, schemas

# ===== Problems =====
def create_problem(db: Session, problem: schemas.ProblemCreate):
    db_problem = models.Problem(
        title=problem.title,
        description=problem.description,
        difficulty=problem.difficulty,
        sample_input=problem.sample_input,
        sample_output=problem.sample_output,
        hint=problem.hint
    )
    db.add(db_problem)
    db.commit()
    db.refresh(db_problem)
    return db_problem

def get_problems(db: Session):
    return db.query(models.Problem).all()

def get_problem(db: Session, problem_id: int):
    return db.query(models.Problem).filter(
        models.Problem.id == problem_id
    ).first()

# ===== Test Cases =====
def create_test_case(db: Session, test_case: schemas.TestCaseCreate):
    db_test_case = models.TestCase(
        problem_id=test_case.problem_id,
        input_data=test_case.input_data,
        expected_output=test_case.expected_output,
        is_hidden=test_case.is_hidden
    )
    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)
    return db_test_case

def get_test_cases(db: Session, problem_id: int):
    return db.query(models.TestCase).filter(
        models.TestCase.problem_id == problem_id
    ).all()

# ===== Submissions =====
def create_submission(db: Session, user_id: int, problem_id: int, source_code: str,
                      language: str, status: str, passed: int, total: int, error: str):
    db_submission = models.Submission(
        user_id=user_id,
        problem_id=problem_id,
        source_code=source_code,
        language=language,
        status=status,
        passed_cases=passed,
        total_cases=total,
        error_message=error
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission

from .auth import hash_password

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_submissions(db: Session, user_id: int):
    return db.query(models.Submission).filter(
        models.Submission.user_id == user_id
    ).order_by(models.Submission.submitted_at.desc()).all()


def get_user_stats(db: Session, user_id: int):
    submissions = get_user_submissions(db, user_id)

    accepted_submissions = [
        s for s in submissions
        if "Accepted" in s.status
    ]

    solved_problem_ids = set(s.problem_id for s in accepted_submissions)

    return {
        "total_submissions": len(submissions),
        "accepted_submissions": len(accepted_submissions),
        "solved_problems": len(solved_problem_ids),
    }