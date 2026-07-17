"""
BAg-IDS — Identités cryptographiques des agents (étape 1.3).

Chaque agent possède une paire de clés Ed25519. Les votes sont signés
par l'agent émetteur et vérifiés PAR LE LEDGER contre le registre des
signataires autorisés — exactement la logique que portera le chaincode
`validateVote` sur Hyperledger Fabric (où les identités deviendront des
certificats X.509 délivrés par la CA de l'organisation).

Arborescence des clés (non versionnée) :
    keys/<agent_id>.key            clé privée Ed25519 (PEM)
    keys/authorized_signers.json   registre {agent_id: clé publique hex}

Génération :
    python -m agents.common.identity --config configs/agents.yaml
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

logger = logging.getLogger("bag_ids.agents.identity")


def canonical_bytes(payload: dict) -> bytes:
    """Sérialisation canonique (mêmes octets signés côté agent et
    vérifiés côté ledger/chaincode)."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


class AgentIdentity:
    """Clé privée d'un agent : signe les payloads qu'il émet."""

    def __init__(self, agent_id: str, private_key: Ed25519PrivateKey):
        self.agent_id = agent_id
        self._private_key = private_key

    @classmethod
    def load(cls, keys_dir: str | Path, agent_id: str) -> "AgentIdentity":
        pem = (Path(keys_dir) / f"{agent_id}.key").read_bytes()
        key = serialization.load_pem_private_key(pem, password=None)
        return cls(agent_id, key)

    def sign(self, payload: dict) -> str:
        """Signature hex du payload canonique."""
        return self._private_key.sign(canonical_bytes(payload)).hex()

    def public_key_hex(self) -> str:
        return self._private_key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        ).hex()


class SignerRegistry:
    """Registre des signataires autorisés : la partie *vérification* de
    la logique validateVote. Chargé par le ledger simulé (et, à l'étape
    1.4, embarqué dans l'état du chaincode)."""

    def __init__(self, registry: dict[str, str]):
        self._keys = {
            agent_id: Ed25519PublicKey.from_public_bytes(bytes.fromhex(hexkey))
            for agent_id, hexkey in registry.items()
        }

    @classmethod
    def load(cls, keys_dir: str | Path) -> "SignerRegistry":
        path = Path(keys_dir) / "authorized_signers.json"
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def is_authorized(self, agent_id: str) -> bool:
        return agent_id in self._keys

    def verify(self, agent_id: str, payload: dict, signature_hex: str) -> bool:
        """True si `signature_hex` est une signature valide de `payload`
        par la clé enregistrée de `agent_id`."""
        key = self._keys.get(agent_id)
        if key is None:
            return False
        try:
            key.verify(bytes.fromhex(signature_hex), canonical_bytes(payload))
            return True
        except (InvalidSignature, ValueError):
            return False


def generate_keys(cfg: dict, keys_dir: str | Path):
    """Génère (ou complète) les clés de tous les agents du déploiement."""
    keys_dir = Path(keys_dir)
    keys_dir.mkdir(parents=True, exist_ok=True)
    registry_path = keys_dir / "authorized_signers.json"
    registry = (json.loads(registry_path.read_text(encoding="utf-8"))
                if registry_path.exists() else {})

    agent_ids = [cfg["sentinel"]["agent_id"],
                 cfg["executor"]["agent_id"],
                 cfg["data_scientist"]["agent_id"]]
    agent_ids += [inst["agent_id"] for inst in cfg["notary"]["instances"]]

    for agent_id in agent_ids:
        key_path = keys_dir / f"{agent_id}.key"
        if key_path.exists():
            identity = AgentIdentity.load(keys_dir, agent_id)
            logger.info("Clé existante conservée : %s", agent_id)
        else:
            private = Ed25519PrivateKey.generate()
            key_path.write_bytes(private.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            ))
            identity = AgentIdentity(agent_id, private)
            logger.info("Clé générée : %s", agent_id)
        registry[agent_id] = identity.public_key_hex()

    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    logger.info("Registre des signataires : %s (%d agents)",
                registry_path, len(registry))


def main():
    import yaml
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)-7s | %(message)s")
    parser = argparse.ArgumentParser(description="Génération des identités")
    parser.add_argument("--config", default="configs/agents.yaml")
    parser.add_argument("--keys-dir", default="keys")
    args = parser.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    generate_keys(cfg, args.keys_dir)


if __name__ == "__main__":
    main()
