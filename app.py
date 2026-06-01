"""
🐓 نظام إدارة ومراقبة قطيع الدجاج البياض
H&N Super Nick — مرحلة التربية
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import os

from data_loader import load_data, get_weekly_summary, INITIAL_BIRDS, STRAIN
from dashboard import (
    render_kpi_cards, render_alerts, render_health_gauge,
    chart_temperature, chart_humidity, chart_feed, chart_water,
    chart_mortality, chart_health_score, chart_weekly_summary,
)
from analysis import compute_health_score, get_flock_status, generate_smart_analysis
from rules import check_alerts, get_alert_summary

# ── Page Config ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="مزرعة شديد — مراقبة القطيع",
    page_icon="🐓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    * { font-family: 'Cairo', sans-serif !important; }
    
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; font-weight: 700; }
    [data-testid="stMetricLabel"] { font-size: 0.85rem !important; color: #555; }
    
    .alert-danger {
        background: linear-gradient(135deg, #FDEDEC, #FADBD8);
        border-right: 5px solid #E74C3C;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 6px 0;
    }
    .alert-warning {
        background: linear-gradient(135deg, #FEF9E7, #FDEBD0);
        border-right: 5px solid #F39C12;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 6px 0;
    }
    .alert-ok {
        background: linear-gradient(135deg, #EAFAF1, #D5F5E3);
        border-right: 5px solid #27AE60;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 6px 0;
    }
    
    .section-header {
        background: linear-gradient(90deg, #2C3E50, #3498DB);
        color: white;
        padding: 8px 16px;
        border-radius: 8px;
        margin: 16px 0 8px 0;
        font-size: 1.1rem;
        font-weight: 700;
    }
    
    .stTabs [data-baseweb="tab"] { font-size: 1rem; font-weight: 600; }
    
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
        border-top: 4px solid #3498DB;
    }
    
    .stDataFrame { direction: rtl; }
    
    footer { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/chicken.png", width=80)
    st.markdown("## 🐓 مراقبة القطيع")
    st.markdown(f"**السلالة:** {STRAIN}")
    st.markdown(f"**العدد الأولي:** {INITIAL_BIRDS:,} طائر")
    st.divider()

    uploaded_file = st.file_uploader(
        "📂 رفع ملف Excel",
        type=["xlsx"],
        help="ارفع الملف اليومي لتحديث البيانات تلقائياً",
    )

    default_path = os.path.join(os.path.dirname(__file__), "Sheded_Farm_Weekly_Report____week__2_.xlsx")
    
    if uploaded_file:
        filepath = "/tmp/flock_data.xlsx"
        with open(filepath, "wb") as f:
            f.write(uploaded_file.read())
    else:
        filepath = default_path

    auto_refresh = st.checkbox("🔄 تحديث تلقائي كل دقيقة", value=False)
    
    st.divider()
    st.markdown("### ⚙️ إعدادات العرض")
    show_std = st.checkbox("إظهار القيم القياسية في الرسوم", value=True)

    st.divider()
    st.caption("🏭 مزرعة شديد — نظام الإدارة الذكي")
    st.caption("H&N Super Nick Rearing Monitor")


# ── Load Data ────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def cached_load(path):
    return load_data(path)


try:
    df_raw = cached_load(filepath)
    df = compute_health_score(df_raw)
    weekly = get_weekly_summary(df)
    alerts = check_alerts(df)
    analysis = generate_smart_analysis(df)
except Exception as e:
    st.error(f"❌ خطأ في تحميل البيانات: {e}")
    st.stop()

# ── Header ──────────────────────────────────────────────────────────────
col_logo, col_title, col_status = st.columns([1, 5, 2])
with col_logo:
    st.markdown("## 🐓")
with col_title:
    latest = df.iloc[-1]
    st.markdown(f"# مزرعة شديد — قطيع {STRAIN}")
    st.markdown(f"📅 آخر تحديث: **{latest['_date'].strftime('%Y/%m/%d')}** | العمر: **{int(latest['_age_num'])} يوم** — أسبوع **{int(latest['week'])}**")
with col_status:
    alert_count = len(alerts)
    if alert_count == 0:
        st.success("✅ لا توجد تنبيهات")
    elif any(a["severity"] in ["خطر", "خطر شديد"] for a in alerts):
        st.error(f"🚨 {alert_count} تنبيه خطر")
    else:
        st.warning(f"⚠️ {alert_count} تنبيه")

st.divider()

# ── Main Tabs ────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 لوحة التحكم",
    "🔔 نظام الإنذار",
    "🏥 التحليل الذكي",
    "📅 التقارير الأسبوعية",
    "📈 المقارنة بالقياسي",
])


# ════════════════════════════════════════════════════════════════════════
# TAB 1: Dashboard
# ════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">📌 المؤشرات الرئيسية — آخر يوم مسجل</div>', unsafe_allow_html=True)
    render_kpi_cards(df)
    
    st.divider()
    st.markdown('<div class="section-header">📈 الرسوم البيانية اليومية</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(chart_temperature(df), use_container_width=True)
    with c2:
        st.plotly_chart(chart_humidity(df), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(chart_feed(df), use_container_width=True)
    with c4:
        st.plotly_chart(chart_water(df), use_container_width=True)

    c5, c6 = st.columns(2)
    with c5:
        st.plotly_chart(chart_mortality(df), use_container_width=True)
    with c6:
        st.plotly_chart(chart_health_score(df), use_container_width=True)

    st.divider()
    st.markdown('<div class="section-header">📋 جدول البيانات اليومية</div>', unsafe_allow_html=True)
    display_cols = [
        "_date", "_age_num", "week", "current_birds",
        "temp_cur", "temp_max", "temp_min",
        "hum_cur", "mortality", "mortality_pct",
        "feed_kg", "feed_per_bird", "water_l", "water_per_bird_ml",
        "health_score",
    ]
    col_names = {
        "_date": "التاريخ", "_age_num": "العمر (يوم)", "week": "الأسبوع",
        "current_birds": "عدد الطيور", "temp_cur": "الحرارة الحالية",
        "temp_max": "الحرارة القصوى", "temp_min": "الحرارة الدنيا",
        "hum_cur": "الرطوبة %", "mortality": "النافق",
        "mortality_pct": "نسبة النفوق%", "feed_kg": "علف كجم",
        "feed_per_bird": "علف/طائر جم", "water_l": "ماء لتر",
        "water_per_bird_ml": "ماء/طائر مل", "health_score": "مؤشر الصحة",
    }
    show_df = df[display_cols].rename(columns=col_names)
    show_df["التاريخ"] = show_df["التاريخ"].dt.strftime("%Y/%m/%d")
    show_df["نسبة النفوق%"] = show_df["نسبة النفوق%"].round(2)
    show_df["مؤشر الصحة"] = show_df["مؤشر الصحة"].round(1)
    st.dataframe(show_df, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════
# TAB 2: Alerts
# ════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">🔔 تنبيهات اليوم الأخير</div>', unsafe_allow_html=True)
    render_alerts(alerts)

    st.divider()
    st.markdown('<div class="section-header">📜 سجل التنبيهات الكاملة</div>', unsafe_allow_html=True)
    hist = get_alert_summary(df)
    if not hist.empty:
        hist["date"] = hist["date"].dt.strftime("%Y/%m/%d")
        st.dataframe(hist.rename(columns={
            "date": "التاريخ", "age": "العمر", "category": "الفئة",
            "severity": "الخطورة", "message": "الرسالة",
        }), use_container_width=True, hide_index=True)
    else:
        st.info("لا يوجد سجل تنبيهات.")


# ════════════════════════════════════════════════════════════════════════
# TAB 3: Smart Analysis
# ════════════════════════════════════════════════════════════════════════
with tab3:
    a = analysis

    col_gauge, col_summary = st.columns([2, 3])
    with col_gauge:
        render_health_gauge(a["health_score"], a["status_text"], a["status_color"])
    with col_summary:
        st.markdown('<div class="section-header">📋 ملخص الحالة</div>', unsafe_allow_html=True)
        l = a["latest"]
        age = int(l["_age_num"])

        st.markdown(f"""
