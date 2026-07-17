// BAg-IDS — Passerelle HTTP vers le chaincode validateVote (étape 1.4).
//
// Petit service qui encapsule le SDK officiel fabric-gateway (Go) et
// expose deux endpoints HTTP locaux consommés par le client Python
// FabricLedger (agents/common/fabric_ledger.py) :
//
//	POST /submit    {"function": "...", "args": ["...", ...]}  -> transaction
//	POST /evaluate  {"function": "...", "args": ["...", ...]}  -> lecture seule
//
// Il se connecte en tant qu'Admin@org1 au peer0.org1 du test-network.
// Lancement (depuis WSL) :
//
//	go run . -listen 127.0.0.1:8445
package main

import (
	"crypto/x509"
	"encoding/json"
	"flag"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/hyperledger/fabric-gateway/pkg/client"
	"github.com/hyperledger/fabric-gateway/pkg/identity"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
)

const (
	mspID       = "Org1MSP"
	channelName = "mychannel"
	ccName      = "validatevote"
	peerEndpoint = "dns:///localhost:7051"
	gatewayPeer  = "peer0.org1.example.com"
)

var cryptoPath = filepath.Join(os.Getenv("HOME"),
	"fabric-samples/test-network/organizations/peerOrganizations/org1.example.com")

type rpcRequest struct {
	Function string   `json:"function"`
	Args     []string `json:"args"`
}

type rpcResponse struct {
	Result string `json:"result,omitempty"`
	Error  string `json:"error,omitempty"`
}

func firstFile(dir string) string {
	entries, err := os.ReadDir(dir)
	if err != nil || len(entries) == 0 {
		log.Fatalf("répertoire vide ou illisible : %s (%v)", dir, err)
	}
	return filepath.Join(dir, entries[0].Name())
}

func newGRPCConnection() *grpc.ClientConn {
	tlsCertPath := filepath.Join(cryptoPath,
		"peers/peer0.org1.example.com/tls/ca.crt")
	pem, err := os.ReadFile(tlsCertPath)
	if err != nil {
		log.Fatalf("lecture cert TLS : %v", err)
	}
	pool := x509.NewCertPool()
	pool.AppendCertsFromPEM(pem)
	creds := credentials.NewClientTLSFromCert(pool, gatewayPeer)
	conn, err := grpc.NewClient(peerEndpoint, grpc.WithTransportCredentials(creds))
	if err != nil {
		log.Fatalf("connexion gRPC : %v", err)
	}
	return conn
}

func newIdentity() *identity.X509Identity {
	certPath := firstFile(filepath.Join(cryptoPath,
		"users/Admin@org1.example.com/msp/signcerts"))
	pem, err := os.ReadFile(certPath)
	if err != nil {
		log.Fatalf("lecture certificat : %v", err)
	}
	cert, err := identity.CertificateFromPEM(pem)
	if err != nil {
		log.Fatalf("parsing certificat : %v", err)
	}
	id, err := identity.NewX509Identity(mspID, cert)
	if err != nil {
		log.Fatalf("identité : %v", err)
	}
	return id
}

func newSigner() identity.Sign {
	keyPath := firstFile(filepath.Join(cryptoPath,
		"users/Admin@org1.example.com/msp/keystore"))
	pem, err := os.ReadFile(keyPath)
	if err != nil {
		log.Fatalf("lecture clé privée : %v", err)
	}
	key, err := identity.PrivateKeyFromPEM(pem)
	if err != nil {
		log.Fatalf("parsing clé privée : %v", err)
	}
	sign, err := identity.NewPrivateKeySign(key)
	if err != nil {
		log.Fatalf("signer : %v", err)
	}
	return sign
}

func main() {
	listen := flag.String("listen", "127.0.0.1:8445", "adresse d'écoute HTTP")
	flag.Parse()

	conn := newGRPCConnection()
	defer conn.Close()

	gw, err := client.Connect(
		newIdentity(),
		client.WithSign(newSigner()),
		client.WithClientConnection(conn),
		client.WithEvaluateTimeout(15*time.Second),
		client.WithEndorseTimeout(30*time.Second),
		client.WithSubmitTimeout(15*time.Second),
		client.WithCommitStatusTimeout(2*time.Minute),
	)
	if err != nil {
		log.Fatalf("connexion gateway : %v", err)
	}
	defer gw.Close()

	contract := gw.GetNetwork(channelName).GetContract(ccName)

	handler := func(submit bool) http.HandlerFunc {
		return func(w http.ResponseWriter, r *http.Request) {
			var req rpcRequest
			if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
				writeJSON(w, http.StatusBadRequest,
					rpcResponse{Error: err.Error()})
				return
			}
			var result []byte
			var err error
			if submit {
				result, err = contract.SubmitTransaction(req.Function, req.Args...)
			} else {
				result, err = contract.EvaluateTransaction(req.Function, req.Args...)
			}
			if err != nil {
				writeJSON(w, http.StatusInternalServerError,
					rpcResponse{Error: err.Error()})
				return
			}
			writeJSON(w, http.StatusOK, rpcResponse{Result: string(result)})
		}
	}

	http.HandleFunc("/submit", handler(true))
	http.HandleFunc("/evaluate", handler(false))
	http.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{
			"status": "ok", "channel": channelName, "chaincode": ccName})
	})

	log.Printf("Passerelle Fabric en écoute sur %s (canal=%s, cc=%s)",
		*listen, channelName, ccName)
	log.Fatal(http.ListenAndServe(*listen, nil))
}

func writeJSON(w http.ResponseWriter, status int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}
