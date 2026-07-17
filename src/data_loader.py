"""
BAg-IDS — Chargement et préparation des données CICIDS2017.

Reproduit le pipeline de prétraitement décrit dans le manuscrit :
split stratifié 70/15/15 et normalisation StandardScaler.
"""

from __future__ import annotations

import logging

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

logger = logging.getLogger("bag_ids.data")


def load_dataset(cfg: dict):
    """Charge le(s) CSV, nettoie, encode les labels et split en 70/15/15.

    Retourne un dictionnaire contenant les splits, l'encodeur de labels
    et le scaler utilisé.
    """
    data_cfg = cfg["data"]
    split_cfg = cfg["split"]
    label_col = data_cfg["label_column"].strip()
    drop_cols = [c.strip() for c in data_cfg.get("drop_columns", [])]

    # Chaque CSV est nettoyé et réduit à des colonnes float32 avant d'être
    # concaténé aux autres : sur un gros dataset (CICIDS2018, 8M+ lignes),
    # garder plusieurs DataFrames complets en float64 simultanément épuise
    # la RAM disponible (observé : ~9 Go rien que pour le 1er des 9 fichiers,
    # avec swap disque massif). Convertir fichier par fichier limite le pic
    # mémoire à un seul fichier à la fois plutôt qu'à la somme de tous.
    frames = []
    n_header_rows_total = 0
    for path in data_cfg["csv_paths"]:
        logger.info("Lecture de %s ...", path)
        df = pd.read_csv(path, low_memory=False)
        df.columns = df.columns.str.strip()
        if label_col not in df.columns:
            raise KeyError(
                f"Colonne label '{label_col}' introuvable dans {path}. "
                f"Colonnes disponibles : {list(df.columns)[:10]}..."
            )
        df = df.drop(columns=[c for c in drop_cols if c in df.columns])

        # Bug connu CICIDS2018 : des lignes d'en-tête sont dupliquées au
        # milieu de certains CSV (la valeur de la colonne label y vaut
        # littéralement le nom de la colonne, ex. "Label"). Elles polluent
        # aussi les colonnes de features (dtype "object" au lieu de
        # numérique) si on ne les retire pas avant la conversion numérique.
        n_before = len(df)
        df = df[df[label_col].astype(str).str.strip() != label_col]
        n_header_rows_total += n_before - len(df)

        y_raw = df[label_col].astype(str).str.strip()
        X = df.drop(columns=[label_col])
        del df
        # Conversion numérique explicite, mais seulement pour les colonnes
        # dtype "object" (contaminées par des valeurs non numériques) :
        # repasser pd.to_numeric sur des colonnes déjà float/int est inutile.
        object_cols = X.select_dtypes(include="object").columns
        if len(object_cols):
            X[object_cols] = X[object_cols].apply(pd.to_numeric, errors="coerce")
        # Colonnes réellement non numériques (ex. Timestamp) : devenues 100%
        # NaN après la coercion ci-dessus -> à exclure, sans quoi le dropna()
        # global supprimerait toutes les lignes du dataset.
        X = X.dropna(axis=1, how="all")
        X = X.select_dtypes(include=[np.number]).astype(np.float32)

        frames.append(pd.concat([X, y_raw.rename(label_col)], axis=1))
        del X, y_raw

    if n_header_rows_total:
        logger.info("Lignes d'en-tête dupliquées supprimées : %d", n_header_rows_total)

    df = pd.concat(frames, ignore_index=True)
    del frames
    logger.info("Dataset brut : %d lignes, %d colonnes", *df.shape)
    logger.info("Features numériques retenues : %d", df.shape[1] - 1)

    df = df.replace([np.inf, -np.inf], np.nan)
    n_before = len(df)
    df = df.dropna()
    logger.info("Lignes supprimées (inf/NaN) : %d", n_before - len(df))

    y_raw = df[label_col]
    X = df.drop(columns=[label_col])
    del df

    encoder = LabelEncoder()
    y = encoder.fit_transform(y_raw)
    logger.info("Classes (%d) : %s", len(encoder.classes_), list(encoder.classes_))

    # ---- Split stratifié 70 / 15 / 15 ----
    seed = split_cfg["seed"]
    test_size = split_cfg["test"]
    val_size = split_cfg["val"] / (1.0 - test_size)
    strat = y if split_cfg.get("stratify", True) else None

    X_tmp, X_test, y_tmp, y_test = train_test_split(
        X.values, y, test_size=test_size, random_state=seed, stratify=strat
    )
    strat_tmp = y_tmp if split_cfg.get("stratify", True) else None
    X_train, X_val, y_train, y_val = train_test_split(
        X_tmp, y_tmp, test_size=val_size, random_state=seed, stratify=strat_tmp
    )

    # ---- Normalisation ----
    scaler_path = data_cfg.get("scaler_path")
    if scaler_path:
        logger.info("Chargement du scaler d'entraînement : %s", scaler_path)
        scaler = joblib.load(scaler_path)
    else:
        logger.warning(
            "Aucun scaler fourni : re-fit d'un StandardScaler sur le split train. "
            "Assurez-vous que cela correspond au prétraitement d'entraînement "
            "des modèles (voir README)."
        )
        scaler = StandardScaler().fit(X_train)

    X_train = scaler.transform(X_train).astype(np.float32)
    X_val = scaler.transform(X_val).astype(np.float32)
    X_test = scaler.transform(X_test).astype(np.float32)

    logger.info(
        "Splits — train: %d, val: %d, test: %d",
        len(X_train), len(X_val), len(X_test),
    )

    return {
        "X_train": X_train, "y_train": y_train,
        "X_val": X_val, "y_val": y_val,
        "X_test": X_test, "y_test": y_test,
        "encoder": encoder,
        "scaler": scaler,
        "class_names": list(encoder.classes_),
    }


def reshape_for_model(model, X: np.ndarray) -> np.ndarray:
    """Adapte automatiquement la forme de X à l'entrée attendue du modèle.

    Les modèles du manuscrit ont des entrées différentes :
    DNN -> (n, F) ; RNN/CNN -> (n, F, 1) ou variantes (n, t, f).
    On lit model.input_shape et on reshape si le nombre total de
    features correspond.
    """
    input_shape = model.input_shape
    if isinstance(input_shape, list):  # modèles multi-entrées : première entrée
        input_shape = input_shape[0]
    target = tuple(d for d in input_shape[1:])  # sans la dimension batch

    if any(d is None for d in target):
        # Dimension libre (ex. séquences variables) : on tente (n, F, 1)
        if len(target) == 2:
            return X.reshape((-1, X.shape[1], 1))
        return X

    n_expected = int(np.prod(target))
    if n_expected != X.shape[1]:
        raise ValueError(
            f"Le modèle attend {n_expected} features (shape {target}) "
            f"mais les données en ont {X.shape[1]}. Vérifiez le prétraitement "
            f"(colonnes supprimées, scaler)."
        )
    if len(target) == 1:
        return X
    return X.reshape((-1,) + target)
