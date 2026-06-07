def explain_error(error: str, expected: str, actual: str) -> str:
    
    if not error and actual != expected:
        return explain_wrong_output(expected, actual)
    
    return explain_error_message(error)

def explain_wrong_output(expected: str, actual: str) -> str:
    explanation = "✅ الكود يعمل بدون أخطاء، لكن الناتج غير صحيح.\n\n"
    explanation += f"📌 الناتج المتوقع: {expected}\n"
    explanation += f"📌 ناتجك: {actual}\n\n"
    explanation += "💡 نصائح:\n"
    explanation += "- راجع طريقة قراءة المدخلات (input)\n"
    explanation += "- راجع العمليات الحسابية\n"
    explanation += "- تأكد من طريقة الطباعة (print)\n"
    explanation += "- راجع شروط الحلقات والـ if"
    return explanation

def explain_error_message(error: str) -> str:
    error_lower = error.lower()

    if "syntaxerror" in error_lower:
        return (
            "❌ خطأ في الصياغة (SyntaxError)\n\n"
            "💡 يعني في مشكلة بكتابة الكود نفسه.\n"
            "- تأكد من وجود ':' بعد if / for / while / def\n"
            "- تأكد من إغلاق كل قوس فتحته\n"
            "- تأكد من علامات التنصيص"
        )

    elif "indentationerror" in error_lower:
        return (
            "❌ خطأ في المسافات (IndentationError)\n\n"
            "💡 Python حساس جداً للمسافات.\n"
            "- تأكد إن كل السطور داخل if أو for أو def عندها مسافة بادئة\n"
            "- استخدم 4 مسافات أو Tab بشكل موحد"
        )

    elif "nameerror" in error_lower:
        return (
            "❌ متغير غير معرّف (NameError)\n\n"
            "💡 أنت تستخدم متغير قبل تعريفه.\n"
            "- تأكد إنك عرّفت المتغير قبل استخدامه\n"
            "- تأكد من تطابق الأسماء (Python حساس للحروف الكبيرة والصغيرة)\n"
            "- مثلاً: 'Name' و 'name' مختلفتان"
        )

    elif "typeerror" in error_lower:
        return (
            "❌ خطأ في نوع البيانات (TypeError)\n\n"
            "💡 أنت تحاول عمل عملية على نوع بيانات خاطئ.\n"
            "- مثلاً: جمع رقم مع نص\n"
            "- الحل: استخدم int() أو str() لتحويل البيانات\n"
            "- مثال: int(input()) بدل input()"
        )

    elif "valueerror" in error_lower:
        return (
            "❌ خطأ في قيمة البيانات (ValueError)\n\n"
            "💡 القيمة المدخلة غير مناسبة للعملية.\n"
            "- مثلاً: int('abc') لن يعمل\n"
            "- تأكد إن المدخل رقم فعلاً قبل تحويله"
        )

    elif "indexerror" in error_lower:
        return (
            "❌ خطأ في فهرس القائمة (IndexError)\n\n"
            "💡 أنت تحاول الوصول لعنصر غير موجود.\n"
            "- تأكد إن الفهرس أصغر من طول القائمة\n"
            "- القوائم تبدأ من الفهرس 0 مش 1"
        )

    elif "zerodivisionerror" in error_lower:
        return (
            "❌ قسمة على صفر (ZeroDivisionError)\n\n"
            "💡 أنت تقسم عدداً على صفر.\n"
            "- أضف شرط: if divisor != 0 قبل القسمة"
        )

    elif "time limit" in error_lower:
        return (
            "⏰ تجاوز الوقت المسموح (Time Limit Exceeded)\n\n"
            "💡 الكود استغرق وقتاً طويلاً جداً.\n"
            "- تحقق إذا عندك حلقة لا نهائية (while True)\n"
            "- راجع شرط الإيقاف في الحلقات\n"
            "- فكر بطريقة أسرع لحل المسألة"
        )

    else:
        return (
            f"❌ خطأ في الكود:\n{error}\n\n"
            "💡 راجع الكود بعناية وتأكد من المنطق العام"
        )