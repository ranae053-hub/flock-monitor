"""
مؤشر صحة القطيع والتحليل الذكي
"""
import pandas as pd
import numpy as np
from data_loader import get_standard_for_age, INITIAL_BIRDS
from rules import check_alerts


def compute_health_score(df):
    """
    مؤشر صحة القطيع من 100 يومياً.
    مكونات الدرجة:
      - النفوق           30 نقطة
      - استهلاك العلف    20 نقطة
      - استهلاك المياه   20 نقطة
      - الحرارة          15 نقطة
      - الرطوبة          10 نقطة
      - انتظام الأداء    5 نقطة
    """
    scores = []
    for _, row in df.iterrows():
        age = row["_age_num"]
        std = get_standard_for_age(age)
        std_feed, std_water, std_tmax, std_tmin, std_hmax = std
        score = 100.0

        # النفوق (30 نقطة)
        if pd.notna(row["mortality"]):
            daily_pct = row["mortality"] / max(row["current_birds"], 1) * 100
            threshold = 0.5 if age < 14 else 0.3
            mort_penalty = min(30, (daily_pct / threshold) * 30 if threshold > 0 else 0)
            score -= mort_penalty

        # استهلاك العلف (20 نقطة)
        if pd.notna(row["feed_per_bird"]) and std_feed > 0:
            ratio = row["feed_per_bird"] / std_feed
            dev = abs(1 - ratio)
            feed_penalty = min(20, dev * 40)
            score -= feed_penalty

        # استهلاك المياه (20 نقطة)
        if pd.notna(row["water_per_bird_ml"]) and std_water > 0:
            ratio = row["water_per_bird_ml"] / std_water
            dev = abs(1 - ratio)
            water_penalty = min(20, dev * 40)
            score -= water_penalty

        # الحرارة (15 نقطة)
        if pd.notna(row["temp_cur"]):
            if row["temp_cur"] > std_tmax:
                temp_penalty = min(15, (row["temp_cur"] - std_tmax) * 3)
            elif row["temp_cur"] < std_tmin:
                temp_penalty = min(15, (std_tmin - row["temp_cur"]) * 3)
            else:
                temp_penalty = 0
            score -= temp_penalty

        # الرطوبة (10 نقطة)
        if pd.notna(row["hum_cur"]) and row["hum_cur"] > std_hmax:
            hum_penalty = min(10, (row["hum_cur"] - std_hmax) * 0.5)
            score -= hum_penalty

        scores.append(max(0, min(100, score)))

    df = df.copy()
    df["health_score"] = scores

    # انتظام الأداء (bonus -5 إذا كان التباين عالياً)
    if len(df) >= 3:
        feed_cv = df["feed_per_bird"].std() / df["feed_per_bird"].mean() if df["feed_per_bird"].mean() > 0 else 0
        if feed_cv > 0.2:
            df["health_score"] = (df["health_score"] - 5).clip(0, 100)

    return df


def get_flock_status(df):
    """Return overall flock status text and color."""
    if df.empty:
        return "لا توجد بيانات", "#888"
    latest_score = df["health_score"].iloc[-1]
    if latest_score >= 85:
        return "ممتاز ✅", "#2ECC71"
    elif latest_score >= 70:
        return "جيد 👍", "#27AE60"
    elif latest_score >= 55:
        return "متوسط ⚠️", "#F39C12"
    elif latest_score >= 40:
        return "ضعيف ⚠️", "#E67E22"
    else:
        return "حرج 🚨", "#E74C3C"


def generate_smart_analysis(df):
    """Return structured smart analysis for the analysis page."""
    if df.empty:
        return {}

    df = compute_health_score(df)
    alerts = check_alerts(df)
    latest = df.iloc[-1]
    status_text, status_color = get_flock_status(df)

    # Performance vs standard
    age = latest["_age_num"]
    std = get_standard_for_age(age)
    std_feed, std_water, std_tmax, std_tmin, std_hmax = std

    feed_diff = (latest["feed_per_bird"] - std_feed) if pd.notna(latest["feed_per_bird"]) else None
    water_diff = (latest["water_per_bird_ml"] - std_water) if pd.notna(latest["water_per_bird_ml"]) else None

    # Trend (last 3 days)
    recent = df.tail(3)
    feed_trend = "مستقر"
    if len(recent) >= 2:
        delta = recent["feed_per_bird"].iloc[-1] - recent["feed_per_bird"].iloc[0]
        feed_trend = "تصاعدي ↑" if delta > 2 else ("تنازلي ↓" if delta < -2 else "مستقر →")

    return {
        "status_text": status_text,
        "status_color": status_color,
        "health_score": df["health_score"].iloc[-1],
        "alerts": alerts,
        "latest": latest,
        "std_feed": std_feed,
        "std_water": std_water,
        "std_tmax": std_tmax,
        "std_tmin": std_tmin,
        "feed_diff": feed_diff,
        "water_diff": water_diff,
        "feed_trend": feed_trend,
        "cum_mortality_pct": latest["mortality_pct"],
        "df": df,
    }
