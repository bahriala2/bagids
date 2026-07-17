"""
BAg-IDS — Sources de flux pour le Sentinel.

V1 : ReplayFlowSource rejoue le split test du bundle de déploiement à
cadence contrôlée — parfait pour développer/mesurer les agents sans
capture réseau. L'interface (générateur async de FlowFeatures) est la
même que celle qu'implémentera la future source CICFlowMeter live, de
sorte que l'agent ne change pas d'une source à l'autre.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import numpy as np

from agents.common.schemas import FlowFeatures

logger = logging.getLogger("bag_ids.agents.sentinel.source")


class ReplayFlowSource:
    """Rejoue X_test.npy/y_test.npy du bundle (déjà normalisés)."""

    def __init__(self, bundle_dir: str | Path, class_names: list[str],
                 flows_per_second: float = 200.0, max_flows: int = 0,
                 batch_size: int = 32, loop: bool = False):
        bundle_dir = Path(bundle_dir)
        self.X = np.load(bundle_dir / "X_test.npy")
        y = np.load(bundle_dir / "y_test.npy")
        self.labels = [class_names[int(i)] for i in y]
        self.flows_per_second = flows_per_second
        self.max_flows = max_flows if max_flows > 0 else len(self.X)
        self.batch_size = batch_size
        self.loop = loop   # rejeu continu (mode surveillance live)
        logger.info("Replay : %d flux disponibles, cadence %.0f flux/s, "
                    "limite %d flux, boucle=%s", len(self.X), flows_per_second,
                    self.max_flows, loop)

    async def stream(self):
        """Générateur async de micro-batches de FlowFeatures.

        En mode `loop`, le jeu est rejoué indéfiniment (surveillance
        continue pour le tableau de bord temps réel)."""
        n = min(self.max_flows, len(self.X))
        delay = (self.batch_size / self.flows_per_second
                 if self.flows_per_second > 0 else 0.0)
        while True:
            for start in range(0, n, self.batch_size):
                end = min(start + self.batch_size, n)
                batch = [
                    FlowFeatures(
                        features=self.X[i].tolist(),
                        true_label=self.labels[i],
                    )
                    for i in range(start, end)
                ]
                yield batch
                if delay:
                    await asyncio.sleep(delay)
            if not self.loop:
                break
