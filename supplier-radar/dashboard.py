"""Supplier Risk Radar — Dashboard profesional.

  streamlit run dashboard.py
"""
import io

import pandas as pd
import streamlit as st

from radar.config import LIVE, TEST, VALID
from radar.data import is_labelled, load_news, load_suppliers, load_materials
from radar.impact import eur, ids_of
from radar.pipeline import analyze_news, load_pool, save_excel

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Supplier Risk Radar", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

# ── Custom CSS (dark corporate / Accenture purple) ───────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Global */
.stApp { font-family: 'Inter', sans-serif; }

/* Header bar */
.header-bar {
    background: linear-gradient(135deg, #7B2FBE 0%, #A100FF 50%, #460073 100%);
    padding: 1.5rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.header-bar h1 { color: white; margin: 0; font-size: 1.8rem; font-weight: 700; }
.header-bar p { color: rgba(255,255,255,0.85); margin: 0.25rem 0 0 0; font-size: 0.9rem; }
.header-logo { font-size: 2.5rem; }

/* KPI cards */
.kpi-card {
    background: linear-gradient(145deg, #1a1a2e, #16213e);
    border: 1px solid rgba(123,47,190,0.3);
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(123,47,190,0.2); }
.kpi-value { font-size: 2rem; font-weight: 700; color: #A100FF; }
.kpi-label { font-size: 0.8rem; color: #999; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.3rem; }
.kpi-card.critical .kpi-value { color: #ff4d4d; }
.kpi-card.warn .kpi-value { color: #ffaa00; }
.kpi-card.ok .kpi-value { color: #00d4aa; }

/* Priority badges */
.badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.badge-critical { background: #ff4d4d22; color: #ff4d4d; border: 1px solid #ff4d4d44; }
.badge-high { background: #ff880022; color: #ff8800; border: 1px solid #ff880044; }
.badge-medium { background: #ffcc0022; color: #ffcc00; border: 1px solid #ffcc0044; }
.badge-low { background: #00d4aa22; color: #00d4aa; border: 1px solid #00d4aa44; }

/* Alert cards */
.alert-card {
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 0.8rem;
    border-left: 4px solid;
    background: rgba(26,26,46,0.6);
}
.alert-critical { border-left-color: #ff4d4d; background: rgba(255,77,77,0.05); }
.alert-high { border-left-color: #ff8800; background: rgba(255,136,0,0.05); }
.alert-medium { border-left-color: #ffcc00; background: rgba(255,204,0,0.05); }
.alert-low { border-left-color: #00d4aa; background: rgba(0,212,170,0.03); }

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f23, #1a1a2e);
    border-right: 1px solid rgba(123,47,190,0.2);
}
section[data-testid="stSidebar"] .stRadio label { color: #ccc; }

/* Accuracy banner */
.accuracy-bar {
    background: linear-gradient(90deg, rgba(0,212,170,0.1), rgba(123,47,190,0.1));
    border: 1px solid rgba(0,212,170,0.3);
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.accuracy-val { font-size: 1.3rem; font-weight: 700; color: #00d4aa; }

/* Tabs override */
.stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 0.5rem 1.5rem;
}

/* Supplier tag */
.sup-tag {
    display: inline-block;
    background: rgba(123,47,190,0.15);
    border: 1px solid rgba(123,47,190,0.3);
    border-radius: 6px;
    padding: 0.2rem 0.5rem;
    margin: 0.15rem;
    font-size: 0.8rem;
    color: #c89dff;
}

/* Action box */
.action-box {
    background: rgba(161,0,255,0.08);
    border: 1px solid rgba(161,0,255,0.25);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-top: 0.5rem;
    font-size: 0.85rem;
    color: #ddd;
}

/* Info row */
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin: 0.5rem 0; }
.info-item { font-size: 0.85rem; color: #bbb; }
.info-item strong { color: #eee; }
</style>
""", unsafe_allow_html=True)

# ── Data ─────────────────────────────────────────────────────────────────────
SUP = load_suppliers().set_index("Supplier_ID")
MAT = load_materials()
PRIORITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-bar">
    <div>
        <h1>🛡️ Supplier Risk Radar</h1>
        <p>AI-powered news monitoring for Helixa Pharmaceuticals' 40 critical suppliers</p>
    </div>
    <div class="header-logo">⚡</div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")
    st.divider()
    src = st.radio("📰 News Source", ["Live Day feed", "Test", "Validation (labelled)", "Upload Excel"],
                   help="Select the news feed to analyse")
    up = st.file_uploader("Upload news Excel", type=["xlsx"]) if src == "Upload Excel" else None
    st.divider()
    mode = st.selectbox("🤖 Engine", ["rules", "models"],
                        help="rules = keyword baseline (fast, no GPU); models = fine-tuned classifiers")
    st.divider()
    go = st.button("🚀 Analyse", type="primary", use_container_width=True)
    st.divider()
    st.markdown("##### 📊 Supplier Portfolio")
    st.metric("Total Suppliers", len(SUP))
    st.metric("Total Annual Spend", eur(SUP["Annual_Spend_EUR"].sum()))
    st.metric("Single-Source Suppliers", int((SUP["Single_Source"] == "Y").sum()))

# ── Run analysis ─────────────────────────────────────────────────────────────
if go:
    try:
        if src == "Upload Excel":
            if up is None:
                st.error("Upload an Excel file first.")
                st.stop()
            news = load_news(up)
        else:
            news = load_news({"Live Day feed": LIVE, "Test": TEST, "Validation (labelled)": VALID}[src])
        pool = load_pool(include_valid=(src != "Validation (labelled)"))
        with st.spinner("Analysing news articles..."):
            res = analyze_news(news, pool, mode)
        st.session_state["res"] = res
        st.session_state["news"] = news
    except Exception as e:
        st.error(f"Analysis failed: {e}")
        st.stop()

if "res" not in st.session_state:
    st.markdown("""
    <div style="text-align:center; padding: 4rem 2rem;">
        <p style="font-size: 3rem; margin-bottom: 1rem;">📡</p>
        <h3 style="color: #999;">Waiting for analysis</h3>
        <p style="color: #666;">Select a news source and click <strong>Analyse</strong> in the sidebar</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

res: pd.DataFrame = st.session_state["res"]
news: pd.DataFrame = st.session_state["news"]
res["_o"] = res["Priority"].map(PRIORITY_ORDER)
res = res.sort_values(["_o", "News_ID"]).drop(columns="_o").reset_index(drop=True)

# ── KPI Row ──────────────────────────────────────────────────────────────────
n_total = len(res)
n_risk = int((res.Is_Risk == "Y").sum())
n_urgent = int((res.Urgent == "Y").sum())
n_critical = int((res.Priority == "CRITICAL").sum())
spend = res.loc[res.Is_Risk == "Y", "Spend_At_Risk_EUR"].sum()
secs = res.attrs.get("seconds", 0)

cols = st.columns(6)
kpis = [
    ("📰", str(n_total), "Articles Scanned", ""),
    ("⚠️", str(n_risk), "Risks Detected", "warn" if n_risk > 0 else "ok"),
    ("🔴", str(n_critical), "Critical Alerts", "critical" if n_critical > 0 else "ok"),
    ("🚨", str(n_urgent), "Urgent Actions", "critical" if n_urgent > 0 else "ok"),
    ("💰", eur(spend), "Spend at Risk", "warn" if spend > 0 else "ok"),
    ("⏱️", f"{secs:.1f}s", "Processing Time", "ok"),
]
for col, (icon, val, label, cls) in zip(cols, kpis):
    col.markdown(f"""
    <div class="kpi-card {cls}">
        <div style="font-size:1.5rem;">{icon}</div>
        <div class="kpi-value">{val}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Accuracy (if labelled) ───────────────────────────────────────────────────
if is_labelled(news):
    g = news.set_index("News_ID")
    m = res.set_index("News_ID")
    acc_r = (m.Is_Risk == g.loc[m.index, "Is_Risk"]).mean()
    acc_u = (m.Urgent == g.loc[m.index, "Urgent"]).mean()
    st.markdown(f"""
    <div class="accuracy-bar">
        <span style="font-size:1.3rem;">🎯</span>
        <span style="color:#ccc;">Accuracy vs expert labels:</span>
        <span class="accuracy-val">Is_Risk {acc_r:.0%}</span>
        <span style="color:#666;">|</span>
        <span class="accuracy-val">Urgent {acc_u:.0%}</span>
    </div>
    """, unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_alerts, tab_suppliers, tab_data = st.tabs(["🚨 Alerts", "🏭 Supplier Map", "📋 Raw Data"])

# ── Tab 1: Alerts ────────────────────────────────────────────────────────────
with tab_alerts:
    col_filter, col_search = st.columns([1, 2])
    with col_filter:
        show = st.multiselect("Filter by priority", ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                               default=["CRITICAL", "HIGH", "MEDIUM"])
    with col_search:
        q = st.text_input("🔍 Search headlines", placeholder="fire, strike, export...")

    view = res[res.Priority.isin(show)] if show else res
    if q:
        view = view[view.Headline.str.contains(q, case=False, na=False) |
                     view.get("Reasoning", pd.Series(dtype=str)).str.contains(q, case=False, na=False)]

    for r in view.itertuples():
        prio_lower = r.Priority.lower()
        badge_cls = f"badge-{prio_lower}"
        st.markdown(f"""
        <div class="alert-card alert-{prio_lower}">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                <div>
                    <span class="badge {badge_cls}">{r.Priority}</span>
                    <span style="color:#888; margin-left:0.5rem; font-size:0.8rem;">{r.News_ID}</span>
                </div>
                <span style="color:#888; font-size:0.75rem;">Confidence: {r.Confidence}</span>
            </div>
            <div style="font-size:1rem; font-weight:600; color:#eee; margin-bottom:0.4rem;">{r.Headline}</div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("View details", expanded=(r.Priority == "CRITICAL")):
            text = news.loc[news.News_ID == r.News_ID, "Summary"].iloc[0]
            st.markdown(f"<p style='color:#bbb; font-size:0.9rem;'>{text}</p>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                risk_icon = "🔴" if r.Is_Risk == "Y" else "🟢"
                urgent_icon = "🔴" if r.Urgent == "Y" else "⚪"
                st.markdown(f"""
                <div class="info-grid">
                    <div class="info-item">{risk_icon} <strong>Risk:</strong> {'Yes' if r.Is_Risk == 'Y' else 'No'}</div>
                    <div class="info-item">{urgent_icon} <strong>Urgent:</strong> {'Yes' if r.Urgent == 'Y' else 'No'}</div>
                    <div class="info-item">📌 <strong>Event:</strong> {r.Event_Type}</div>
                    <div class="info-item">💰 <strong>Spend at risk:</strong> {eur(r.Spend_At_Risk_EUR) if r.Is_Risk == 'Y' else 'N/A'}</div>
                </div>
                """, unsafe_allow_html=True)

                ids = ids_of(r.Affected_Supplier_IDs)
                if ids:
                    tags = "".join(
                        f'<span class="sup-tag">{i} — {SUP.loc[i, "Supplier_Name"]} ({SUP.loc[i, "City"]})</span>'
                        for i in ids if i in SUP.index
                    )
                    st.markdown(f"**Affected suppliers:** {tags}", unsafe_allow_html=True)

                if hasattr(r, "Products_At_Risk") and r.Products_At_Risk:
                    st.markdown(f"**Products at risk:** {r.Products_At_Risk}")

            with c2:
                if r.Is_Risk == "Y":
                    inv = r.Min_Inventory_Days
                    dur = r.Duration_Days
                    inv_str = f"{inv:.0f} days" if inv == inv and inv is not None else "unknown"
                    dur_str = f"{dur:.0f} days" if dur == dur and dur is not None else "not stated"
                    st.markdown(f"""
                    <div class="info-grid">
                        <div class="info-item">📦 <strong>Inventory cover:</strong> {inv_str}</div>
                        <div class="info-item">⏳ <strong>Est. duration:</strong> {dur_str}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if hasattr(r, "Action") and r.Action:
                        st.markdown(f'<div class="action-box">💡 <strong>Recommended action:</strong> {r.Action}</div>',
                                    unsafe_allow_html=True)

            st.caption(f"Reasoning: {r.Reasoning}")

# ── Tab 2: Supplier Map ─────────────────────────────────────────────────────
with tab_suppliers:
    st.markdown("### Supplier Portfolio Overview")

    affected_ids = set()
    for _, row in res[res.Is_Risk == "Y"].iterrows():
        affected_ids.update(ids_of(row["Affected_Supplier_IDs"]))

    sup_view = SUP.copy()
    sup_view["Status"] = sup_view.index.map(lambda i: "⚠️ AT RISK" if i in affected_ids else "✅ OK")
    sup_view["Spend_M"] = (sup_view["Annual_Spend_EUR"] / 1e6).round(2)

    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        display_cols = ["Supplier_Name", "Status", "Country", "City", "Material_Supplied",
                        "Spend_M", "Single_Source", "Criticality", "Inventory_Cover_Days"]
        st.dataframe(
            sup_view[display_cols].sort_values("Status", ascending=False),
            use_container_width=True, hide_index=False,
            column_config={
                "Spend_M": st.column_config.NumberColumn("Spend (M EUR)", format="%.2f"),
                "Inventory_Cover_Days": st.column_config.NumberColumn("Inv. Days", format="%.0f"),
            }
        )

    with col_s2:
        st.markdown("##### Risk Summary")
        st.metric("Suppliers at Risk", len(affected_ids))
        st.metric("Spend at Risk", eur(sup_view.loc[sup_view.index.isin(affected_ids), "Annual_Spend_EUR"].sum()))
        st.metric("Single-Source at Risk", len([i for i in affected_ids if i in SUP.index and SUP.loc[i, "Single_Source"] == "Y"]))

        st.markdown("##### By Country")
        country_risk = sup_view[sup_view.index.isin(affected_ids)].groupby("Country").size().sort_values(ascending=False)
        if len(country_risk):
            st.bar_chart(country_risk)

# ── Tab 3: Raw Data ──────────────────────────────────────────────────────────
with tab_data:
    st.markdown("### Full Results Table")
    display_res_cols = ["Priority", "News_ID", "Headline", "Is_Risk", "Urgent", "Affected_Supplier_IDs",
                        "Event_Type", "Spend_At_Risk_EUR", "Confidence", "Reasoning"]
    available = [c for c in display_res_cols if c in res.columns]
    st.dataframe(res[available], use_container_width=True, hide_index=True)

    st.divider()
    buf = io.BytesIO()
    save_excel(res, buf)
    st.download_button("📥 Download Excel (Results + Details)", buf.getvalue(), "supplier_risk_result.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       use_container_width=True)
