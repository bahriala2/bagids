import { Fragment, useEffect, useState } from "react";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { useI18n } from "../i18n.jsx";

/* ---------------------------------------------------------------- XAI
 * Panneau d'explication d'une remédiation en attente : narration (LLM,
 * ancrée sur les attributions) + barres des features les plus influentes
 * (SHAP). L'explication est calculée hors chemin critique par le Sentinel
 * et attachée à l'élément par le backend quand elle est prête. */
function ExplanationPanel({ item }) {
  const { t, lang } = useI18n();
  const ex = item.explanation;

  if (!item.flow_id) {
    return <div className="muted">{t("xai_unavailable")}</div>;
  }
  if (ex == null) {
    return <div className="muted">⏳ {t("xai_computing")}</div>;
  }
  if (ex.error) {
    return (
      <div className="muted">
        {t("xai_failed")} <code>{ex.error}</code>
      </div>
    );
  }

  const feats = ex.top_features || [];
  const maxAbs = Math.max(...feats.map((f) => Math.abs(f.shap)), 1e-9);
  const narrative = ex.narrative && (ex.narrative[lang] || ex.narrative.en);
  const intro = t("xai_template_intro")
    .replace("{cls}", ex.predicted_class)
    .replace("{conf}", `${Math.round((ex.confidence || 0) * 100)}%`);

  return (
    <div>
      <p style={{ marginTop: 0 }}>{narrative || intro}</p>
      <div className="muted" style={{ fontSize: 13, marginBottom: 6 }}>
        {t("xai_top_features")}
      </div>
      {feats.map((f) => (
        <div key={f.name} style={{
          display: "flex", alignItems: "center", gap: 8, marginBottom: 3 }}>
          <span style={{
            width: 190, fontSize: 12, overflow: "hidden",
            textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={f.name}>
            {f.name}
          </span>
          <div style={{ flex: 1, background: "var(--panel-2)",
            borderRadius: 4, height: 14, position: "relative" }}>
            <div style={{
              width: `${Math.max(3, 100 * Math.abs(f.shap) / maxAbs)}%`,
              height: "100%", borderRadius: 4,
              background: f.direction === "supports"
                ? "var(--red)" : "var(--accent)",
              opacity: 0.85 }} />
          </div>
          <span className="muted" style={{
            width: 150, fontSize: 12, textAlign: "end" }}>
            {f.shap > 0 ? "+" : ""}{f.shap.toFixed(4)}{" · "}
            {f.direction === "supports" ? t("xai_supports") : t("xai_opposes")}
          </span>
        </div>
      ))}
      <div className="muted" style={{ fontSize: 12, marginTop: 8 }}>
        {t("xai_method")} : {ex.method}
        {ex.narrative
          ? <> · {t("xai_narrative_by")} : {ex.narrative_provider}</>
          : null}
        {" · "}{(ex.latency_ms / 1000).toFixed(1)} s
      </div>
    </div>
  );
}

export default function Approvals() {
  const { can } = useAuth();
  const { t } = useI18n();
  const [pending, setPending] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [busy, setBusy] = useState(null);
  const [open, setOpen] = useState(null);   // id de l'alerte dépliée (XAI)

  const refresh = async () => {
    try {
      setPending(await api.pending());
      setDecisions(await api.decisions(50));
    } catch { /* ignore */ }
  };
  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 4000);
    return () => clearInterval(id);
  }, []);

  async function decide(id, approve) {
    setBusy(id);
    try {
      const reason = approve ? null
        : prompt("Motif du rejet (optionnel) :") || null;
      await api.decide(id, approve, reason);
      await refresh();
    } catch (e) { alert(e.message); }
    finally { setBusy(null); }
  }

  return (
    <>
      <div className="card">
        <h3>{t("pending_title")} ({pending.length})</h3>
        {pending.length === 0
          ? <div className="empty">{t("no_pending")}</div>
          : (
          <table>
            <thead><tr>
              <th>{t("cls")}</th><th>{t("severity")}</th>
              <th>{t("proposed_actions")}</th>
              <th>{t("received")}</th>
              <th style={{ width: 200 }}>{t("decision")}</th>
            </tr></thead>
            <tbody>
              {pending.map((it) => (
                <Fragment key={it.id}>
                <tr>
                  <td>
                    {it.predicted_class}{" "}
                    <button className="ghost" style={{
                      fontSize: 12, padding: "2px 8px" }}
                      onClick={() => setOpen(open === it.id ? null : it.id)}>
                      {open === it.id ? "▲" : "▼"} {t("why_alert")}
                    </button>
                  </td>
                  <td><span className={`badge ${it.severity}`}>{it.severity}</span></td>
                  <td className="muted">{(it.actions || []).join(", ")}</td>
                  <td className="muted">
                    {new Date(it.created_at * 1000).toLocaleTimeString()}</td>
                  <td>
                    {can("analyst") ? (
                      <div className="row">
                        <button className="success" disabled={busy === it.id}
                          onClick={() => decide(it.id, true)}>{t("approve")}</button>
                        <button className="danger" disabled={busy === it.id}
                          onClick={() => decide(it.id, false)}>{t("reject")}</button>
                      </div>
                    ) : <span className="muted">{t("read_only")}</span>}
                  </td>
                </tr>
                {open === it.id && (
                  <tr>
                    <td colSpan={5} style={{
                      background: "var(--bg-2)", borderRadius: 6 }}>
                      <div style={{ padding: "10px 14px" }}>
                        <strong>{t("xai_title")}</strong>
                        <div style={{ marginTop: 8 }}>
                          <ExplanationPanel item={it} />
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
                </Fragment>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h3>{t("recent_decisions")}</h3>
        {decisions.length === 0
          ? <div className="muted">{t("no_decisions")}</div>
          : (
          <table>
            <thead><tr>
              <th>{t("cls")}</th><th>{t("decision")}</th>
              <th>{t("by")}</th><th>{t("reason")}</th>
            </tr></thead>
            <tbody>
              {decisions.map((d) => (
                <tr key={d.id}>
                  <td>{d.predicted_class}</td>
                  <td>{d.approved
                    ? <span className="badge certified">{t("approved")}</span>
                    : <span className="badge high">{t("rejected_v")}</span>}</td>
                  <td>{d.decided_by}</td>
                  <td className="muted">{d.reason || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
