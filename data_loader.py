import pandas as pd
import numpy as np
import re

INITIAL_BIRDS = 5200
STRAIN = "H&N Super Nick"

# H&N Super Nick Rearing Standard (per bird/day, grams)
HN_STANDARDS = {
    # age_day: (feed_g, water_ml, max_temp, min_temp, max_humidity)
    1:  (10,  25,  35, 32, 65),
    2:  (12,  28,  35, 32, 65),
    3:  (14,  30,  34, 31, 65),
    4:  (16,  33,  34, 31, 65),
    5:  (18,  36,  33, 30, 65),
    6:  (20,  38,  33, 30, 65),
    7:  (22,  40,  32, 29, 65),
    8:  (24,  43,  32, 29, 65),
    9:  (26,  46,  31, 28, 65),
    10: (28,  48,  31, 28, 65),
    11: (30,  50,  30, 27, 65),
    12: (32,  53,  30, 27, 65),
    13: (34,  56,  30, 26, 65),
    14: (36,  58,  29, 26, 65),
    21: (45,  70,  27, 24, 65),
    28: (54,  84,  25, 22, 65),
    35: (62,  95,  23, 20, 65),
    42: (70, 105,  22, 18, 65),
    49: (76, 112,  21, 17, 65),
    56: (80, 118,  20, 17, 65),
    63: (83, 122,  20, 17, 65),
    70: (85, 125,  20, 17, 65),
    77: (87, 128,  20, 17, 65),
    84: (88, 130,  20, 17, 65),
    91: (89, 131,  20, 17, 65),
    98: (90, 132,  20, 17, 65),
    105:(90, 133,  20, 17, 65),
    112:(91, 134,  20, 17, 65),
    119:(91, 135,  20, 17, 65),
}


def _parse_age(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    m = re.search(r'(\d+)', s)
    return int(m.group(1)) if m else np.nan


def get_standard_for_age(age_day):
    """Interpolate H&N standard for any age."""
    ages = sorted(HN_STANDARDS.keys())
    if age_day <= ages[0]:
        return HN_STANDARDS[ages[0]]
    if age_day >= ages[-1]:
        return HN_STANDARDS[ages[-1]]
    for i in range(len(ages) - 1):
        a1, a2 = ages[i], ages[i + 1]
        if a1 <= age_day <= a2:
            t = (age_day - a1) / (a2 - a1)
            s1, s2 = HN_STANDARDS[a1], HN_STANDARDS[a2]
            return tuple(s1[j] + t * (s2[j] - s1[j]) for j in range(5))
    return HN_STANDARDS[ages[-1]]


def load_data(filepath):
    df = pd.read_excel(filepath, sheet_name="Daily Date")

    # Drop rows where التاريخ is NaT or row is totals/empty
    df = df[df["التاريخ"].notna()].copy()
    df = df[df["اليوم"].notna()].copy()
    df = df[df["اليوم"] != "-"].copy()

    # Parse age
    df["_age_num"] = df["عمر القطيع (باليوم)"].apply(_parse_age)
    df = df[df["_age_num"].notna()].copy()
    df["_age_num"] = df["_age_num"].astype(int)

    # Parse date
    df["_date"] = pd.to_datetime(df["التاريخ"], errors="coerce")
    df = df.sort_values("_date").reset_index(drop=True)

    # Numeric conversions
    num_cols = {
        "الحرارة الحالية (مئوية)": "temp_cur",
        "الحرارة (Max) (مئوية)": "temp_max",
        "الحرارة (Min) (م)": "temp_min",
        "الرطوبة الحالية (%)": "hum_cur",
        "الرطوبة (Max) (%)": "hum_max",
        "الرطوبة (Min) (%)": "hum_min",
        "النافق اليومي": "mortality",
        "استهلاك العلف اليومي (بالكيلو جرام)": "feed_kg",
        "استهلاك العلف لكل طائر (بالجرام)": "feed_per_bird",
        "استهلاك المياه اليومي (باللتر)": "water_l",
    }
    for orig, new in num_cols.items():
        df[new] = pd.to_numeric(df[orig], errors="coerce")

    # Cumulative mortality & current birds
    df["cum_mortality"] = df["mortality"].fillna(0).cumsum()
    df["current_birds"] = INITIAL_BIRDS - df["cum_mortality"]
    df["mortality_pct"] = df["cum_mortality"] / INITIAL_BIRDS * 100

    # Water per bird (ml)
    df["water_per_bird_ml"] = df["water_l"] / df["current_birds"] * 1000

    # Week number
    df["week"] = np.ceil(df["_age_num"] / 7).astype(int)

    # Add standard columns
    def std_row(age):
        s = get_standard_for_age(age)
        return pd.Series({
            "std_feed_g": s[0],
            "std_water_ml": s[1],
            "std_temp_max": s[2],
            "std_temp_min": s[3],
            "std_hum_max": s[4],
        })

    std_df = df["_age_num"].apply(std_row)
    df = pd.concat([df, std_df], axis=1)

    # Notes / illness flag
    df["_notes"] = df["الملاحظات"].fillna("") + " " + df["وجود إصابة مرضية"].fillna("")
    df["_notes"] = df["_notes"].str.lower()
    df["_has_diarrhea"] = df["_notes"].str.contains("اسهال|إسهال|diarr", na=False)
    df["_has_respiratory"] = df["_notes"].str.contains("تنفس|respiratory|سعال|wheez", na=False)

    return df


def get_weekly_summary(df):
    agg = df.groupby("week").agg(
        days=("_age_num", "count"),
        avg_temp=("temp_cur", "mean"),
        avg_hum=("hum_cur", "mean"),
        total_mortality=("mortality", "sum"),
        total_feed_kg=("feed_kg", "sum"),
        total_water_l=("water_l", "sum"),
        avg_feed_per_bird=("feed_per_bird", "mean"),
        avg_water_per_bird_ml=("water_per_bird_ml", "mean"),
        end_birds=("current_birds", "last"),
        start_age=("_age_num", "min"),
        end_age=("_age_num", "max"),
    ).reset_index()
    agg["mortality_pct"] = agg["total_mortality"] / INITIAL_BIRDS * 100
    return agg
