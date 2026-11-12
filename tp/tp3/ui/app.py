"""Interface Streamlit de MaintAI : explorer les données, puis demander une prédiction à l'API.

Lancement (depuis la racine du projet) : python -m streamlit run ui/app.py
"""
import httpx
import pandas as pd
import streamlit as st

from maintai.client import APIError, MaintaiClient
from maintai.config import FEATURES, get_settings

st.set_page_config(page_title="MaintAI — Yahya Baid", page_icon="🔧")
st.title("MaintAI · prédiction de panne")
st.caption("TP3 · Yahya Baid")


@st.cache_data
def charger(path) -> pd.DataFrame:
    # Lu une seule fois : Streamlit relance tout le script à chaque clic
    return pd.read_csv(path)


with st.sidebar:
    url = st.text_input("URL de l'API", "http://127.0.0.1:8001")
    cle = st.text_input("Clé API", type="password")

onglet_donnees, onglet_prediction = st.tabs(["Données", "Prédiction"])

# Sprint 1 : explorer les données
with onglet_donnees:
    df = charger(get_settings().data_path)

    n_rows = len(df)
    failure_rate = df["failure"].mean()
    avg_temp = df["temperature_c"].mean()

    cols = st.columns(3)
    cols[0].metric("Relevés", n_rows)
    cols[1].metric("Taux de panne", f"{failure_rate * 100:.1f} %")
    cols[2].metric("Température moyenne", f"{avg_temp:.1f} °C")

    feature = st.selectbox("Variable à analyser", FEATURES)
    bins = pd.qcut(df[feature], q=5, duplicates="drop")
    taux_par_tranche = (
        df.assign(_tranche=bins)
        .groupby("_tranche")["failure"]
        .mean()
        .mul(100)
        .rename("taux_panne")
        .to_frame()
    )
    taux_par_tranche.index = taux_par_tranche.index.map(str)
    st.bar_chart(taux_par_tranche)

    st.scatter_chart(df, x="temperature_c", y="vibration_mm_s", color="failure")


# Sprint 2 : demander une prédiction à l'API
with onglet_prediction:
    with st.form("releve"):
        releve = {
            "temperature_c": st.slider("Température (°C)", -40.0, 150.0, 72.0),
            "vibration_mm_s": st.slider("Vibration (mm/s)", 0.0, 50.0, 6.0),
            "load_pct": st.slider("Charge (%)", 0.0, 100.0, 85.0),
            "runtime_hours": st.number_input("Heures de fonctionnement", 0, 100_000, 15000),
        }
        envoye = st.form_submit_button("Prédire")

    if envoye:
        try:
            api = MaintaiClient(url, api_key=cle)
            result = api.predict(releve)
        except APIError as exc:
            st.warning(f"Erreur {exc.status_code} : {exc.detail}")
        except httpx.HTTPError as exc:
            st.error(f"API injoignable : {exc}")
        else:
            pct = int(round(result["failure_probability"] * 100))
            st.metric("Probabilité de panne", f"{pct} %")
            if result["alert"]:
                st.error(f"ALERTE : probabilité de panne {pct}% (seuil {result['threshold']*100:.0f}%)")
            else:
                st.success(f"Système normal : probabilité de panne {pct}% (seuil {result['threshold']*100:.0f}%)")
