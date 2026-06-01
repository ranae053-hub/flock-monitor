"""
وظائف عرض لوحة التحكم والرسوم البيانية
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from data_loader import INITIAL_BIRDS, get_standard_for_age


# ── KPI Cards ──────────────────────────────────────────────────────────────

def render_kpi_cards(df):
    latest = df.iloc[-1]
    age = int(latest["_age_num"])
    week = int(latest["week"])
    birds = int(latest["current_birds"])
    cum_mort = int(latest["cum_mortality"])
    mort_pct = latest["mortality_pct"]

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("🐣 عمر القطيع", f"{age} يوم", f"أسبوع {week}")
    with c2:
        st.metric("🐓 عدد الطيور", f"{birds:,}", f"-{int(latest['mortality'])} اليوم" if pd.notna(latest["mortality"]) else "")
    with c3:
        st.metric("💀 إجمالي النافق", f"{cum_mort:,}", f"{mort_pct:.2f}%")
    with c4:
        feed = latest["feed_per_bird"]
        std_feed = latest["std_feed_g"]
        delta_feed = f"{feed - std_feed:+.1f} جم" if pd.notna(feed) else ""
        st.metric("🌾 علف/طائر", f"{feed:.1f} جم" if pd.notna(feed) else "—", delta_feed)
    with c5:
        water = latest["water_per_bird_ml"]
        std_water = latest["std_water_ml"]
        delta_water = f"{water - std_water:+.1f} مل" if pd.notna(water) else ""
        st.metric("💧 ماء/طائر", f"{water:.1f} مل" if pd.notna(water) else "—", delta_water)

    c6, c7, c8, c9, c10 = st.columns(5)
    with c6:
        st.metric("🌡️ الحرارة الحالية", f"{latest['temp_cur']:.1f}°م" if pd.notna(latest["temp_cur"]) else "—")
    with c7:
        st.metric("🌡️ الحرارة القصوى", f"{latest['temp_max']:.1f}°م" if pd.notna(latest["temp_max"]) else "—")
    with c8:
        st.metric("🌡️ الحرارة الدنيا", f"{latest['temp_min']:.1f}°م" if pd.notna(latest["temp_min"]) else "—")
    with c9:
        st.metric("💦 الرطوبة الحالية", f"{latest['hum_cur']:.0f}%" if pd.notna(latest["hum_cur"]) else "—")
    with c10:
        total_feed = latest["feed_kg"]
        total_water = latest["water_l"]
        st.metric("🌾 علف اليوم", f"{total_feed:.1f} كجم" if pd.notna(total_feed) else "—",
                  f"ماء: {total_water:.0f} ل" if pd.notna(total_water) else "")


# ── Trend Charts ───────────────────────────────────────────────────────────

def _base_layout(title):
    return dict(
        title=dict(text=title, font=dict(size=16, color="#2C3E50"), x=0.5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(245,247,250,1)",
        font=dict(family="Cairo, Arial", size=12),
        margin=dict(t=50, b=40, l=50, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )


def chart_temperature(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["_age_num"], y=df["temp_cur"], name="الحرارة الحالية",
                             mode="lines+markers", line=dict(color="#E74C3C", width=2)))
    fig.add_trace(go.Scatter(x=df["_age_num"], y=df["temp_max"], name="الحرارة القصوى",
                             mode="lines", line=dict(color="#FF8C00", dash="dot")))
    fig.add_trace(go.Scatter(x=df["_age_num"], y=df["temp_min"], name="الحرارة الدنيا",
                             mode="lines", line=dict(color="#3498DB", dash="dot")))
    fig.add_trace(go.Scatter(x=df["_age_num"], y=df["std_temp_max"], name="الحد الأقصى القياسي",
                             mode="lines", line=dict(color="#E74C3C", dash="dash", width=1),
                             opacity=0.5))
    fig.update_layout(**_base_layout("📈 اتجاه درجة الحرارة اليومية"),
                      xaxis_title="عمر القطيع (يوم)", yaxis_title="°مئوية")
    return fig


def chart_humidity(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["_age_num"], y=df["hum_cur"], name="الرطوبة الحالية",
                             mode="lines+markers", line=dict(color="#2980B9", width=2),
                             fill="tozeroy", fillcolor="rgba(41,128,185,0.1)"))
    fig.add_trace(go.Scatter(x=df["_age_num"], y=df["std_hum_max"], name="الحد الأقصى القياسي",
                             mode="lines", line=dict(color="#E74C3C", dash="dash")))
    fig.update_layout(**_base_layout("💦 اتجاه الرطوبة اليومية"),
                      xaxis_title="عمر القطيع (يوم)", yaxis_title="%")
    return fig


def chart_feed(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["_age_num"], y=df["feed_per_bird"], name="الفعلي",
                         marker_color="#27AE60", opacity=0.8))
    fig.add_trace(go.Scatter(x=df["_age_num"], y=df["std_feed_g"], name="القياسي",
                             mode="lines+markers", line=dict(color="#E74C3C", width=2, dash="dash")))
    fig.update_layout(**_base_layout("🌾 استهلاك العلف لكل طائر"),
                      xaxis_title="عمر القطيع (يوم)", yaxis_title="جرام/طائر")
    return fig


def chart_water(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["_age_num"], y=df["water_per_bird_ml"], name="الفعلي",
                         marker_color="#2980B9", opacity=0.8))
    fig.add_trace(go.Scatter(x=df["_age_num"], y=df["std_water_ml"], name="القياسي",
                             mode="lines+markers", line=dict(color="#E74C3C", width=2, dash="dash")))
    fig.update_layout(**_base_layout("💧 استهلاك المياه لكل طائر"),
                      xaxis_title="عمر القطيع (يوم)", yaxis_title="مل/طائر")
    return fig


def chart_mortality(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["_age_num"], y=df["mortality"], name="النافق اليومي",
                         marker_color="#E74C3C", opacity=0.75))
    fig.add_trace(go.Scatter(x=df["_age_num"], y=df["cum_mortality"], name="التراكمي",
                             mode="lines+markers", yaxis="y2",
                             line=dict(color="#8E44AD", width=2)))
    fig.update_layout(
        **_base_layout("💀 النافق اليومي والتراكمي"),
        xaxis_title="عمر القطيع (يوم)",
        yaxis=dict(title="نافق يومي"),
        yaxis2=dict(title="نافق تراكمي", overlaying="y", side="right"),
    )
    return fig


def chart_health_score(df):
    colors = ["#E74C3C" if s < 50 else "#F39C12" if s < 70 else "#27AE60" for s in df["health_score"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["_age_num"], y=df["health_score"], name="مؤشر الصحة",
                         marker_color=colors))
    fig.add_hline(y=70, line_dash="dash", line_color="#F39C12", annotation_text="حد مقبول (70)")
    fig.add_hline(y=85, line_dash="dash", line_color="#27AE60", annotation_text="ممتاز (85)")
    fig.update_layout(**_base_layout("🏥 مؤشر صحة القطيع اليومي"),
                      xaxis_title="عمر القطيع (يوم)", yaxis_title="الدرجة / 100",
                      yaxis_range=[0, 105])
    return fig


def chart_weekly_summary(weekly_df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=weekly_df["week"].astype(str).apply(lambda w: f"أسبوع {w}"),
                         y=weekly_df["total_feed_kg"], name="إجمالي العلف (كجم)",
                         marker_color="#27AE60"))
    fig.add_trace(go.Bar(x=weekly_df["week"].astype(str).apply(lambda w: f"أسبوع {w}"),
                         y=weekly_df["total_water_l"] / 10, name="إجمالي المياه (×10 لتر)",
                         marker_color="#2980B9"))
    fig.update_layout(**_base_layout("📊 ملخص أسبوعي: العلف والمياه"),
                      barmode="group")
    return fig


# ── Alert Badges ───────────────────────────────────────────────────────────

def render_alerts(alerts):
    if not alerts:
        st.success("✅ لا توجد تنبيهات حالياً — القطيع في حالة جيدة")
        return
    for a in alerts:
        severity_icon = "🚨" if a["severity"] in ["خطر", "خطر شديد"] else "⚠️"
        with st.expander(f"{severity_icon} {a['category']} — {a['severity']}", expanded=True):
            st.markdown(f"**{a['message']}**")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**الأسباب المحتملة:**")
                for c in a["causes"]:
                    st.markdown(f"• {c}")
            with col2:
                st.markdown("**التوصيات:**")
                for r in a["recommendations"]:
                    st.markdown(f"✔️ {r}")


# ── Gauge ──────────────────────────────────────────────────────────────────

def render_health_gauge(score, status_text, status_color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "مؤشر صحة القطيع", "font": {"size": 20, "family": "Cairo"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": status_color},
            "steps": [
                {"range": [0, 40], "color": "#FADBD8"},
                {"range": [40, 55], "color": "#FDEBD0"},
                {"range": [55, 70], "color": "#FEF9E7"},
                {"range": [70, 85], "color": "#EAFAF1"},
                {"range": [85, 100], "color": "#D5F5E3"},
            ],
            "threshold": {"line": {"color": "black", "width": 3}, "value": score},
        },
    ))
    fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Cairo, Arial"))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"<h3 style='text-align:center;color:{status_color}'>{status_text}</h3>",
                unsafe_allow_html=True)
