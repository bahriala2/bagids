# Réponse aux remarques — BAg-IDS, révision v9 (16/07/2026)

Merci beaucoup pour votre lecture et vos recommandations. Toutes ont été prises en compte dans la version révisée ci-jointe. Voici, point par point, ce qui a été modifié.

## 1. Mise en avant de la contribution principale

Le papier est désormais recentré sur le message unique : « un IDS de confiance construit sur une architecture agentique sécurisée par un consensus blockchain ».

- L'abstract a été réécrit : il énonce cette contribution centrale dès la deuxième phrase, puis présente explicitement les autres éléments (fusion calibrée, rejet sélectif, délibération LLM, supervision humaine) comme des mécanismes au service de ce but.
- L'introduction contient maintenant une phrase-thèse explicite (« Its central claim is deliberately singular... ») juste avant la description des quatre couches, avec la même hiérarchie : un objectif, des mécanismes.

## 2. Positionnement du Conscious Weighted Consensus

Le CWC est désormais présenté comme une stratégie de fusion pondérée intégrée dans l'architecture de confiance, et non comme un nouvel algorithme :

- **Le titre a été changé** : « ...with Conscious Weighted Consensus » a été retiré. Nouveau titre : *BAg-IDS: A Blockchain-Enabled Agentic AI Architecture for Trustworthy Intrusion Detection*.
- La contribution n°2 de l'introduction est reformulée : « A reliability-weighted fusion strategy integrated in the trust architecture », avec la mention explicite qu'elle est assemblée à partir de composants établis et que sa contribution est son rôle architectural.
- La section 4.2.4 contient un paragraphe « remark on novelty » qui désamorce explicitement toute attente d'innovation algorithmique.

## 3. Étude d'ablation

L'ablation demandée figure dans le papier (Table 7, section 6.4) : détecteurs individuels → moyenne uniforme (ensemble simple) → vote majoritaire → fusion pondérée sans calibration → fusion calibrée (CWC) → fusion + rejet (architecture de décision complète), le tout sur des sorties de détecteurs identiques. Chaque étage est quantifié (F1 opérationnel, FPR, accuracy 15 classes). La révision la rend beaucoup plus visible : elle est désormais annoncée dans l'abstract et détaillée dans la contribution n°4 de l'introduction. La section 6 mesure en outre l'impact de chaque sous-système sur le suivant (synthèse en 6.10).

## 4. Discussion des limites

La section 8.3 (Limitations) a été étendue avec deux nouvelles sous-sections :

- **8.3.6 — Coût du consensus (latence et énergie)** : coût mesuré (~2 s par vote signé, dominé par la formation des blocs, croissance linéaire avec le quorum), ses conséquences pour le dimensionnement, et le coût énergétique traité honnêtement : pas de proof-of-work (Fabric est permissionné), donc surcoût faible, mais non mesuré — une mesure joules/alerte certifiée est proposée en extension.
- **8.3.7 — Dépendance au corpus d'évaluation** : tous les chiffres de détection proviennent de CICIDS2017 (défauts documentés discutés en 6.1) ; la machinerie de confiance est indépendante du dataset, mais les points de fonctionnement sont spécifiques au corpus ; la validation sur un second corpus puis en conditions réelles est identifiée comme la mesure la plus utile.
- **8.4** inclut désormais des perspectives de déploiement concrètes : insertion en tier de certification derrière un SOC existant, alertes co-signées vers le SIEM, notaires mappés sur les domaines de confiance de l'organisation (filiales, prestataires, régulateurs).

Le passage à grande échelle (réseau mono-hôte) et la dépendance au LLM étaient déjà couverts (8.3.2, 8.3.4).

## 5. Comparaison quantitative avec l'état de l'art

Une nouvelle section **6.9 « Positioning against recently reported blockchain, federated and agentic IDS results »** a été ajoutée, avec une table (Table 11) plaçant nos résultats mesurés à côté des chiffres publiés par les travaux récents les plus proches : blockchain + multi-agents (Liang et al., 83,2 % / NSL-KDD), multi-agents adaptatif (Soltani et al., taux de détection > 95 % / CIC-IDS2017-2018), fédéré + blockchain (Begum et al., 97,4 % / Edge-IIoTSet ; Ali et al., 97,3 % / ToN-IoT) et IDS agentique à base de LLM (H. Li et al., > 90 %). Chaque chiffre a été vérifié à la source. La section assume explicitement qu'il s'agit d'un contexte indicatif et non d'un benchmark contrôlé (datasets, granularités de classes et protocoles différents), et en tire trois observations robustes : (i) notre 96,60 % porte sur 15 classes, dans la même bande que les systèmes fédérés-blockchain sur des corpus IoT plus grossiers, et notre point certifié (99,65 %, FPR 0,04 %) dépasse tous les chiffres de la table au prix, explicite, de 12,7 % de flux déférés ; (ii) aucun des systèmes comparés ne rapporte de point de fonctionnement certifié, de FPR associé ni de coût on-chain par décision ; (iii) BAg-IDS est le seul dont les chiffres passent à travers le chemin de consensus plutôt qu'à côté.

## 6. Ouverture de la conclusion

Un paragraphe d'ouverture a été ajouté en conclusion : généralisation du patron « décisions co-signées par quorum, gouvernance on-chain » à d'autres applications de cybersécurité (triage de malware certifié, décisions de takedown phishing, partage de renseignement inter-organisations avec indicateurs signés par quorum, playbooks SOAR notarisés) ; intégration dans un environnement **Zero Trust**, où les alertes certifiées constituent les signaux vérifiables et attribuables qu'attend un policy engine ; et validation dans un **SOC de production**, en mesurant l'effet des alertes certifiées/déférées/annotées sur la charge des analystes et le temps de réponse.

---

*Version révisée : BAg-IDS_ComputersSecurity_v9.docx (~18 600 mots, 12 tables, 19 figures).*
