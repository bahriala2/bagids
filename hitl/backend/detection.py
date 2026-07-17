"""
BAg-IDS HITL — Contrôle du pipeline de détection.

Démarre / arrête le pipeline d'agents (Sentinel continu + Notary + Executor
+ Data Scientist) comme sous-processus piloté depuis la console, et
injecte des flux de test (« mes attaques ») vers le Sentinel.
"""

from __future__ import annotations

import subprocess
import sys
import threading
import time
from pathlib import Path

import httpx

from hitl.backend.config import CONFIG

# Répertoire racine du projet (contient agents/, configs/, .venv...)
_ROOT = Path(__file__).resolve().parents[2]


class DetectionController:
    def __init__(self):
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._started_at: float | None = None
        self._config = CONFIG.get("detection_config", "configs/agents_live.yaml")
        self._sentinel = CONFIG["agents"]["sentinel"]

    # --------------------------------------------------------- cycle de vie
    def running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def start(self) -> dict:
        with self._lock:
            if self.running():
                return {"running": True, "already": True}
            # Lance le pipeline persistant ; nouveau groupe de processus pour
            # pouvoir tuer tout l'arbre à l'arrêt (Windows: CREATE_NEW_...).
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            self._proc = subprocess.Popen(
                [sys.executable, "-m", "agents.run_pipeline",
                 "--config", self._config],
                cwd=str(_ROOT), creationflags=creationflags)
            self._started_at = time.time()
            return {"running": True, "started": True, "pid": self._proc.pid}

    def stop(self) -> dict:
        with self._lock:
            if not self.running():
                self._proc = None
                return {"running": False, "already_stopped": True}
            pid = self._proc.pid
            if sys.platform == "win32":
                # Tue l'arbre de processus (le pipeline + tous les agents)
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                               capture_output=True)
            else:
                self._proc.terminate()
            try:
                self._proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._proc.kill()
            self._proc = None
            self._started_at = None
            return {"running": False, "stopped": True}

    def status(self) -> dict:
        running = self.running()
        sentinel_online, processed = False, 0
        if running:
            try:
                r = httpx.get(f"{self._sentinel}/health", timeout=2.0)
                if r.status_code == 200:
                    h = r.json()
                    sentinel_online = True
                    processed = h.get("processed", 0)
            except httpx.HTTPError:
                pass
        return {
            "running": running,
            "sentinel_online": sentinel_online,
            "flows_processed": processed,
            "uptime_s": round(time.time() - self._started_at, 1)
            if self._started_at else 0,
        }

    # ------------------------------------------------------ injection test
    def inject(self, flows: list[list[float]],
               labels: list[str] | None = None) -> dict:
        """Envoie des flux (vecteurs de features normalisés) au Sentinel."""
        if not self.running():
            return {"error": "pipeline arrêté : démarrez la détection d'abord"}
        try:
            r = httpx.post(f"{self._sentinel}/detect",
                           json={"flows": flows, "labels": labels},
                           timeout=30.0)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPError as exc:
            return {"error": f"Sentinel injoignable : {exc}"}

    def sentinel_meta(self) -> dict | None:
        try:
            r = httpx.get(f"{self._sentinel}/meta", timeout=2.0)
            return r.json() if r.status_code == 200 else None
        except httpx.HTTPError:
            return None


CONTROLLER = DetectionController()
