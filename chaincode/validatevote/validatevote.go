// BAg-IDS — Chaincode validateVote (étape 1.4).
//
// Traduction Go, pour Hyperledger Fabric, de la logique de consensus
// validée et testée en étape 1.3 (agents/common/ledger.py). Le
// chaincode porte l'état "monde" (world state) sur le ledger répliqué
// de Fabric et applique les mêmes règles :
//
//   - RecordAlert : enregistre une alerte émise par un Sentinel.
//   - ValidateVote : n'accepte un vote QUE s'il est signé (Ed25519) par
//     un notary du registre des signataires autorisés ; un notary ne
//     vote qu'une fois par alerte (anti-rejeu) ; quand `quorum` votes
//     d'approbation valides sont réunis, l'alerte passe à CERTIFIED.
//   - GetAlert / IsCertified : lecture de l'état.
//
// Les identités sont ici des clés Ed25519 (mêmes clés que le ledger
// simulé) enregistrées via RegisterSigner ; sur un déploiement Fabric
// de production, elles seraient adossées aux certificats X.509 des MSP,
// mais on conserve Ed25519 pour rester iso avec les agents Python.

package main

import (
	"crypto/ed25519"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"sort"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// SmartContract fournit les fonctions de gestion des votes.
type SmartContract struct {
	contractapi.Contract
}

// Alert reflète le monde-état d'une alerte et de ses votes.
type Alert struct {
	AlertID        string          `json:"alert_id"`
	SentinelID     string          `json:"sentinel_id"`
	PredictedClass string          `json:"predicted_class"`
	Confidence     float64         `json:"confidence"`
	Severity       string          `json:"severity"`
	Votes          map[string]bool `json:"votes"` // voter_id -> approve
	Certified      bool            `json:"certified"`
	Payload        string          `json:"payload"` // JSON canonique original (audit)
}

const signerPrefix = "signer~"
const alertPrefix = "alert~"
const govPrefix = "gov~"

// GovernanceRecord : trace immuable d'une action de la couche
// Human-in-the-Loop (bascule HITL, changement de policy, décision
// manuelle). Signée par le signataire de gouvernance : l'administrateur
// est ainsi auditable au même titre que les notaries.
type GovernanceRecord struct {
	Seq       uint64 `json:"seq"`
	Action    string `json:"action"`
	Actor     string `json:"actor"`
	Payload   string `json:"payload"`   // JSON canonique signé
	Signature string `json:"signature"` // Ed25519 hex
	Signer    string `json:"signer"`    // agent_id du signataire
}

// --- Gestion du registre des signataires -----------------------------

// RegisterSigner enregistre la clé publique Ed25519 (hex) d'un notary
// autorisé. (Bootstrap ; en production, réservé à un admin MSP.)
func (s *SmartContract) RegisterSigner(ctx contractapi.TransactionContextInterface,
	agentID string, publicKeyHex string) error {
	if _, err := hex.DecodeString(publicKeyHex); err != nil {
		return fmt.Errorf("clé publique hex invalide : %v", err)
	}
	key := signerPrefix + agentID
	return ctx.GetStub().PutState(key, []byte(publicKeyHex))
}

func (s *SmartContract) getSignerKey(ctx contractapi.TransactionContextInterface,
	agentID string) (ed25519.PublicKey, error) {
	data, err := ctx.GetStub().GetState(signerPrefix + agentID)
	if err != nil {
		return nil, err
	}
	if data == nil {
		return nil, fmt.Errorf("signataire non autorisé : %s", agentID)
	}
	raw, err := hex.DecodeString(string(data))
	if err != nil {
		return nil, err
	}
	return ed25519.PublicKey(raw), nil
}

// --- Alertes ---------------------------------------------------------

// RecordAlert enregistre une nouvelle alerte (idempotent sur alert_id).
func (s *SmartContract) RecordAlert(ctx contractapi.TransactionContextInterface,
	alertID, sentinelID, predictedClass string, confidence float64,
	severity, payload string) error {
	existing, err := ctx.GetStub().GetState(alertPrefix + alertID)
	if err != nil {
		return err
	}
	if existing != nil {
		return nil // déjà enregistrée
	}
	alert := Alert{
		AlertID:        alertID,
		SentinelID:     sentinelID,
		PredictedClass: predictedClass,
		Confidence:     confidence,
		Severity:       severity,
		Votes:          map[string]bool{},
		Certified:      false,
		Payload:        payload,
	}
	return s.putAlert(ctx, &alert)
}

// ValidateVote vérifie et enregistre un vote signé, puis certifie
// l'alerte si le quorum d'approbations est atteint. Retourne l'alerte
// mise à jour. Reproduit exactement SimulatedLedger.validate_vote.
//
// signedPayload = JSON canonique EXACT signé par l'agent (les mêmes
// octets que ceux vérifiés). signatureHex = signature Ed25519 (hex).
func (s *SmartContract) ValidateVote(ctx contractapi.TransactionContextInterface,
	alertID, voterID string, approve bool, signedPayload, signatureHex string,
	quorum int) (*Alert, error) {

	// 1. Autorisation + authenticité (signature Ed25519)
	pubKey, err := s.getSignerKey(ctx, voterID)
	if err != nil {
		return nil, err
	}
	sig, err := hex.DecodeString(signatureHex)
	if err != nil {
		return nil, fmt.Errorf("signature hex invalide : %v", err)
	}
	if !ed25519.Verify(pubKey, []byte(signedPayload), sig) {
		return nil, fmt.Errorf("signature invalide pour %s", voterID)
	}

	// 2. Chargement de l'alerte
	alert, err := s.readAlert(ctx, alertID)
	if err != nil {
		return nil, err
	}

	// 3. Anti-rejeu : un seul vote par notary
	if _, voted := alert.Votes[voterID]; voted {
		return nil, fmt.Errorf("double vote de %s sur %s", voterID, alertID)
	}
	alert.Votes[voterID] = approve

	// 4. Quorum -> certification
	approvals := 0
	for _, ok := range alert.Votes {
		if ok {
			approvals++
		}
	}
	if approvals >= quorum {
		alert.Certified = true
	}
	if err := s.putAlert(ctx, alert); err != nil {
		return nil, err
	}
	return alert, nil
}

// GetAlert lit l'état d'une alerte.
func (s *SmartContract) GetAlert(ctx contractapi.TransactionContextInterface,
	alertID string) (*Alert, error) {
	return s.readAlert(ctx, alertID)
}

// IsCertified indique si une alerte a atteint le consensus.
func (s *SmartContract) IsCertified(ctx contractapi.TransactionContextInterface,
	alertID string) (bool, error) {
	alert, err := s.readAlert(ctx, alertID)
	if err != nil {
		return false, err
	}
	return alert.Certified, nil
}

// ListCertified renvoie les IDs des alertes certifiées (audit).
func (s *SmartContract) ListCertified(ctx contractapi.TransactionContextInterface) ([]string, error) {
	iter, err := ctx.GetStub().GetStateByRange(alertPrefix, alertPrefix+"￿")
	if err != nil {
		return nil, err
	}
	defer iter.Close()
	var ids []string
	for iter.HasNext() {
		kv, err := iter.Next()
		if err != nil {
			return nil, err
		}
		var a Alert
		if err := json.Unmarshal(kv.Value, &a); err != nil {
			continue
		}
		if a.Certified {
			ids = append(ids, a.AlertID)
		}
	}
	sort.Strings(ids)
	return ids, nil
}

// --- Gouvernance (couche Human-in-the-Loop) --------------------------

// RecordGovernance ancre une action de gouvernance signée. On distingue
// l'ACTEUR humain (métadonnée : le username de l'admin/analyste) du
// SIGNATAIRE cryptographique (l'identité de gouvernance enregistrée qui
// signe pour le compte de la couche HITL). La signature Ed25519 est
// vérifiée contre la clé enregistrée du `signer` : une intervention ne
// peut être forgée sans cette clé. Retourne le numéro de séquence.
func (s *SmartContract) RecordGovernance(ctx contractapi.TransactionContextInterface,
	action, actor, signer, signedPayload, signatureHex string) (uint64, error) {

	pubKey, err := s.getSignerKey(ctx, signer)
	if err != nil {
		return 0, fmt.Errorf("signataire de gouvernance non autorisé : %v", err)
	}
	sig, err := hex.DecodeString(signatureHex)
	if err != nil {
		return 0, fmt.Errorf("signature hex invalide : %v", err)
	}
	if !ed25519.Verify(pubKey, []byte(signedPayload), sig) {
		return 0, fmt.Errorf("signature de gouvernance invalide (signer %s)", signer)
	}

	seq, err := s.nextGovSeq(ctx)
	if err != nil {
		return 0, err
	}
	rec := GovernanceRecord{
		Seq: seq, Action: action, Actor: actor,
		Payload: signedPayload, Signature: signatureHex, Signer: signer,
	}
	data, err := json.Marshal(rec)
	if err != nil {
		return 0, err
	}
	key := fmt.Sprintf("%s%020d", govPrefix, seq)
	if err := ctx.GetStub().PutState(key, data); err != nil {
		return 0, err
	}
	return seq, nil
}

// ListGovernance renvoie l'ensemble des actions de gouvernance ancrées
// (ordre chronologique), pour l'audit de la couche HITL.
func (s *SmartContract) ListGovernance(ctx contractapi.TransactionContextInterface) ([]*GovernanceRecord, error) {
	iter, err := ctx.GetStub().GetStateByRange(govPrefix, govPrefix+"￿")
	if err != nil {
		return nil, err
	}
	defer iter.Close()
	var out []*GovernanceRecord
	for iter.HasNext() {
		kv, err := iter.Next()
		if err != nil {
			return nil, err
		}
		var rec GovernanceRecord
		if err := json.Unmarshal(kv.Value, &rec); err != nil {
			continue
		}
		out = append(out, &rec)
	}
	return out, nil
}

func (s *SmartContract) nextGovSeq(ctx contractapi.TransactionContextInterface) (uint64, error) {
	iter, err := ctx.GetStub().GetStateByRange(govPrefix, govPrefix+"￿")
	if err != nil {
		return 0, err
	}
	defer iter.Close()
	var n uint64
	for iter.HasNext() {
		if _, err := iter.Next(); err != nil {
			return 0, err
		}
		n++
	}
	return n, nil
}

// --- Helpers ---------------------------------------------------------

func (s *SmartContract) readAlert(ctx contractapi.TransactionContextInterface,
	alertID string) (*Alert, error) {
	data, err := ctx.GetStub().GetState(alertPrefix + alertID)
	if err != nil {
		return nil, err
	}
	if data == nil {
		return nil, fmt.Errorf("alerte inconnue : %s", alertID)
	}
	var alert Alert
	if err := json.Unmarshal(data, &alert); err != nil {
		return nil, err
	}
	if alert.Votes == nil {
		alert.Votes = map[string]bool{}
	}
	return &alert, nil
}

func (s *SmartContract) putAlert(ctx contractapi.TransactionContextInterface,
	alert *Alert) error {
	data, err := json.Marshal(alert)
	if err != nil {
		return err
	}
	return ctx.GetStub().PutState(alertPrefix+alert.AlertID, data)
}

func main() {
	chaincode, err := contractapi.NewChaincode(&SmartContract{})
	if err != nil {
		panic(fmt.Sprintf("création du chaincode validateVote : %v", err))
	}
	if err := chaincode.Start(); err != nil {
		panic(fmt.Sprintf("démarrage du chaincode validateVote : %v", err))
	}
}
