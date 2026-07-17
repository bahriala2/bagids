"""
BAg-IDS — Démonstration de bout en bout de l'étape 1.2.

Démarre Notary, Executor et Data Scientist en sous-processus, attend
leur disponibilité (/health), lance le Sentinel (qui rejoue le split
test), puis imprime un rapport : compteurs de chaque agent, dernières
entrées du ledger et vérification d'intégrité de la chaîne de hachages.

Usage (depuis la racine du dépôt) :
    python -m agents.launch_demo --config configs/agents.yaml
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import httpx
import yaml

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

def background_agents(cfg: dict) -> list[tuple[str, str, list[str], str]]:
    """(nom, module, args supplémentaires, url de santé) par agent de fond."""
    agents = []
    for inst in cfg["notary"]["instances"]:
        agents.append((
            inst["agent_id"], "agents.notary.agent",
            ["--instance", inst["agent_id"]],
            f"http://{inst['host']}:{inst['port']}",
        ))
    for name in ("executor", "data_scientist"):
        agents.append((
            name, f"agents.{name}.agent", [],
            f"http://{cfg[name]['host']}:{cfg[name]['port']}",
        ))
    if cfg.get("investigator"):
        ic = cfg["investigator"]
        agents.append((
            "investigator", "agents.investigator.agent", [],
            f"http://{ic['host']}:{ic['port']}",
        ))
    return agents


def wait_healthy(name: str, url: str, timeout_s: float = 60.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            if httpx.get(f"{url}/health", timeout=2.0).status_code == 200:
                print(f"  [ok] {name} prêt sur {url}")
                return True
        except httpx.HTTPError:
            pass
        time.sleep(1.0)
    print(f"  [!!] {name} injoignable sur {url}")
    return False


def main():
    parser = argparse.ArgumentParser(description="BAg-IDS demo étape 1.2")
    parser.add_argument("--config", default="configs/agents.yaml")
    args = parser.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    urls = {name: f"http://{cfg[name]['host']}:{cfg[name]['port']}"
            for name in ("sentinel", "executor", "data_scientist")}
    leader = cfg["notary"]["instances"][0]
    urls["notary_leader"] = f"http://{leader['host']}:{leader['port']}"

    agents = background_agents(cfg)
    procs: list[subprocess.Popen] = []
    try:
        print("=== Démarrage des agents de fond ===")
        for name, module, extra, _url in agents:
            procs.append(subprocess.Popen(
                [sys.executable, "-m", module, "--config", args.config]
                + extra))
        for name, _module, _extra, url in agents:
            if not wait_healthy(name, url):
                raise RuntimeError(f"{name} n'a pas démarré")

        print("\n=== Lancement du Sentinel (replay du split test) ===")
        sentinel = subprocess.run(
            [sys.executable, "-m", "agents.sentinel.agent",
             "--config", args.config])
        if sentinel.returncode != 0:
            raise RuntimeError("Sentinel terminé en erreur")

        print("\n=== Rapport final ===")
        with httpx.Client(timeout=5.0) as http:
            for name, _module, _extra, url in agents:
                h = http.get(f"{url}/health").json()
                print(f"  {name:<15} processed={h['processed']:<6} "
                      f"extra={h['extra']}")
            ledger = http.get(f"{urls['notary_leader']}/ledger",
                              params={"n": 4}).json()
            print(f"  ledger          chaîne_valide={ledger['chain_valid']} "
                  f"(4 dernières entrées : "
                  f"{[e['kind'] for e in ledger['entries']]})")
            recs = http.get(f"{urls['data_scientist']}/recommendations").json()
            if recs:
                print(f"  data_scientist  dernière recommandation : "
                      f"{recs[-1]['actions']} ({recs[-1]['provider']})")
    finally:
        print("\n=== Arrêt des agents de fond ===")
        for p in procs:
            p.terminate()
        for p in procs:
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()


if __name__ == "__main__":
    main()
