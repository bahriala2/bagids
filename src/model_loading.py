"""
BAg-IDS — Chargement compatible des modèles Keras legacy (.h5).

Certains modèles ont été sauvegardés avec d'anciennes versions de
TensorFlow/Keras et contiennent des arguments de configuration depuis
supprimés par Keras 3 (ex. `time_major` sur SimpleRNN/GRU/LSTM), ce qui
fait échouer `tf.keras.models.load_model`. On nettoie la config JSON
embarquée dans le .h5 puis on recharge les poids séparément.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile

import h5py
import tensorflow as tf

logger = logging.getLogger("bag_ids.model_loading")

# Arguments de configuration de couches Keras supprimés dans les
# versions récentes mais encore présents dans certains .h5 legacy.
_DEPRECATED_LAYER_KEYS = ("time_major",)


def _strip_deprecated_keys(obj):
    if isinstance(obj, dict):
        for key in _DEPRECATED_LAYER_KEYS:
            obj.pop(key, None)
        for value in obj.values():
            _strip_deprecated_keys(value)
    elif isinstance(obj, list):
        for value in obj:
            _strip_deprecated_keys(value)


def load_keras_model_compat(path: str):
    """Charge un modèle Keras .h5, avec repli compatible si la config
    contient des arguments de couches obsolètes.

    On patche l'attribut `model_config` (JSON) dans une copie temporaire
    du .h5 puis on recharge via le loader legacy standard : celui-ci sait
    reconstruire les vieux modèles Sequential (contrairement à
    `model_from_json`, qui n'accepte que le format de sérialisation
    Keras 3), et les poids restent inchangés dans le fichier.
    """
    try:
        return tf.keras.models.load_model(path, compile=False)
    except (ValueError, TypeError) as exc:
        if "Unrecognized keyword arguments" not in str(exc):
            raise
        logger.warning(
            "Config Keras legacy incompatible (%s) : nettoyage et rechargement de %s",
            exc, path,
        )
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".h5")
        os.close(tmp_fd)
        try:
            shutil.copyfile(path, tmp_path)
            with h5py.File(tmp_path, "r+") as f:
                raw_config = f.attrs["model_config"]
                if isinstance(raw_config, bytes):
                    raw_config = raw_config.decode("utf-8")
                config = json.loads(raw_config)
                _strip_deprecated_keys(config)
                f.attrs["model_config"] = json.dumps(config)
            return tf.keras.models.load_model(tmp_path, compile=False)
        finally:
            os.remove(tmp_path)
