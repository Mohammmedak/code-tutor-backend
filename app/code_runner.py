import subprocess
import tempfile
import os
import uuid

DOCKER_IMAGE = "code-runner"
TIMEOUT = 10
MEMORY_LIMIT = "128m"
CPU_LIMIT = "0.5"

def run_code(source_code: str, input_data: str, language: str, timeout: int = TIMEOUT):
    if language == "python":
        return run_in_docker(source_code, input_data, "py", "python", timeout)
    elif language == "cpp":
        return run_cpp_in_docker(source_code, input_data, timeout)
    elif language == "javascript":
        return run_js_in_docker(source_code, input_data, timeout)
    else:
        return {
            "success": False,
            "output": "",
            "error": f"اللغة '{language}' غير مدعومة"
        }

def run_python_code(source_code: str, input_data: str = "", timeout: int = TIMEOUT):
    return run_in_docker(source_code, input_data, "py", "python", timeout)

def run_in_docker(source_code, input_data, extension, command, timeout):
    result = {
        "success": False,
        "output": "",
        "error": "",
    }

    # إنشاء مجلد مؤقت
    temp_dir = tempfile.mkdtemp()
    code_file = os.path.join(temp_dir, f"code.{extension}")

    try:
        # كتابة الكود في ملف
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(source_code)

        # بناء أمر Docker
        docker_cmd = [
            "docker", "run",
            "--rm",
            "--network", "none",
            "--memory", MEMORY_LIMIT,
            "--cpus", CPU_LIMIT,
            "--pids-limit", "50",
            "--read-only",
            "--tmpfs", "/tmp:size=10m",
            "-v", f"{temp_dir}:/code:ro",
            "-w", "/code",
            DOCKER_IMAGE,
            command, f"code.{extension}"
        ]

        process = subprocess.run(
            docker_cmd,
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout + 5
        )

        if process.returncode == 0:
            result["success"] = True
            result["output"] = process.stdout.strip()
        else:
            result["error"] = process.stderr.strip()

    except subprocess.TimeoutExpired:
        result["error"] = "Time Limit Exceeded (الكود استغرق وقتاً طويلاً)"
    except Exception as e:
        result["error"] = str(e)
    finally:
        # تنظيف الملفات المؤقتة
        try:
            os.remove(code_file)
            os.rmdir(temp_dir)
        except:
            pass

    return result

def run_cpp_in_docker(source_code, input_data, timeout):
    result = {
        "success": False,
        "output": "",
        "error": "",
    }

    temp_dir = tempfile.mkdtemp()
    code_file = os.path.join(temp_dir, "code.cpp")

    try:
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(source_code)

        # تجميع C++
        compile_cmd = [
            "docker", "run",
            "--rm",
            "--network", "none",
            "--memory", MEMORY_LIMIT,
            "-v", f"{temp_dir}:/code",
            "-w", "/code",
            DOCKER_IMAGE,
            "g++", "code.cpp", "-o", "code_out"
        ]

        compile_process = subprocess.run(
            compile_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )

        if compile_process.returncode != 0:
            result["error"] = compile_process.stderr.strip()
            return result

        # تشغيل C++
        run_cmd = [
            "docker", "run",
            "--rm",
            "--network", "none",
            "--memory", MEMORY_LIMIT,
            "--cpus", CPU_LIMIT,
            "--pids-limit", "50",
            "--read-only",
            "--tmpfs", "/tmp:size=10m",
            "-v", f"{temp_dir}:/code:ro",
            "-w", "/code",
            DOCKER_IMAGE,
            "./code_out"
        ]

        run_process = subprocess.run(
            run_cmd,
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout + 5
        )

        if run_process.returncode == 0:
            result["success"] = True
            result["output"] = run_process.stdout.strip()
        else:
            result["error"] = run_process.stderr.strip()

    except subprocess.TimeoutExpired:
        result["error"] = "Time Limit Exceeded (الكود استغرق وقتاً طويلاً)"
    except Exception as e:
        result["error"] = str(e)
    finally:
        try:
            for f in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, f))
            os.rmdir(temp_dir)
        except:
            pass

    return result

def run_js_in_docker(source_code, input_data, timeout):
    result = {
        "success": False,
        "output": "",
        "error": "",
    }

    # إضافة wrapper للمدخلات
    wrapper = f"""
const inputLines = `{input_data}`.trim().split('\\n');
let lineIndex = 0;
function input() {{
    return inputLines[lineIndex++];
}}
function readline() {{
    return input();
}}
{source_code}
"""

    temp_dir = tempfile.mkdtemp()
    code_file = os.path.join(temp_dir, "code.js")

    try:
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(wrapper)

        docker_cmd = [
            "docker", "run",
            "--rm",
            "--network", "none",
            "--memory", MEMORY_LIMIT,
            "--cpus", CPU_LIMIT,
            "--pids-limit", "50",
            "--read-only",
            "--tmpfs", "/tmp:size=10m",
            "-v", f"{temp_dir}:/code:ro",
            "-w", "/code",
            DOCKER_IMAGE,
            "node", "code.js"
        ]

        process = subprocess.run(
            docker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout + 5
        )

        if process.returncode == 0:
            result["success"] = True
            result["output"] = process.stdout.strip()
        else:
            result["error"] = process.stderr.strip()

    except subprocess.TimeoutExpired:
        result["error"] = "Time Limit Exceeded (الكود استغرق وقتاً طويلاً)"
    except Exception as e:
        result["error"] = str(e)
    finally:
        try:
            os.remove(code_file)
            os.rmdir(temp_dir)
        except:
            pass

    return result