| المؤشر | القيمة الفعلية | القياسي | الفرق |
|--------|--------------|---------|-------|
| نسبة النفوق التراكمية | {l['mortality_pct']:.2f}% | <0.5% | {'🟢' if l['mortality_pct'] < 0.5 else '🔴'} |
| علف/طائر | {l['feed_per_bird']:.1f} جم | {a['std_feed']:.0f} جم | {l['feed_per_bird'] - a['std_feed']:+.1f} جم |
| ماء/طائر | {l['water_per_bird_ml']:.1f} مل | {a['std_water']:.0f} مل | {l['water_per_bird_ml'] - a['std_water']:+.1f} مل |
| الحرارة الحالية | {l['temp_cur']:.1f}°م | {a['std_tmin']:.0f}-{a['std_tmax']:.0f}°م | {'✅' if a['std_tmin'] <= l['temp_cur'] <= a['std_tmax'] else '❌'} |
| اتجاه العلف | {a['feed_trend']} | — | — |
        """)

    st.divider()
    st.markdown('<div class="section-header">🔍 المشكلات المكتشفة والتوصيات</div>', unsafe_allow_html=True)

    if not a["alerts"]:
        st.markdown("""
<div class="alert-ok">
✅ <strong>لا توجد مشكلات مكتشفة حالياً</strong><br>
القطيع يعمل ضمن النطاق الطبيعي. استمر في المراقبة اليومية.
</div>""", unsafe_allow_html=True)
    else:
        for alert in a["alerts"]:
            severity_class = "alert-danger" if "خطر" in alert["severity"] else "alert-warning"
            st.markdown(f"""
