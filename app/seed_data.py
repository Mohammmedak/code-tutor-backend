import json
import os
from .database import SessionLocal
from . import models

def seed_problems():
    db = SessionLocal()

    existing = db.query(models.Problem).count()
    if existing > 0:
        print("المسائل موجودة مسبقاً ✅")
        db.close()
        return

    # قراءة ملف JSON
    json_path = os.path.join(os.path.dirname(__file__), "problems.json")
    with open(json_path, "r", encoding="utf-8") as f:
        problems_data = json.load(f)

    for p_data in problems_data:
        problem = models.Problem(
            title=p_data["title"],
            description=p_data["description"],
            difficulty=p_data["difficulty"],
            sample_input=p_data["sample_input"],
            sample_output=p_data["sample_output"],
            hint=p_data["hint"],
        )
        db.add(problem)
        db.commit()
        db.refresh(problem)

        for tc in p_data["test_cases"]:
            test_case = models.TestCase(
                problem_id=problem.id,
                input_data=tc["input"],
                expected_output=tc["output"],
                is_hidden=False,
            )
            db.add(test_case)

        db.commit()

    print(f"تم إضافة {len(problems_data)} مسألة بنجاح ✅")
    db.close()