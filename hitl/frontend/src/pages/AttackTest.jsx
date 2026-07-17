import { useEffect, useState } from "react";
import { api } from "../api.js";
import { useI18n } from "../i18n.jsx";

const VERDICT_BADGE = {
  attack: { cls: "high", key: "detected_attack" },
  benign: { cls: "certified", key: "detected_benign" },
  rejected: { cls: "pending", key: "detected_rejected" },
};

// Parse un texte CSV : chaque ligne = un flux. Dernière colonne = label
// si elle n'est pas numérique. Retourne { flows: number[][], labels: [] }.
function parseCsv(text) {
  const flows = [], labels = [];
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith("#")) continue;
    const parts = line.split(",").map((s) => s.trim());
    let label = null;
    if (parts.length && isNaN(Number(parts[parts.length - 1]))) {
      label = parts.pop();
    }
    const nums = parts.map(Number);
    if (nums.some((n) => Number.isNaN(n))) continue;
    flows.push(nums);
    labels.push(label);
  }
  return { flows, labels };
}

export default function AttackTest() {
  const { t } = useI18n();
  const [text, setText] = useState("");
  const [meta, setMeta] = useState(null);
  const [results, setResults] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.detectionMeta().then(setMeta).catch(() => {}); }, []);

  async function run() {
    setErr(""); setResults(null); setBusy(true);
    try {
      const { flows, labels } = parseCsv(text);
      if (!flows.length) { setErr("Aucun flux valide détecté."); return; }
      const r = await api.detectionInject(flows, labels);
      if (r.error) { setErr(r.error); return; }
      setResults(r.results || []);
    } catch (e) { setErr(e.message); }
    finally { setBusy(false); }
  }

  function loadSample() {
    // Exemple : un flux type PortScan (valeurs illustratives, 78 features).
    // L'utilisateur remplacera par ses propres flux CICIDS bruts.
    const n = meta?.n_features || 78;
    const row = Array.from({ length: n }, (_, i) => (i % 7) * 3.5).join(",");
    setText(row + ",PortScan");
  }

  return (
    <>
      <div className="card">
        <p className="muted" style={{ fontSize: 13 }}>{t("attack_help")}</p>
        {meta && !meta.error && (
          <p className="muted" style={{ fontSize: 12 }}>
            {meta.n_features} features · τ={meta.tau} · {meta.classes?.length}{" "}
            classes</p>
        )}
        <textarea value={text} onChange={(e) => setText(e.target.value)}
          rows={8} placeholder={t("paste_flows")}
          style={{ width: "100%", fontFamily: "monospace", fontSize: 12,
            background: "var(--panel-2)", color: "var(--text)",
            border: "1px solid var(--border)", borderRadius: 8, padding: 10 }} />
        <div className="row" style={{ marginTop: 10 }}>
          <button className="primary" onClick={run} disabled={busy}>
            {busy ? "…" : t("run_test")}
          </button>
          <button onClick={loadSample}>{t("load_sample")}</button>
        </div>
        {err && <div className="err" style={{ marginTop: 8 }}>{err}</div>}
      </div>

      {results && (
        <div className="card" style={{ marginTop: 16 }}>
          <h3>{t("test_results")} ({results.length})</h3>
          <table>
            <thead><tr>
              <th>#</th><th>{t("verdict")}</th><th>{t("predicted")}</th>
              <th>{t("confidence")}</th><th>{t("true_label")}</th>
            </tr></thead>
            <tbody>
              {results.map((r, i) => {
                const b = VERDICT_BADGE[r.verdict] || VERDICT_BADGE.rejected;
                return (
                  <tr key={i}>
                    <td>{i + 1}</td>
                    <td><span className={`badge ${b.cls}`}>{t(b.key)}</span></td>
                    <td>{r.predicted_class}</td>
                    <td>{(r.confidence * 100).toFixed(1)}%</td>
                    <td className="muted">{r.true_label || "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
