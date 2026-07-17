"""
BAg-IDS — Phase 2.1 : benchmark de latence de bout en bout ±blockchain.

Mesure, alerte par alerte, le coût de chaque étage du pipeline BAg-IDS
et compare deux configurations de la couche de consensus :

  - "simulated" : ledger local à chaîne de hachages (étape 1.3) ;
  - "fabric"    : chaincode validateVote sur Hyperledger Fabric via la
                  passerelle (étape 1.4).

L'écart entre les deux isole le COÛT DE LA BLOCKCHAIN (endorsement des
deux organisations + ordering + commit), qui est l'argument central de
la section « coût vs confiance » du manuscrit.

Étapes chronométrées par alerte certifiée :
  - inference_ms      : ensemble calibré (réflexe) sur le flux ;
  - consensus_ms      : RecordAlert + N votes ValidateVote (simulated
                        ou on-chain) jusqu'à certification ;
  - (la délibération LLM est mesurée à part : très variable, réseau).

Usage (réseau Fabric + passerelle actifs pour le mode fabric) :
    python -m experiments.phase2.bench_latency --config configs/agents.yaml \
        --n-alerts 60 --quorum 2 --out results/phase2/latency.json
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
import time
from pathlib import Path

import numpy as np
import yaml

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from agents.common.identity import AgentIdentity, SignerRegistry
from agents.common.ledger import SimulatedLedger
from agents.common.schemas import Verdict
from agents.sentinel.detector import EnsembleDetector
from agents.sentinel.flow_source import ReplayFlowSource


def percentile(values, p):
    if not values:
        return float("nan")
    return float(np.percentile(values, p))


def summarize(values):
    return {
        "n": len(values),
        "mean_ms": round(st.mean(values), 3) if values else float("nan"),
        "median_ms": round(st.median(values), 3) if values else float("nan"),
        "p95_ms": round(percentile(values, 95), 3),
        "p99_ms": round(percentile(values, 99), 3),
        "min_ms": round(min(values), 3) if values else float("nan"),
        "max_ms": round(max(values), 3) if values else float("nan"),
    }


def build_ledger(backend, cfg, registry, quorum, run_tag):
    ncfg = cfg["notary"]
    if backend == "fabric":
        from agents.common.fabric_ledger import FabricLedger
        led = FabricLedger(
            proxy_url=ncfg["fabric_proxy_url"],
            local_mirror_path=f"results/phase2/mirror_{run_tag}.jsonl",
            signer_registry=registry, quorum=quorum)
        signers = json.loads(
            (Path(ncfg["keys_dir"]) / "authorized_signers.json")
            .read_text(encoding="utf-8"))
        for inst in ncfg["instances"]:
            led.register_signer(inst["agent_id"], signers[inst["agent_id"]])
        return led
    return SimulatedLedger(f"results/phase2/mirror_{run_tag}.jsonl",
                           signer_registry=registry, quorum=quorum)


def run_backend(backend, cfg, detector, source_flows, identities, quorum,
                n_alerts):
    """Rejoue des flux jusqu'à obtenir n_alerts attaques certifiées,
    en chronométrant inférence et consensus."""
    registry = SignerRegistry.load(cfg["notary"]["keys_dir"])
    voters = [i["agent_id"] for i in cfg["notary"]["instances"]][:quorum]
    run_tag = f"{backend}_q{quorum}"
    # Repart d'un miroir vierge
    mirror = Path(f"results/phase2/mirror_{run_tag}.jsonl")
    if mirror.exists():
        mirror.unlink()
    ledger = build_ledger(backend, cfg, registry, quorum, run_tag)

    inf_ms, cons_ms, total_ms = [], [], []
    certified = 0
    for batch in source_flows:
        if certified >= n_alerts:
            break
        t0 = time.perf_counter()
        detections = detector.detect_batch(batch)
        batch_inf_ms = 1000 * (time.perf_counter() - t0) / len(batch)
        for det in detections:
            if certified >= n_alerts:
                break
            if det.verdict is not Verdict.ATTACK:
                continue
            # --- consensus : RecordAlert + votes signés jusqu'au quorum
            alert_id = det.detection_id
            tc = time.perf_counter()
            ledger.submit("ALERT", {
                "alert_id": alert_id, "sentinel_id": "sentinel-01",
                "severity": "high",
                "detection": {"predicted_class": det.predicted_class,
                              "confidence": det.confidence}})
            for voter in voters:
                payload = {"alert_id": alert_id, "voter_id": voter,
                           "approve": True}
                sig = identities[voter].sign(payload)
                ledger.validate_vote(payload, sig)
            consensus = 1000 * (time.perf_counter() - tc)
            if not ledger.is_certified(alert_id):
                continue
            inf_ms.append(batch_inf_ms)
            cons_ms.append(consensus)
            total_ms.append(batch_inf_ms + consensus)
            certified += 1
    return {
        "backend": backend,
        "quorum": quorum,
        "n_certified": certified,
        "inference": summarize(inf_ms),
        "consensus": summarize(cons_ms),
        "end_to_end": summarize(total_ms),
        "_raw": {"inference_ms": inf_ms, "consensus_ms": cons_ms},
    }


def main():
    parser = argparse.ArgumentParser(description="BAg-IDS phase 2.1 latence")
    parser.add_argument("--config", default="configs/agents.yaml")
    parser.add_argument("--n-alerts", type=int, default=60)
    parser.add_argument("--quorum", type=int, default=2)
    parser.add_argument("--backends", default="simulated,fabric")
    parser.add_argument("--out", default="results/phase2/latency.json")
    args = parser.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    Path("results/phase2").mkdir(parents=True, exist_ok=True)

    print("Chargement du détecteur d'ensemble...")
    detector = EnsembleDetector(cfg["sentinel"]["bundle_dir"])
    identities = {i["agent_id"]: AgentIdentity.load(cfg["notary"]["keys_dir"],
                                                    i["agent_id"])
                  for i in cfg["notary"]["instances"]}

    results = {"config": {"n_alerts": args.n_alerts, "quorum": args.quorum},
               "runs": []}
    for backend in args.backends.split(","):
        backend = backend.strip()
        print(f"\n=== Backend : {backend} (quorum={args.quorum}) ===")
        # Source neuve à chaque backend (mêmes flux, ordre déterministe)
        source = ReplayFlowSource(
            bundle_dir=cfg["sentinel"]["bundle_dir"],
            class_names=detector.class_names,
            flows_per_second=0,  # aussi vite que possible pour le bench
            max_flows=0, batch_size=64)
        # Générateur synchrone à partir du flux async
        flows = _sync_batches(source)
        run = run_backend(backend, cfg, detector, flows, identities,
                          args.quorum, args.n_alerts)
        results["runs"].append({k: v for k, v in run.items()
                                if k != "_raw"})
        e = run["end_to_end"]
        c = run["consensus"]
        print(f"  {run['n_certified']} alertes certifiées")
        print(f"  consensus  : moy {c['mean_ms']:.1f} ms | "
              f"méd {c['median_ms']:.1f} | p95 {c['p95_ms']:.1f}")
        print(f"  bout-en-bout: moy {e['mean_ms']:.1f} ms | "
              f"méd {e['median_ms']:.1f} | p95 {e['p95_ms']:.1f}")

    # Coût de la blockchain = écart des médianes de consensus
    runs = {r["backend"]: r for r in results["runs"]}
    if "simulated" in runs and "fabric" in runs:
        overhead = (runs["fabric"]["consensus"]["median_ms"]
                    - runs["simulated"]["consensus"]["median_ms"])
        results["blockchain_overhead_median_ms"] = round(overhead, 3)
        print(f"\n>>> Surcoût médian de la blockchain (consensus) : "
              f"{overhead:.1f} ms/alerte")

    Path(args.out).write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nRésultats : {args.out}")


def _sync_batches(source):
    """Adapte le générateur async de ReplayFlowSource en itérable
    synchrone (le bench n'a pas besoin de la cadence temporelle)."""
    import asyncio
    loop = asyncio.new_event_loop()
    agen = source.stream()
    try:
        while True:
            try:
                yield loop.run_until_complete(agen.__anext__())
            except StopAsyncIteration:
                break
    finally:
        loop.close()


if __name__ == "__main__":
    main()
