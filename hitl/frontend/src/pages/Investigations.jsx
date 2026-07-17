import { useEffect, useState } from "react";
import { api } from "../api.js";
import { useI18n } from "../i18n.jsx";

const SEV_COLOR = { low: "#35c8d6", medium: "#f0a202",
  high: "#ff8c42", critical: "#ff5c6c" };

export default function Investigations() {
  const { t } = useI18n();
  const [reports, setReports] = useState([]);
  const [sel, setSel] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const r = await api.investigations(30);
        if (alive) { setReports(r); if (!sel && r.length) setSel(r[0]); }
      } catch { /* investigator hors ligne */ }
      finally { if (alive) setLoading(false); }
    };
    tick();
    const id = setInterval(tick, 4000);
    return () => { alive = false; clearInterval(id); };
  }, []);   // eslint-disable-line

  if (loading) return <div className="empty">{t("loading")}</div>;

  return (
    <div className="grid cols-2" style={{ gridTemplateColumns: "1fr 1.3fr" }}>
      <div className="card">
        <h3>{t("investigations_n")} ({reports.length})</h3>
        {reports.length === 0
          ? <div className="empty">{t("no_investigations")}</div>
          : (
          <table>
            <thead><tr>
              <th>{t("cls")}</th><th>{t("severity")}</th>
              <th>{t("campaign")}</th><th>{t("steps")}</th>
            </tr></thead>
            <tbody>
              {reports.map((r) => (
                <tr key={r.report_id}
                  className={sel?.report_id === r.report_id ? "active" : ""}
                  onClick={() => setSel(r)} style={{ cursor: "pointer" }}>
                  <td>{r.alert_id?.slice(0, 8)}…</td>
                  <td><span className="badge" style={{
                    background: SEV_COLOR[r.severity] || "#8ea0bf",
                    color: "#0b1220" }}>{r.severity}</span></td>
                  <td>{r.campaign_suspected
                    ? <span className="badge high">{t("yes")}</span>
                    : <span className="muted">{t("no")}</span>}</td>
                  <td>{(r.steps || []).length}</td>
                </tr>
              ))}
            </tbody>
          </table>)}
      </div>

      <div className="card">
        <h3>{t("agentic_trace")}</h3>
        {!sel ? <div className="muted">{t("select_investigation")}</div> : (
          <div>
            <div className="field">
              <label>{t("identifier")}</label>
              <div className="mono">{sel.alert_id}</div>
            </div>
            <div className="row" style={{ gap: 18, marginBottom: 8 }}>
              <div><span className="muted">{t("severity")}: </span>
                <b style={{ color: SEV_COLOR[sel.severity] }}>{sel.severity}</b></div>
              <div><span className="muted">{t("campaign")}: </span>
                <b>{sel.campaign_suspected ? t("yes") : t("no")}</b></div>
              <div><span className="muted">{t("provider")}: </span>
                {sel.provider}</div>
            </div>

            <label style={{ fontSize: 12, color: "var(--muted)",
              textTransform: "uppercase" }}>{t("reasoning_steps")}</label>
            <div className="agent-steps">
              {(sel.steps || []).map((s) => (
                <div className="agent-step" key={s.index}>
                  <div className="step-head">
                    <span className="step-num">{s.index}</span>
                    <span className="step-tool">{s.tool}</span>
                  </div>
                  <div className="step-thought">💭 {s.thought}</div>
                  <div className="step-obs">▸ {s.observation}</div>
                </div>
              ))}
            </div>

            <div className="field" style={{ marginTop: 12 }}>
              <label>{t("summary")}</label>
              <div className="muted" style={{ fontSize: 13 }}>{sel.summary}</div>
            </div>
            <div className="field">
              <label>{t("recommended_response")}</label>
              <div>{(sel.recommended_response || []).join(" · ")}</div>
            </div>
            {(sel.related_incidents || []).length > 0 && (
              <div className="field">
                <label>{t("related_incidents")} ({sel.related_incidents.length})</label>
                <div className="mono" style={{ fontSize: 11 }}>
                  {sel.related_incidents.slice(0, 8).map((x) =>
                    x.slice(0, 8)).join(", ")}</div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
