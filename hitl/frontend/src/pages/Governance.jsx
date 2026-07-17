import { useEffect, useState } from "react";
import { api } from "../api.js";
import { useI18n } from "../i18n.jsx";

export default function Governance() {
  const { t } = useI18n();
  const [snap, setSnap] = useState(null);
  const [gov, setGov] = useState([]);
  const [form, setForm] = useState({});
  const [msg, setMsg] = useState(null);
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    const s = await api.policy();
    setSnap(s);
    setForm({
      tau: s.policy.tau, quorum: s.policy.quorum,
      executor_dry_run: s.policy.executor_dry_run,
    });
    try {
      const g = await api.governanceLog(100);
      // Nouvelle forme {local, onchain} ; repli si ancienne forme (liste).
      setGov(Array.isArray(g) ? g : (g.local || []));
    } catch { /* ignore */ }
  };
  useEffect(() => { refresh(); }, []);

  async function toggle() {
    setBusy(true); setMsg(null);
    try {
      const r = await api.toggleHitl(!snap.hitl_enabled);
      setMsg(`HITL ${r.hitl_enabled ? "activé" : "désactivé"} — ancrage : ${r.anchor.anchored}`);
      await refresh();
    } catch (e) { setMsg("Erreur : " + e.message); }
    finally { setBusy(false); }
  }

  async function savePolicy() {
    setBusy(true); setMsg(null);
    try {
      const r = await api.setPolicy({
        tau: parseFloat(form.tau), quorum: parseInt(form.quorum),
        executor_dry_run: form.executor_dry_run,
      });
      setMsg(`Paramètres enregistrés — ancrage : ${r.anchor.anchored}`);
      await refresh();
    } catch (e) { setMsg("Erreur : " + e.message); }
    finally { setBusy(false); }
  }

  if (!snap) return <div className="empty">{t("loading")}</div>;

  return (
    <>
      <div className="grid cols-2">
        <div className="card">
          <h3>{t("hitl_switch")}</h3>
          <p className="muted" style={{ fontSize: 13 }}>{t("hitl_desc")}</p>
          <div className="row spread" style={{ marginTop: 16 }}>
            <span className={`pill ${snap.hitl_enabled ? "on" : "off"}`}>
              <span className="dot" />
              {snap.hitl_enabled ? t("active") : t("inactive")}
            </span>
            <button className={`toggle-btn ${snap.hitl_enabled ? "danger" : "success"}`}
              onClick={toggle} disabled={busy}>
              {snap.hitl_enabled ? t("disable_auto") : t("enable_super")}
            </button>
          </div>
        </div>

        <div className="card">
          <h3>{t("governed_params")}</h3>
          <div className="field">
            <label>{t("tau_label")}</label>
            <input type="number" step="0.01" min="0" max="1" value={form.tau}
              onChange={(e) => setForm({ ...form, tau: e.target.value })} />
          </div>
          <div className="field">
            <label>{t("quorum_label")}</label>
            <input type="number" min="1" max="3" value={form.quorum}
              onChange={(e) => setForm({ ...form, quorum: e.target.value })} />
          </div>
          <div className="field">
            <label>{t("executor_mode")}</label>
            <select value={form.executor_dry_run ? "1" : "0"}
              onChange={(e) => setForm({ ...form,
                executor_dry_run: e.target.value === "1" })}>
              <option value="1">{t("dry_run")}</option>
              <option value="0">{t("live")}</option>
            </select>
          </div>
          <button className="primary" onClick={savePolicy} disabled={busy}>
            {t("save_params")}
          </button>
        </div>
      </div>

      {msg && <div className="card" style={{ marginTop: 16 }}>
        <span className="muted">{msg}</span></div>}

      <div className="card" style={{ marginTop: 16 }}>
        <h3>{t("gov_log")}</h3>
        {gov.length === 0
          ? <div className="muted">{t("no_gov")}</div>
          : (
          <table>
            <thead><tr>
              <th>{t("time")}</th><th>{t("action")}</th>
              <th>{t("actor")}</th><th>{t("details")}</th>
            </tr></thead>
            <tbody>
              {gov.map((g, i) => (
                <tr key={i}>
                  <td className="muted">
                    {new Date(g.ts * 1000).toLocaleTimeString()}</td>
                  <td><span className="badge" style={{
                    background: "#7d4fd322", color: "#a98ce6" }}>{g.action}</span></td>
                  <td>{g.actor}</td>
                  <td className="mono muted" style={{ fontSize: 11 }}>
                    {JSON.stringify(g.details).slice(0, 70)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