<div class="{severity_class}">
<strong>{alert['category']}</strong> — {alert['severity']}<br>
<em>{alert['message']}</em>
</div>""", unsafe_allow_html=True)

            col_c, col_r = st.columns(2)
            with col_c:
                st.markdown("**🔍 الأسباب:**")
                for c in alert["causes"]:
                    st.markdown(f"• {c}")
            with col_r:
                st.markdown("**✅ التوصيات:**")
                for r in alert["recommendations"]:
                    st.markdown(f"• {r}")
            st.divider()

    # Score trend
    st.markdown('<div class="section-header">📊 تطور مؤشر الصحة</div>', unsafe_allow_html=True)
    st.plotly_chart(chart_health_score(df), use_container_width=True)


# ════════════════════════════════════════════════════════════════════════
# TAB 4: Weekly Reports
# ════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">📅 التقارير الأسبوعية (محسوبة من البيانات اليومية)</div>', unsafe_allow_html=True)

    for _, wrow in weekly.iterrows():
        w = int(wrow["week"])
        with st.expander(f"📆 الأسبوع {w} | العمر: {int(wrow['start_age'])}-{int(wrow['end_age'])} يوم", expanded=(w == weekly["week"].max())):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("🐓 الطيور في نهاية الأسبوع", f"{int(wrow['end_birds']):,}")
                st.metric("💀 النافق الأسبوعي", f"{int(wrow['total_mortality'])}")
            with c2:
                st.metric("🌾 إجمالي العلف", f"{wrow['total_feed_kg']:.1f} كجم")
                st.metric("🌾 متوسط علف/طائر", f"{wrow['avg_feed_per_bird']:.1f} جم")
            with c3:
                st.metric("💧 إجمالي المياه", f"{wrow['total_water_l']:.0f} لتر")
                st.metric("💧 متوسط ماء/طائر", f"{wrow['avg_water_per_bird_ml']:.0f} مل")
            with c4:
                st.metric("🌡️ متوسط الحرارة", f"{wrow['avg_temp']:.1f}°م")
                st.metric("💦 متوسط الرطوبة", f"{wrow['avg_hum']:.0f}%")

    st.divider()
    st.plotly_chart(chart_weekly_summary(weekly), use_container_width=True)

    st.markdown('<div class="section-header">📊 جدول ملخص أسبوعي</div>', unsafe_allow_html=True)
    weekly_display = weekly.rename(columns={
        "week": "الأسبوع", "days": "الأيام", "avg_temp": "متوسط الحرارة",
        "avg_hum": "متوسط الرطوبة", "total_mortality": "إجمالي النافق",
        "total_feed_kg": "إجمالي العلف (كجم)", "total_water_l": "إجمالي المياه (ل)",
        "avg_feed_per_bird": "علف/طائر (جم)", "avg_water_per_bird_ml": "ماء/طائر (مل)",
        "end_birds": "الطيور النهائية", "mortality_pct": "نسبة النفوق%",
    })
    st.dataframe(weekly_display.round(2), use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════
# TAB 5: Standard Comparison
# ════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">📈 مقارنة الأداء الفعلي بالمعيار القياسي H&N Super Nick</div>', unsafe_allow_html=True)

    # Feed comparison
    fig_feed_cmp = go.Figure()
    fig_feed_cmp.add_trace(go.Scatter(
        x=df["_age_num"], y=df["feed_per_bird"],
        name="الفعلي", mode="lines+markers",
        line=dict(color="#27AE60", width=3),
        marker=dict(size=8),
    ))
    fig_feed_cmp.add_trace(go.Scatter(
        x=df["_age_num"], y=df["std_feed_g"],
        name="القياسي H&N", mode="lines",
        line=dict(color="#E74C3C", width=2, dash="dash"),
    ))
    fig_feed_cmp.update_layout(
        title="مقارنة استهلاك العلف لكل طائر",
        xaxis_title="عمر القطيع (يوم)",
        yaxis_title="جرام/طائر",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(245,247,250,1)",
        font=dict(family="Cairo, Arial"),
    )

    # Water comparison
    fig_water_cmp = go.Figure()
    fig_water_cmp.add_trace(go.Scatter(
        x=df["_age_num"], y=df["water_per_bird_ml"],
        name="الفعلي", mode="lines+markers",
        line=dict(color="#2980B9", width=3),
        marker=dict(size=8),
    ))
    fig_water_cmp.add_trace(go.Scatter(
        x=df["_age_num"], y=df["std_water_ml"],
        name="القياسي H&N", mode="lines",
        line=dict(color="#E74C3C", width=2, dash="dash"),
    ))
    fig_water_cmp.update_layout(
        title="مقارنة استهلاك المياه لكل طائر",
        xaxis_title="عمر القطيع (يوم)",
        yaxis_title="مل/طائر",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(245,247,250,1)",
        font=dict(family="Cairo, Arial"),
    )

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_feed_cmp, use_container_width=True)
    with c2:
        st.plotly_chart(fig_water_cmp, use_container_width=True)

    # Deviation table
    st.markdown('<div class="section-header">📋 جدول الانحرافات اليومية عن القياسي</div>', unsafe_allow_html=True)
    dev_df = df[["_date", "_age_num", "feed_per_bird", "std_feed_g", "water_per_bird_ml", "std_water_ml",
                 "temp_cur", "std_temp_max", "std_temp_min", "mortality_pct"]].copy()
    dev_df["انحراف العلف (جم)"] = (dev_df["feed_per_bird"] - dev_df["std_feed_g"]).round(1)
    dev_df["انحراف المياه (مل)"] = (dev_df["water_per_bird_ml"] - dev_df["std_water_ml"]).round(1)
    dev_df["حالة العلف"] = dev_df["انحراف العلف (جم)"].apply(
        lambda x: "✅ طبيعي" if abs(x) < dev_df["std_feed_g"].mean() * 0.1 else ("🔼 أعلى" if x > 0 else "🔽 أقل")
    )
    dev_df["حالة المياه"] = dev_df["انحراف المياه (مل)"].apply(
        lambda x: "✅ طبيعي" if abs(x) < dev_df["std_water_ml"].mean() * 0.1 else ("🔼 أعلى" if x > 0 else "🔽 أقل")
    )
    show_dev = dev_df[["_date", "_age_num", "feed_per_bird", "std_feed_g", "انحراف العلف (جم)", "حالة العلف",
                        "water_per_bird_ml", "std_water_ml", "انحراف المياه (مل)", "حالة المياه"]].copy()
    show_dev["_date"] = show_dev["_date"].dt.strftime("%Y/%m/%d")
    show_dev = show_dev.rename(columns={
        "_date": "التاريخ", "_age_num": "العمر",
        "feed_per_bird": "علف فعلي (جم)", "std_feed_g": "علف قياسي (جم)",
        "water_per_bird_ml": "ماء فعلي (مل)", "std_water_ml": "ماء قياسي (مل)",
    })
    st.dataframe(show_dev, use_container_width=True, hide_index=True)

    # Mortality comparison
    st.markdown('<div class="section-header">💀 مقارنة نسبة النفوق</div>', unsafe_allow_html=True)
    fig_mort = go.Figure()
    fig_mort.add_trace(go.Scatter(
        x=df["_age_num"], y=df["mortality_pct"],
        name="نسبة النفوق الفعلية %",
        mode="lines+markers",
        line=dict(color="#E74C3C", width=3),
    ))
    # H&N standard: max 5% cumulative by week 18
    std_mort = [0.5 * d / 14 for d in df["_age_num"]]
    fig_mort.add_trace(go.Scatter(
        x=df["_age_num"], y=std_mort,
        name="الحد القياسي H&N",
        mode="lines",
        line=dict(color="#F39C12", width=2, dash="dash"),
    ))
    fig_mort.update_layout(
        title="نسبة النفوق التراكمية مقارنة بالقياسي",
        xaxis_title="عمر القطيع (يوم)",
        yaxis_title="%",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(245,247,250,1)",
        font=dict(family="Cairo, Arial"),
    )
    st.plotly_chart(fig_mort, use_container_width=True)


# ── Auto Refresh ──────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(60)
    st.cache_data.clear()
    st.rerun()

# ── Footer ──────────────────────────────────────────────────────────────
st.divider()
st.caption("🐓 نظام مراقبة قطيع H&N Super Nick | مزرعة شديد | تم التطوير باستخدام Streamlit + Plotly")
