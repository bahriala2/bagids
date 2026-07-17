"""
BAg-IDS — Tests de l'étape 1.3 : ledger simulé + logique validateVote.

Vérifie les 5 propriétés attendues du futur chaincode :
  1. immuabilité   : falsifier une entrée casse la chaîne de hachages ;
  2. authenticité  : un vote mal signé est refusé ;
  3. autorisation  : un signataire hors registre est refusé ;
  4. anti-rejeu    : un agent ne vote qu'une fois par alerte ;
  5. consensus     : quorum atteint => ALERT_CERTIFIED ; sinon rien.

Usage :
    python -m agents.test_step13
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from agents.common.identity import AgentIdentity, SignerRegistry
from agents.common.ledger import SimulatedLedger, VoteValidationError

PASS, FAIL = "[PASS]", "[FAIL]"
failures = 0


def check(name: str, condition: bool):
    global failures
    print(f"  {PASS if condition else FAIL} {name}")
    if not condition:
        failures = 1


def make_identity(agent_id: str) -> AgentIdentity:
    return AgentIdentity(agent_id, Ed25519PrivateKey.generate())


def vote_payload(alert_id: str, voter: str, approve: bool = True) -> dict:
    return {"vote_id": f"v-{voter}-{alert_id}", "timestamp": 0.0,
            "alert_id": alert_id, "voter_id": voter, "approve": approve,
            "reason": "ok"}


def main():
    tmp = Path(tempfile.mkdtemp())

    n1, n2, n3 = (make_identity(f"notary-0{i}") for i in (1, 2, 3))
    intrus = make_identity("intrus-99")
    registry = SignerRegistry({
        i.agent_id: i.public_key_hex() for i in (n1, n2, n3)
    })

    print("1. Immuabilité (chaîne de hachages)")
    ledger = SimulatedLedger(tmp / "l1.jsonl", registry, quorum=2)
    ledger.submit("ALERT", {"alert_id": "a1", "data": "x"})
    ledger.submit("ALERT", {"alert_id": "a2", "data": "y"})
    check("chaîne valide après écritures", ledger.verify_chain())
    lines = (tmp / "l1.jsonl").read_text(encoding="utf-8").splitlines()
    entry = json.loads(lines[0])
    entry["payload"]["data"] = "FALSIFIÉ"
    lines[0] = json.dumps(entry, sort_keys=True, separators=(",", ":"))
    (tmp / "l1.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    check("falsification détectée", not ledger.verify_chain())

    print("2. Authenticité (signature)")
    ledger = SimulatedLedger(tmp / "l2.jsonl", registry, quorum=2)
    p = vote_payload("a1", n1.agent_id)
    ok = ledger.validate_vote(p, n1.sign(p))
    check("vote correctement signé accepté", ok["accepted"])
    p2 = vote_payload("a1", n2.agent_id)
    bad_sig = n3.sign(p2)  # signé par la mauvaise clé
    try:
        ledger.validate_vote(p2, bad_sig)
        check("vote mal signé refusé", False)
    except VoteValidationError:
        check("vote mal signé refusé", True)

    print("3. Autorisation (registre)")
    p3 = vote_payload("a1", intrus.agent_id)
    try:
        ledger.validate_vote(p3, intrus.sign(p3))
        check("signataire hors registre refusé", False)
    except VoteValidationError:
        check("signataire hors registre refusé", True)

    print("4. Anti-rejeu (double vote)")
    p4 = vote_payload("a1", n1.agent_id)
    try:
        ledger.validate_vote(p4, n1.sign(p4))
        check("double vote refusé", False)
    except VoteValidationError:
        check("double vote refusé", True)

    print("5. Consensus (quorum = 2)")
    check("pas certifiée avec 1 seul vote", not ledger.is_certified("a1"))
    p5 = vote_payload("a1", n2.agent_id)
    result = ledger.validate_vote(p5, n2.sign(p5))
    check("certifiée au 2e vote d'approbation", result["certified"]
          and ledger.is_certified("a1"))
    # Contre-cas : votes négatifs -> jamais certifiée
    for ident in (n1, n2, n3):
        pn = vote_payload("a9", ident.agent_id, approve=False)
        ledger.validate_vote(pn, ident.sign(pn))
    check("3 votes négatifs ne certifient pas", not ledger.is_certified("a9"))
    kinds = [e["kind"] for e in ledger.last_n(50)]
    check("entrée ALERT_CERTIFIED présente au ledger",
          "ALERT_CERTIFIED" in kinds)
    check("chaîne toujours valide en fin de tests", ledger.verify_chain())

    print()
    if failures:
        print("ÉCHEC : au moins un test a échoué.")
        sys.exit(1)
    print("SUCCÈS : les 5 propriétés du chaincode simulé sont vérifiées.")


if __name__ == "__main__":
    main()
