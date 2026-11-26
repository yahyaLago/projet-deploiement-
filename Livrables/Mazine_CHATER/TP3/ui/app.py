"""Interface Streamlit de MaintAI : explorer les données puis interroger l'API.

Lancement, depuis la racine du projet :

    python -m streamlit run ui/app.py
"""
import httpx
import pandas as pd
import streamlit as st

from maintai.client import APIError, MaintaiClient
from maintai.config import FEATURES, get_settings

st.set_page_config(page_title="MaintAI", page_icon="🔧")
st.title("MaintAI — prédiction de panne")


@st.cache_data
def lire_donnees(path) -> pd.DataFrame:
    """Streamlit relance le script à chaque interaction : on lit le CSV une fois."""
    return pd.read_csv(path)


def afficher_donnees() -> None:
    df = lire_donnees(get_settings().data_path)

    colonnes = st.columns(3)
    colonnes[0].metric("Relevés", len(df))
    colonnes[1].metric("Taux de panne", f"{df['failure'].mean():.1%}")
    colonnes[2].metric("Température moyenne", f"{df['temperature_c'].mean():.1f} °C")

    variable = st.selectbox("Variable", FEATURES)
    tranches = pd.cut(df[variable], bins=10)
    taux = df.groupby(tranches, observed=True)["failure"].mean()
    taux.index = [round(tranche.mid) for tranche in taux.index]
    st.subheader(f"Taux de panne selon {variable}")
    st.bar_chart(taux)

    st.subheader("Température et vibration (500 relevés)")
    echantillon = df.sample(min(500, len(df)), random_state=0)
    echantillon = echantillon.assign(
        panne=echantillon["failure"].map({0: "non", 1: "oui"})
    )
    st.scatter_chart(
        echantillon, x="temperature_c", y="vibration_mm_s", color="panne"
    )


def afficher_prediction(url: str, cle: str) -> None:
    with st.form("releve"):
        releve = {
            "temperature_c": st.slider("Température (°C)", -40.0, 150.0, 72.0),
            "vibration_mm_s": st.slider("Vibration (mm/s)", 0.0, 50.0, 6.0),
            "load_pct": st.slider("Charge (%)", 0.0, 100.0, 85.0),
            "runtime_hours": st.number_input(
                "Heures de fonctionnement", 0, 100_000, 15000
            ),
        }
        envoye = st.form_submit_button("Prédire")

    if not envoye:
        return

    try:
        resultat = MaintaiClient(url, api_key=cle).predict(releve)
    except APIError as erreur:
        st.warning(f"Erreur {erreur.status_code} : {erreur.detail}")
        return
    except httpx.HTTPError:
        st.error("API injoignable : uvicorn est-il lancé ?")
        return

    pourcentage = round(resultat["failure_probability"] * 100)
    st.metric("Probabilité de panne", f"{pourcentage} %")
    if resultat["alert"]:
        st.error(f"ALERTE : au-dessus du seuil {resultat['threshold']}")
    else:
        st.success(f"Normal : sous le seuil {resultat['threshold']}")


with st.sidebar:
    url_api = st.text_input("URL de l'API", "http://localhost:8000")
    cle_api = st.text_input("Clé API", type="password")

onglet_donnees, onglet_prediction = st.tabs(["Données", "Prédiction"])
with onglet_donnees:
    afficher_donnees()
with onglet_prediction:
    afficher_prediction(url_api, cle_api)
