"""
BAg-IDS — Lanceur de pipeline PERSISTANT (mode surveillance live).

Contrairement à launch_demo (qui rejoue un batch puis s'arrête), ce
lanceur démarre tous les agents et les maintient en vie jusqu'à ce qu'on
tue le processus. Le Sentinel tourne en mode boucle (rejeu continu du
jeu de test) pour alimenter le tableau de bord en flux temps réel et
accepter des injections d'attaques via son endpoint /detect.

Utilisé par la console HITL (bouton « Démarrer la détection »), qui le
lance comme sous-processus et l'arrête en tuant l'arbre de processus.

    python -m agents.run_pipeline --config configs/agents.yaml
"""

from __future__ import annotations

import argparse
import signal
import subprocess
import sys
import time
from pathlib import Path

import httpx
import yaml

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

BACKGROUND = [
    ("executor", "agents.executor.agent", []),
    ("data_scientist", "agents.data_scientist.agent", []),
    ("investigator", "agents.investigator.agent", []),
]


def _wait_health(url: str, timeout_s: float = 45.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            if httpx.get(f"{url}/health", timeout=2.0).status_code == 200:
                return True
        except httpx.HTTPError:
            pass
        time.sleep(1.0)
    return False


def main():
    parser = argparse.ArgumentParser(description="BAg-IDS pipeline persistant")
    parser.add_argument("--config", default="configs/agents.yaml")
    args = parser.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    procs: list[subprocess.Popen] = []

    def spawn(module: str, extra: list[str]):
        p = subprocess.Popen([sys.executable, "-m", module,
                              "--config", args.config] + extra)
        procs.append(p)
        return p

    print("[pipeline] Démarrage des notaries...", flush=True)
    for inst in cfg["notary"]["instances"]:
        spawn("agents.notary.agent", ["--instance", inst["agent_id"]])
    for _name, module, extra in BACKGROUND:
        spawn(module, extra)

    # Attente de disponibilité des agents de fond
    leader = cfg["notary"]["instances"][0]
    for url in [f"http://{leader['host']}:{leader['port']}",
                f"http://{cfg['executor']['host']}:{cfg['executor']['port']}",
                f"http://{cfg['data_scientist']['host']}:"
                f"{cfg['data_scientist']['port']}"]:
        _wait_health(url)
    print("[pipeline] Agents de fond prêts. Démarrage du Sentinel (continu)...",
          flush=True)

    # Sentinel en dernier, en avant-plan (garde le pipeline vivant)
    sentinel = spawn("agents.sentinel.agent", [])

    def shutdown(*_):
        print("[pipeline] Arrêt : terminaison des agents...", flush=True)
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        for p in procs:
            try:
                p.wait(timeout=8)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    try:
        sentinel.wait()
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()


if __name__ == "__main__":
    main()
