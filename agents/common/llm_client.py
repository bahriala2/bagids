"""
BAg-IDS — Client LLM pour la couche délibérative des agents.

Deux backends interchangeables, tous deux compatibles avec l'API
OpenAI /chat/completions :

  - OpenRouter (cloud, modèles gratuits disponibles) :
      base_url = https://openrouter.ai/api/v1
      clé dans la variable d'environnement OPENROUTER_API_KEY
  - LM Studio (local, aucun coût ni réseau) :
      base_url = http://localhost:1234/v1 (serveur local LM Studio)

L'ordre d'essai est configurable ; si aucun backend LLM n'est joignable,
`RuleBasedFallback` fournit une délibération dégradée à base de règles,
pour que les agents restent autonomes même sans LLM (et pour que les
mesures de la phase 2 restent reproductibles).
"""

from __future__ import annotations

import json
import logging
import os
import time

import httpx

logger = logging.getLogger("bag_ids.agents.llm")


class LLMError(RuntimeError):
    pass


class LLMClient:
    """Client minimal /chat/completions, agnostique du fournisseur."""

    def __init__(self, provider: str, base_url: str, model: str,
                 api_key: str | None = None, timeout_s: float = 60.0):
        self.provider = provider
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout_s = timeout_s

    def is_available(self) -> bool:
        """Sonde rapide du backend (liste des modèles)."""
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            r = httpx.get(f"{self.base_url}/models", headers=headers, timeout=5.0)
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    def chat(self, system: str, user: str, temperature: float = 0.2,
             max_tokens: int = 1024) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        t0 = time.perf_counter()
        try:
            r = httpx.post(f"{self.base_url}/chat/completions",
                           headers=headers, json=payload, timeout=self.timeout_s)
        except httpx.HTTPError as exc:
            raise LLMError(f"{self.provider} injoignable : {exc}") from exc
        if r.status_code != 200:
            raise LLMError(f"{self.provider} HTTP {r.status_code} : {r.text[:300]}")
        data = r.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Réponse {self.provider} inattendue : {data}") from exc
        dt_ms = 1000 * (time.perf_counter() - t0)
        logger.info("LLM %s/%s : réponse en %.0f ms", self.provider, self.model, dt_ms)
        return content


def build_clients(llm_cfg: dict) -> list[LLMClient]:
    """Construit la liste des clients dans l'ordre de préférence configuré.

    Chaque backend accepte `model` (str) ou `models` (liste, essayée dans
    l'ordre) : utile avec les modèles gratuits OpenRouter, souvent
    rate-limités individuellement (HTTP 429) mais rarement tous à la fois.
    """
    clients: list[LLMClient] = []
    for name in llm_cfg.get("provider_order", ["openrouter", "lmstudio"]):
        cfg = llm_cfg.get(name)
        if not cfg:
            continue
        api_key = None
        if cfg.get("api_key_env"):
            api_key = os.environ.get(cfg["api_key_env"])
            if not api_key:
                logger.warning(
                    "Backend %s ignoré : variable %s non définie",
                    name, cfg["api_key_env"])
                continue
        elif cfg.get("api_key"):
            api_key = cfg["api_key"]
        models = cfg.get("models") or [cfg["model"]]
        for model in models:
            clients.append(LLMClient(
                provider=name,
                base_url=cfg["base_url"],
                model=model,
                api_key=api_key,
                timeout_s=float(cfg.get("timeout_s", 60)),
            ))
    return clients


class Deliberator:
    """Couche délibérative : interroge le premier backend disponible,
    exige une réponse JSON structurée, sinon repli sur règles."""

    SYSTEM_PROMPT = (
        "You are the deliberative layer of an autonomous intrusion-detection "
        "agent (BAg-IDS). You receive a security event summary produced by a "
        "calibrated ensemble of neural detectors. Reason about it and reply "
        "with a single JSON object, nothing else, with the keys: "
        '"severity" (one of "low","medium","high","critical"), '
        '"rationale" (2-4 sentences, technical), '
        '"recommended_actions" (list of short imperative strings, chosen '
        'among: block_ip, rate_limit, isolate_host, recalibrate, retrain, '
        "notify_operator, no_action)."
    )

    def __init__(self, clients: list[LLMClient]):
        self.clients = clients

    def deliberate(self, trigger: str, event_summary: str) -> dict:
        """Retourne un dict {severity, rationale, recommended_actions,
        provider, model, latency_ms} ; ne lève jamais (repli sur règles)."""
        t0 = time.perf_counter()
        for client in self.clients:
            try:
                raw = client.chat(self.SYSTEM_PROMPT, event_summary)
                parsed = self._parse_json(raw)
                parsed.update({
                    "provider": client.provider,
                    "model": client.model,
                    "latency_ms": 1000 * (time.perf_counter() - t0),
                })
                return parsed
            except (LLMError, ValueError) as exc:
                logger.warning("Délibération %s échouée : %s", client.provider, exc)
        logger.warning("Aucun backend LLM disponible : repli sur règles")
        result = RuleBasedFallback.deliberate(trigger, event_summary)
        result["latency_ms"] = 1000 * (time.perf_counter() - t0)
        return result

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """Extrait l'objet JSON de la réponse (tolère les fences markdown)."""
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"Pas de JSON dans la réponse LLM : {raw[:200]}")
        data = json.loads(text[start:end + 1])
        if not {"severity", "rationale", "recommended_actions"} <= set(data):
            raise ValueError(f"Clés manquantes dans la réponse LLM : {data}")
        if data["severity"] not in ("low", "medium", "high", "critical"):
            raise ValueError(f"Sévérité invalide : {data['severity']}")
        return data


class RuleBasedFallback:
    """Délibération dégradée sans LLM : règles simples sur le résumé
    d'événement. Garantit l'autonomie de l'agent hors connectivité."""

    #: classes considérées à fort impact immédiat
    HIGH_IMPACT = ("ddos", "dos", "heartbleed", "infiltration", "bot")

    @classmethod
    def deliberate(cls, trigger: str, event_summary: str) -> dict:
        text = event_summary.lower()
        if any(k in text for k in cls.HIGH_IMPACT):
            severity, actions = "high", ["block_ip", "notify_operator"]
        elif "rejected" in text or "drift" in text:
            severity, actions = "medium", ["recalibrate", "notify_operator"]
        else:
            severity, actions = "low", ["notify_operator"]
        return {
            "severity": severity,
            "rationale": (
                "Rule-based fallback (no LLM backend reachable): decision "
                f"derived from keyword heuristics on trigger '{trigger}'."
            ),
            "recommended_actions": actions,
            "provider": "rules-fallback",
            "model": "keyword-heuristics-v1",
        }
