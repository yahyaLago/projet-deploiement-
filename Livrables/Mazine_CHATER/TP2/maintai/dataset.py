"""Génère un jeu de données de capteurs synthétique.

Le projet doit pouvoir tourner sans téléchargement : les mesures sont
simulées. Pour utiliser de vraies données, il suffit de garder les mêmes
colonnes que celles produites ici.

    python -m maintai.dataset
    python -m maintai.dataset --n 8000 --seed 7
"""
import argparse
import sys

import numpy as np
import pandas as pd

from maintai.config import SEED, TARGET, get_settings


def make_dataset(n: int = 5000, seed: int = SEED) -> pd.DataFrame:
    """Simule n relevés de capteurs et leur étiquette de panne."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "temperature_c": rng.normal(60, 10, n).round(1),
        "vibration_mm_s": rng.gamma(2.0, 1.5, n).round(2),
        "load_pct": rng.uniform(20, 100, n).round(1),
        "runtime_hours": rng.uniform(0, 20_000, n).round(0),
    })

    # Le risque augmente avec la chaleur, les vibrations, la charge et l'âge.
    risque = (
        0.08 * (df["temperature_c"] - 60)
        + 0.6 * (df["vibration_mm_s"] - 3)
        + 0.03 * (df["load_pct"] - 60)
        + 0.00008 * (df["runtime_hours"] - 10_000)
    )
    df[TARGET] = (risque + rng.normal(0, 1, n) > 2.2).astype(int)
    return df


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m maintai.dataset")
    parser.add_argument("--n", type=int, default=5000, help="nombre de relevés")
    parser.add_argument("--seed", type=int, default=SEED, help="graine du générateur")
    args = parser.parse_args(argv)

    path = get_settings().data_path
    path.parent.mkdir(parents=True, exist_ok=True)
    df = make_dataset(args.n, args.seed)
    df.to_csv(path, index=False)
    print(
        f"{len(df)} relevés écrits dans {path} "
        f"(taux de panne : {df[TARGET].mean():.1%})"
    )


if __name__ == "__main__":
    main(sys.argv[1:])
