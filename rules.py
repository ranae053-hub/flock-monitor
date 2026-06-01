"""
نظام قواعد الإنذار الذكي لقطيع H&N Super Nick
"""
import pandas as pd


def check_alerts(df):
    """Return list of alert dicts for the latest day."""
    if df.empty:
        return []

    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else None
    alerts = []

    age = latest["_age_num"]
    std_tmax = latest["std_temp_max"]
    std_tmin = latest["std_temp_min"]
    std_hmax = latest["std_hum_max"]
    std_feed = latest["std_feed_g"]
    std_water = latest["std_water_ml"]

    # ── A. الإجهاد الحراري ──────────────────────────────────────
    if pd.notna(latest["temp_cur"]) and latest["temp_cur"] > std_tmax + 2:
        alerts.append({
            "category": "إجهاد حراري 🌡️",
            "severity": "خطر",
            "color": "#FF4444",
            "message": f"الحرارة الحالية {latest['temp_cur']}°م تتجاوز الحد الموصى به ({std_tmax}°م) للعمر {age} يوم",
            "causes": ["ارتفاع درجة حرارة الجو", "قصور في التهوية", "كثافة الطيور"],
            "recommendations": [
                "تشغيل مراوح إضافية أو رفع سرعة التهوية",
                "رش الماء على السقف أو استخدام الضباب",
                "تقليل الكثافة مؤقتاً إذا أمكن",
                "زيادة استهلاك المياه بإضافة إلكتروليت",
            ],
        })
    if pd.notna(latest["temp_max"]) and latest["temp_max"] > std_tmax + 4:
        alerts.append({
            "category": "إجهاد حراري حاد 🌡️",
            "severity": "خطر شديد",
            "color": "#CC0000",
            "message": f"الحرارة القصوى {latest['temp_max']}°م بالغة الخطورة للعمر {age} يوم",
            "causes": ["موجة حر", "تعطل التهوية"],
            "recommendations": [
                "تدخل فوري: تشغيل كل وسائل التبريد",
                "مراقبة النافق كل ساعة",
                "توفير ماء بارد ومعززات",
            ],
        })

    # ── B. مشاكل التهوية ────────────────────────────────────────
    if pd.notna(latest["hum_cur"]) and latest["hum_cur"] > std_hmax + 10:
        alerts.append({
            "category": "مشكلة تهوية 💨",
            "severity": "تحذير",
            "color": "#FF8C00",
            "message": f"الرطوبة {latest['hum_cur']}% تتجاوز الحد المسموح ({std_hmax}%)",
            "causes": ["تهوية غير كافية", "مصادر رطوبة زائدة", "تسرب مياه"],
            "recommendations": [
                "زيادة معدل التهوية",
                "الكشف عن تسرب المياه",
                "تحسين تصريف الفرشة",
            ],
        })

    if latest["_has_respiratory"]:
        alerts.append({
            "category": "أعراض تنفسية ⚠️",
            "severity": "خطر",
            "color": "#FF4444",
            "message": "وجود ملاحظات تنفسية في السجل اليومي",
            "causes": ["عدوى تنفسية", "ضعف التهوية", "غبار عالي"],
            "recommendations": [
                "عزل الطيور المريضة فوراً",
                "استشارة الطبيب البيطري",
                "مراجعة برنامج التحصين",
                "فحص جودة الهواء",
            ],
        })

    # ── C. مشاكل المياه ─────────────────────────────────────────
    if pd.notna(latest["water_per_bird_ml"]) and latest["water_per_bird_ml"] < std_water * 0.75:
        alerts.append({
            "category": "انخفاض استهلاك المياه 💧",
            "severity": "تحذير",
            "color": "#FF8C00",
            "message": f"استهلاك المياه للطائر {latest['water_per_bird_ml']:.1f} مل أقل من القياسي ({std_water:.0f} مل)",
            "causes": ["عطل في خطوط المياه", "ضغط منخفض", "تلوث المياه", "مرض"],
            "recommendations": [
                "فحص جميع المنافذ والنيبلات",
                "قياس ضغط المياه",
                "فحص جودة المياه وتطهيرها",
            ],
        })

    # ── D. مشاكل صحية (نافق مرتفع) ─────────────────────────────
    if pd.notna(latest["mortality"]):
        daily_mort_pct = latest["mortality"] / latest["current_birds"] * 100
        threshold = 0.5 if age < 14 else 0.3
        if daily_mort_pct > threshold:
            alerts.append({
                "category": "نافق مرتفع 💀",
                "severity": "خطر" if daily_mort_pct > threshold * 2 else "تحذير",
                "color": "#FF4444" if daily_mort_pct > threshold * 2 else "#FF8C00",
                "message": f"النافق اليومي {int(latest['mortality'])} طائر ({daily_mort_pct:.2f}%) يتجاوز الحد الطبيعي {threshold}%",
                "causes": ["مرض وبائي", "تعفن", "إجهاد حراري", "مشكلة تغذية"],
                "recommendations": [
                    "إجراء فحص سريع للطيور النافقة",
                    "استدعاء الطبيب البيطري",
                    "عزل الطيور الضعيفة",
                    "مراجعة جميع المعاملات",
                ],
            })

    # ── E. اضطرابات هضمية ───────────────────────────────────────
    if latest["_has_diarrhea"]:
        alerts.append({
            "category": "اضطرابات هضمية 🦠",
            "severity": "تحذير",
            "color": "#FF8C00",
            "message": "ملاحظة إسهال في السجل اليومي",
            "causes": ["عدوى بكتيرية", "فطريات", "تغيير مفاجئ في العلف", "مياه ملوثة"],
            "recommendations": [
                "إضافة بروبيوتيك وإلكتروليت للمياه",
                "فحص جودة العلف والمياه",
                "استشارة الطبيب البيطري للعلاج المناسب",
            ],
        })

    # ── انخفاض استهلاك العلف ────────────────────────────────────
    if pd.notna(latest["feed_per_bird"]) and latest["feed_per_bird"] < std_feed * 0.75:
        alerts.append({
            "category": "انخفاض استهلاك العلف 🌾",
            "severity": "تحذير",
            "color": "#FFC300",
            "message": f"استهلاك العلف للطائر {latest['feed_per_bird']:.1f} جم أقل من القياسي ({std_feed:.0f} جم)",
            "causes": ["مشكلة صحية", "إجهاد حراري", "مشكلة في جودة العلف", "انقطاع المياه"],
            "recommendations": [
                "فحص جودة العلف وتاريخ صلاحيته",
                "التأكد من توفر المياه",
                "مراقبة الطيور لاكتشاف أعراض مرضية",
            ],
        })

    return alerts


def get_alert_summary(df):
    """Get alert history over all days."""
    rows = []
    for i in range(1, len(df)):
        sub = df.iloc[:i+1]
        day_alerts = check_alerts(sub)
        for a in day_alerts:
            rows.append({
                "date": df.iloc[i]["_date"],
                "age": df.iloc[i]["_age_num"],
                "category": a["category"],
                "severity": a["severity"],
                "message": a["message"],
            })
    return pd.DataFrame(rows) if rows else pd.DataFrame()
