import { Fragment, useEffect, useState } from "react";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { useI18n } from "../i18n.jsx";

/* ---------------------------------------------------------------- XAI
 * Panneau d'aide à la décision d'une remédiation en attente :
 *   1. nature de l'attaque (base de connaissances),
 *   2. interprétation du flux (LLM ancré sur SHAP, ou socle déterministe),
 *   3. checklist de vérification pour l'analyste,
 *   4. recommandation consultative (règle déterministe, jamais décisionnelle),
 *   5. preuves : barres d'attribution SHAP.
 * Le tout est calculé hors chemin critique par le Sentinel et attaché à
 * l'élément par le backend quand il est prêt. */
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

  const L = (obj) => (obj && (obj[lang] || obj.en)) || null;
  const feats = ex.top_features || [];
  const maxAbs = Math.max(...feats.map((f) => Math.abs(f.shap)), 1e-9);
  const reco = ex.recommendation;
  const checks = ex.checks && (ex.checks[lang] || ex.checks.en);
  const sectionTitle = {
    fontSize: 12, textTransform: "uppercase", letterSpacing: ".05em",
    color: "var(--muted)", margin: "12px 0 4px" };

  return (
    <div>
      {/* 1. nature de l'attaque + accord des détecteurs */}
      {L(ex.attack_profile) && (
        <>
          <div style={{ ...sectionTitle, marginTop: 0 }}>{t("xai_about")}</div>
          <p style={{ margin: 0 }}>
            {L(ex.attack_profile)}
            {ex.agreement && (
              <span className="muted">
                {" "}({t("xai_agreement")} : {ex.agreement.agree}/
                {ex.agreement.total}
                {ex.per_model_votes &&
                  " — " + Object.entries(ex.per_model_votes)
                    .map(([m, c]) => `${m}: ${c}`).join(", ")})
              </span>
            )}
          </p>
        </>
      )}

      {/* 2. interprétation du flux */}
      <div style={sectionTitle}>{t("xai_interpretation")}</div>
      <p style={{ margin: 0 }}>
        {L(ex.interpretation)
          || (ex.narrative && L(ex.narrative))
          || t("xai_template_intro")
              .replace("{cls}", ex.predicted_class)
              .replace("{conf}", `${Math.round((ex.confidence || 0) * 100)}%`)}
      </p>

      {/* 3. checklist analyste */}
      {checks && checks.length > 0 && (
        <>
          <div style={sectionTitle}>{t("xai_checks")}</div>
          <ul style={{ margin: 0, paddingInlineStart: 20 }}>
            {checks.map((c, i) => <li key={i}>{c}</li>)}
          </ul>
        </>
      )}

      {/* 4. recommandation consultative */}
      {reco && (
        <>
          <div style={sectionTitle}>{t("xai_reco")}</div>
          <div style={{
            border: "1px solid var(--border)", borderRadius: 8,
            padding: "8px 12px",
            borderInlineStartWidth: 4,
            borderInlineStartColor: reco.verdict === "approve"
              ? "var(--green)" : "var(--amber)" }}>
            <strong style={{
              color: reco.verdict === "approve"
                ? "var(--green)" : "var(--amber)" }}>
              {reco.verdict === "approve"
                ? `✔ ${t("xai_reco_approve")}`
                : `⚠ ${t("xai_reco_verify")}`}
            </strong>
            <p style={{ margin: "4px 0 0" }}>{L(reco.rationale)}</p>
            <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
              {t("xai_advisory")}
            </div>
          </div>
        </>
      )}

      {/* 5. preuves : attributions SHAP */}
      <div style={sectionTitle}>{t("xai_evidence")}</div>
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
        {" · "}{t("xai_narrative_by")} : {ex.narrative_provider}
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
