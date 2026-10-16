"""Panel de alertas del Supplier Risk Radar.

  python3 -m streamlit run dashboard.py --server.port 8501 --server.headless true \
      --server.enableCORS false --server.enableXsrfProtection false
"""
import io

import pandas as pd
import streamlit as st

from radar.config import LIVE, TEST, VALID
from radar.data import is_labelled, load_news, load_suppliers
from radar.impact import eur, ids_of
from radar.pipeline import analyze_news, load_pool, save_excel

st.set_page_config(page_title="Supplier Risk Radar", layout="wide")
st.title("Supplier Risk Radar")
st.caption("Monitor de noticias de riesgo para los 40 proveedores de Helixa Pharmaceuticals")

SUP = load_suppliers().set_index("Supplier_ID")
COLORS = {"CRITICAL": "#f4a6a6", "HIGH": "#f8cbad", "MEDIUM": "#ffe699", "LOW": "#ffffff"}
ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

with st.sidebar:
    st.header("Entrada")
    src = st.radio("Fuente", ["Live Day feed", "Test", "Validación (con respuestas)", "Subir Excel"])
    up = st.file_uploader("Excel de noticias", type=["xlsx"]) if src == "Subir Excel" else None
    mode = st.selectbox("Motor", ["models", "rules"], help="models = nuestros modelos afinados; rules = línea base sin modelos")
    go = st.button("Analizar", type="primary", use_container_width=True)

if go:
    try:
        if src == "Subir Excel":
            if up is None:
                st.error("Sube un Excel primero.")
                st.stop()
            news = load_news(up)
        else:
            news = load_news({"Live Day feed": LIVE, "Test": TEST, "Validación (con respuestas)": VALID}[src])
        pool = load_pool(include_valid=(src != "Validación (con respuestas)"))
        with st.spinner("Analizando noticias..."):
            res = analyze_news(news, pool, mode)
        st.session_state["res"], st.session_state["news"] = res, news
    except Exception as e:  # noqa: BLE001
        st.error(f"No se pudo analizar: {e}")
        st.stop()

if "res" not in st.session_state:
    st.info("Elige una fuente y pulsa **Analizar**.")
    st.stop()

res: pd.DataFrame = st.session_state["res"]
news: pd.DataFrame = st.session_state["news"]
res["_o"] = res["Priority"].map(ORDER)
res = res.sort_values(["_o", "News_ID"]).drop(columns="_o").reset_index(drop=True)

k = st.columns(5)
k[0].metric("Noticias", len(res))
k[1].metric("Riesgos", int((res.Is_Risk == "Y").sum()))
k[2].metric("Urgentes", int((res.Urgent == "Y").sum()))
k[3].metric("Gasto anual en riesgo", eur(res.loc[res.Is_Risk == "Y", "Spend_At_Risk_EUR"].sum()))
k[4].metric("Tiempo", f"{res.attrs.get('seconds', 0):.1f} s")

if is_labelled(news):
    g = news.set_index("News_ID")
    m = res.set_index("News_ID")
    acc_r = (m.Is_Risk == g.loc[m.index, "Is_Risk"]).mean()
    acc_u = (m.Urgent == g.loc[m.index, "Urgent"]).mean()
    st.success(f"Contra las respuestas del fichero: Is_Risk {acc_r:.0%} · Urgent {acc_u:.0%}")

st.subheader("Alertas")
only_risk = st.checkbox("Mostrar solo riesgos", value=True)
view = res[res.Is_Risk == "Y"] if only_risk else res
cols = ["Priority", "News_ID", "Headline", "Is_Risk", "Urgent", "Affected_Supplier_IDs", "Event_Type", "Spend_At_Risk_EUR", "Confidence"]
try:
    st.dataframe(view[cols].style.apply(lambda r: [f"background-color: {COLORS[r.Priority]}"] * len(r), axis=1),
                 use_container_width=True, hide_index=True)
except Exception:  # noqa: BLE001
    st.dataframe(view[cols], use_container_width=True, hide_index=True)

st.subheader("Detalle")
for r in view.itertuples():
    label = f"{r.Priority} · {r.News_ID} · {r.Headline}"
    with st.expander(label, expanded=(r.Priority == "CRITICAL")):
        text = news.loc[news.News_ID == r.News_ID, "Summary"].iloc[0]
        st.write(text)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Riesgo:** {'sí' if r.Is_Risk == 'Y' else 'no'} · **Urgente:** {'sí' if r.Urgent == 'Y' else 'no'} · **Tipo:** {r.Event_Type}")
            ids = ids_of(r.Affected_Supplier_IDs)
            if ids:
                st.markdown("**Proveedores:** " + ", ".join(f"{i} {SUP.loc[i, 'Supplier_Name']} ({SUP.loc[i, 'City']})" for i in ids if i in SUP.index))
            if r.Products_At_Risk:
                st.markdown(f"**Productos afectados:** {r.Products_At_Risk}")
        with c2:
            if r.Is_Risk == "Y":
                st.markdown(f"**Gasto anual:** {eur(r.Spend_At_Risk_EUR)}")
                if r.Min_Inventory_Days == r.Min_Inventory_Days and r.Min_Inventory_Days is not None:
                    st.markdown(f"**Inventario (peor caso):** {r.Min_Inventory_Days:.0f} días · **Duración estimada:** "
                                + (f"{r.Duration_Days:.0f} días" if r.Duration_Days == r.Duration_Days and r.Duration_Days is not None else "no indicada"))
                st.markdown(f"**Acción recomendada:** {r.Action}")
        st.caption(f"Confianza {r.Confidence} · {r.Reasoning}")

buf = io.BytesIO()
save_excel(res, buf)
st.download_button("Descargar Excel (Results + Details)", buf.getvalue(), "supplier_risk_result.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
