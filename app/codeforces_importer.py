import requests
import time
from bs4 import BeautifulSoup
from .database import SessionLocal
from . import models

CODEFORCES_API = "https://codeforces.com/api"

def fetch_problem_details(contest_id, index):
    """جلب تفاصيل المسألة الكاملة من صفحة الويب"""
    try:
        url = f"https://codeforces.com/problemset/problem/{contest_id}/{index}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0"
        }
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # جلب نص المسألة
        problem_div = soup.find("div", class_="problem-statement")
        if not problem_div:
            return None

        # الوصف
        description = ""
        desc_div = problem_div.find("div", class_="header")
        if desc_div:
            next_div = desc_div.find_next_sibling("div")
            if next_div:
                description = next_div.get_text(strip=True, separator="\n")

        # Input
        input_spec = ""
        input_div = problem_div.find("div", class_="input-specification")
        if input_div:
            input_spec = input_div.get_text(strip=True, separator="\n")

        # Output
        output_spec = ""
        output_div = problem_div.find("div", class_="output-specification")
        if output_div:
            output_spec = output_div.get_text(strip=True, separator="\n")

        # أمثلة
        sample_tests = []
        sample_div = problem_div.find("div", class_="sample-test")
        if sample_div:
            inputs = sample_div.find_all("div", class_="input")
            outputs = sample_div.find_all("div", class_="output")

            for inp, out in zip(inputs, outputs):
                inp_pre = inp.find("pre")
                out_pre = out.find("pre")
                if inp_pre and out_pre:
                    input_text = inp_pre.get_text(strip=True, separator="\n")
                    output_text = out_pre.get_text(strip=True, separator="\n")
                    sample_tests.append({
                        "input": input_text,
                        "output": output_text
                    })

        # Note
        note = ""
        note_div = problem_div.find("div", class_="note")
        if note_div:
            note = note_div.get_text(strip=True, separator="\n")

        # بناء الوصف الكامل
        full_description = ""

        if description:
            full_description += f"📝 الوصف:\n{description}\n\n"

        if input_spec:
            full_description += f"📥 المدخلات:\n{input_spec}\n\n"

        if output_spec:
            full_description += f"📤 المخرجات:\n{output_spec}\n\n"

        if note:
            full_description += f"💡 ملاحظة:\n{note}"

        sample_input = ""
        sample_output = ""
        if sample_tests:
            sample_input = sample_tests[0]["input"]
            sample_output = sample_tests[0]["output"]

        return {
            "description": full_description,
            "sample_input": sample_input,
            "sample_output": sample_output,
            "test_cases": sample_tests
        }

    except Exception as e:
        print(f"خطأ في جلب تفاصيل المسألة: {e}")
        return None

def fetch_problems():
    """جلب المسائل من Codeforces API"""
    try:
        print("جاري جلب المسائل من Codeforces...")
        response = requests.get(
            f"{CODEFORCES_API}/problemset.problems",
            timeout=30
        )
        data = response.json()

        if data["status"] != "OK":
            print("خطأ في جلب المسائل")
            return []

        problems = data["result"]["problems"]
        print(f"تم جلب {len(problems)} مسألة من Codeforces ✅")
        return problems

    except Exception as e:
        print(f"خطأ: {e}")
        return []

def get_difficulty(rating):
    """تحديد مستوى الصعوبة"""
    if rating is None:
        return "Easy"
    elif rating <= 1200:
        return "Easy"
    elif rating <= 1800:
        return "Medium"
    else:
        return "Hard"

def problem_exists(db, title):
    """تحقق إذا المسألة موجودة"""
    return db.query(models.Problem).filter(
        models.Problem.title == title
    ).first() is not None

def import_codeforces_problems(limit=500):
    """استيراد مسائل Codeforces مع تفاصيل كاملة"""
    db = SessionLocal()

    try:
        problems = fetch_problems()
        if not problems:
            print("لا توجد مسائل للاستيراد")
            return

        imported = 0
        skipped = 0
        failed = 0

        for cf_problem in problems:
            if imported >= limit:
                break

            # تجاهل المسائل بدون rating
            if "rating" not in cf_problem:
                skipped += 1
                continue

            contest_id = cf_problem.get("contestId", "")
            index = cf_problem.get("index", "")
            title = f"{cf_problem['name']} ({contest_id}{index})"

            # تجاهل إذا موجودة
            if problem_exists(db, title):
                skipped += 1
                continue

            # جلب التفاصيل الكاملة
            print(f"جلب تفاصيل: {title}...")
            details = fetch_problem_details(contest_id, index)

            # انتظار قصير لتجنب الحظر
            time.sleep(1)

            difficulty = get_difficulty(cf_problem.get("rating"))
            tags = cf_problem.get("tags", [])
            tags_str = ", ".join(tags) if tags else "General"
            rating = cf_problem.get("rating", "N/A")

            if details and details["description"]:
                description = details["description"]
                sample_input = details["sample_input"]
                sample_output = details["sample_output"]
                test_cases = details["test_cases"]
            else:
                problem_url = f"https://codeforces.com/problemset/problem/{contest_id}/{index}"
                description = (
                    f"مسألة من Codeforces - {cf_problem['name']}\n\n"
                    f"📊 المستوى: {rating}\n"
                    f"🏷️ التصنيفات: {tags_str}\n\n"
                    f"🔗 رابط المسألة:\n{problem_url}"
                )
                sample_input = ""
                sample_output = ""
                test_cases = []
                failed += 1

            # إضافة المسألة
            problem = models.Problem(
                title=title,
                description=description,
                difficulty=difficulty,
                sample_input=sample_input,
                sample_output=sample_output,
                hint=f"Rating: {rating} | Tags: {tags_str}",
            )
            db.add(problem)
            db.commit()
            db.refresh(problem)

            # إضافة test cases
            for tc in test_cases:
                test_case = models.TestCase(
                    problem_id=problem.id,
                    input_data=tc["input"],
                    expected_output=tc["output"],
                    is_hidden=False,
                )
                db.add(test_case)

            db.commit()
            imported += 1

            if imported % 10 == 0:
                print(f"✅ تم استيراد {imported} مسألة...")

        print(f"\n✅ تم الانتهاء!")
        print(f"✅ استُوردت: {imported} مسألة")
        print(f"⏭️ تُجووزت: {skipped} مسألة")
        print(f"⚠️ بدون تفاصيل: {failed} مسألة")

    except Exception as e:
        print(f"خطأ: {e}")
        db.rollback()

    finally:
        db.close()