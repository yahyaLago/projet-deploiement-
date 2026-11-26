"""Lecture du fichier de mesures et découpage entraînement / test."""
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from maintai.config import FEATURES, SEED, TARGET

COLONNES_ATTENDUES = FEATURES + [TARGET]


def load_data(path: Path) -> pd.DataFrame:
    """Charge le CSV et refuse un fichier auquel il manque une colonne."""
    df = pd.read_csv(path)
    manquantes = [colonne for colonne in COLONNES_ATTENDUES if colonne not in df.columns]
    if manquantes:
        raise ValueError(f"Colonnes manquantes dans {path} : {manquantes}")
    return df


def split(df: pd.DataFrame, test_size: float = 0.2):
    """Sépare les données en gardant la même proportion de pannes de chaque côté."""
    return train_test_split(
        df[FEATURES],
        df[TARGET],
        test_size=test_size,
        stratify=df[TARGET],
        random_state=SEED,
    )
