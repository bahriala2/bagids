"""
BAg-IDS HITL — Configuration du backend.

Valeurs par défaut surchargées par les variables d'environnement
(préfixe BAGIDS_HITL_) ou par configs/hitl.yaml s'il existe.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

_DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8090,
    # Secret JWT — À REMPLACER en production (variable d'env recommandée)
    "jwt_secret": "bag-ids-hitl-dev-secret-change-me",
    "jwt_algorithm": "HS256",
    "access_token_minutes": 720,
    # URLs des agents (mêmes valeurs que configs/agents.yaml)
    "agents": {
        "sentinel": "http://127.0.0.1:8001",
        "notary_leader": "http://127.0.0.1:8002",
        "executor": "http://127.0.0.1:8003",
        "data_scientist": "http://127.0.0.1:8004",
        "investigator": "http://127.0.0.1:8005",
    },
    # Passerelle Fabric (pour la gouvernance on-chain) ; null => ledger local
    "fabric_proxy_url": "http://127.0.0.1:8445",
    # Miroir local du ledger (lecture d'audit si Fabric indisponible)
    "ledger_mirror": "results/agents/ledger_fabric_mirror.jsonl",
    "keys_dir": "keys",
    # Clé d'identité utilisée par la couche HITL pour signer les
    # transactions de gouvernance (doit être un signataire autorisé).
    "governance_signer": "notary-01",
    # État HITL au démarrage : True = approbation humaine requise.
    "hitl_enabled_default": True,
    # Sévérités qui exigent une approbation humaine quand HITL est actif.
    "approval_required_severities": ["high", "critical"],
    # Utilisateurs (démo). Mots de passe hachés au premier lancement.
    "users": [
        {"username": "admin", "password": "admin123", "role": "admin",
         "full_name": "Administrateur SOC"},
        {"username": "analyste", "password": "analyste123", "role": "analyst",
         "full_name": "Analyste SOC"},
        {"username": "lecteur", "password": "lecteur123", "role": "reader",
         "full_name": "Observateur"},
    ],
    # Policy initiale (reflète configs/agents.yaml ; modifiable via gouvernance)
    "policy": {
        "tau": 0.70,
        "quorum": 2,
        "llm_provider_order": ["openrouter", "lmstudio"],
        "executor_dry_run": True,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config() -> dict:
    cfg = dict(_DEFAULTS)
    path = Path("configs/hitl.yaml")
    if path.exists():
        cfg = _deep_merge(cfg, yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    # Surcharges d'environnement simples
    if os.environ.get("BAGIDS_HITL_JWT_SECRET"):
        cfg["jwt_secret"] = os.environ["BAGIDS_HITL_JWT_SECRET"]
    if os.environ.get("BAGIDS_HITL_PORT"):
        cfg["port"] = int(os.environ["BAGIDS_HITL_PORT"])
    return cfg


CONFIG = load_config()
