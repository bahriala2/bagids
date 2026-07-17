import { useEffect, useState } from "react";
import { api } from "../api.js";
import { useI18n } from "../i18n.jsx";

export default function Incidents() {
  const { t } = useI18n();
  const [incidents, setIncidents] = useState([]);
  const [advisories, setAdvisories] = useState({});
  const [sel, setSel] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const d = await api.incidents(300);
        if (alive) { setIncidents(d); setLoading(false); }
      } catch { if (alive) setLoading(false); }
      try {
        const a = await api.advisories(80);
        if (alive) setAdvisories(a || {});
      } catch { /* notary advisory off */ }
    };
    tick();
    const id = setInterval(tick, 5000);
    return () => { alive = false; clearInterval(id); };
  }, []);

  if (loading) return <div className="empty">{t("loading")}</div>;

  return (
    <div className="grid cols-2" style={{ gridTemplateColumns: "1.4fr 1fr" }}>
      <div className="card">
        <h3>{t("incidents_n")} ({incidents.length})</h3>
        {incidents.length === 0
          ? <div className="empty">{t("no_events")}</div>
          : (
          <table>
            <thead><tr>
              <th>{t("cls")}</th><th>{t("class_conf").split("/")[1] || "Confiance"}</th>
              <th>{t("severity")}</th><th>{t("decision")}</th>
            </tr></thead>
            <tbody>
              {incidents.map((it) => (
                <tr key={it.alert_id} onClick={() => setSel(it)}
                  style={{ cursor: "pointer" }}>
                  <td>{it.predicted_class || "—"}</td>
                  <td className="mono">
                    {it.confidence != null ? (it.confidence * 100).toFixed(1) + "%" : "—"}
                  </td>
                  <td>{it.severity
                    ? <span className={`badge ${it.severity}`}>{it.severity}</span>
                    : "—"}</td>
                  <td>{it.certified
                    ? <span className="badge certified">{t("certified_badge")}</span>
                    : <span className="badge pending">{t("in_progress")}</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <h3>{t("detail")}</h3>
        {!sel ? <div className="muted">{t("select_incident")}</div> : (
          <div>
            <div className="field">
              <label>{t("identifier")}</label>
              <div className="mono">{sel.alert_id}</div>
            </div>
            <div className="field">
              <label>{t("class_conf")}</label>
              <div>{sel.predicted_class} —{" "}
                {sel.confidence != null ? (sel.confidence * 100).toFixed(2) + "%" : "—"}</div>
            </div>
            <div className="field">
              <label>{t("notary_votes")}</label>
              {sel.votes && Object.keys(sel.votes).length
                ? Object.entries(sel.votes).map(([v, ok]) => (
                    <div key={v} className="mono">
                      {v} : {ok ? "✔ " + t("approved") : "✘ " + t("rejected_v")}
                    </div>))
                : <span className="muted">{t("none")}</span>}
            </div>
            {sel.deliberation && (
              <div className="field">
                <label>{t("deliberation")}</label>
                <div className="muted" style={{ fontSize: 13 }}>
                  {sel.deliberation.rationale}
                </div>
                <div style={{ marginTop: 6 }}>
                  {t("actions")} : {(sel.deliberation.recommended_actions || []).join(", ")}
                </div>
              </div>
            )}
            <div className="field">
              <label>{t("certification")}</label>
              {sel.certified
                ? <span className="badge certified">
                    {t("certified_badge")} ({sel.approvals})</span>
                : <span className="badge pending">{t("in_progress")}</span>}
            </div>
            {advisories[sel.alert_id] && (
              <div className="field">
                <label>{t("advisory_opinion")}</label>
                {Object.entries(advisories[sel.alert_id]).map(([v, a]) => (
                  <div key={v} style={{ fontSize: 12.5, marginBottom: 4 }}>
                    <span className="mono" style={{ color: "var(--accent-2)" }}>
                      {v}</span>
                    <span className="muted"> ({a.provider}): </span>
                    {a.opinion}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
