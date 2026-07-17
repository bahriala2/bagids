import { useEffect, useState } from "react";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { useI18n } from "../i18n.jsx";

export default function Approvals() {
  const { can } = useAuth();
  const { t } = useI18n();
  const [pending, setPending] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [busy, setBusy] = useState(null);

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
                <tr key={it.id}>
                  <td>{it.predicted_class}</td>
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
