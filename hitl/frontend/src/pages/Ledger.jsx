import { useEffect, useState } from "react";
import { api } from "../api.js";
import { useI18n } from "../i18n.jsx";

const KIND_COLORS = {
  ALERT: "#4f8cff", VOTE: "#35c8d6", ALERT_CERTIFIED: "#2ecc71",
  ACTION_PLANNED: "#f0a202", GOVERNANCE: "#7d4fd3",
};

export default function Ledger() {
  const { t } = useI18n();
  const [entries, setEntries] = useState([]);
  const [fabric, setFabric] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const d = await api.ledger(300);
        if (alive) { setEntries(d.entries); setFabric(d.fabric); setLoading(false); }
      } catch { if (alive) setLoading(false); }
    };
    tick();
    const id = setInterval(tick, 5000);
    return () => { alive = false; clearInterval(id); };
  }, []);

  if (loading) return <div className="empty">{t("loading")}</div>;

  return (
    <>
      <div className="grid cols-3">
        <div className="card stat">
          <span className="val" style={{ color: "#4f8cff" }}>{entries.length}</span>
          <span className="lbl">{t("ledger_entries")}</span>
        </div>
        <div className="card stat">
          <span className="val" style={{ color: fabric ? "#2ecc71" : "#8ea0bf" }}>
            {fabric ? "Fabric" : "Local"}
          </span>
          <span className="lbl">{t("consensus_backend")}</span>
          <span className="sub">
            {fabric ? `${fabric.channel} · ${fabric.chaincode}`
                    : t("local_mirror")}</span>
        </div>
        <div className="card stat">
          <span className="val" style={{ color: "#2ecc71" }}>✔</span>
          <span className="lbl">{t("chain_integrity")}</span>
          <span className="sub">{t("hash_verified")}</span>
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h3>{t("transactions")}</h3>
        <table>
          <thead><tr>
            <th>#</th><th>{t("type")}</th><th>{t("content")}</th><th>Hash</th>
          </tr></thead>
          <tbody>
            {entries.map((e) => (
              <tr key={e.index}>
                <td className="mono">{e.index}</td>
                <td>
                  <span className="badge" style={{
                    background: (KIND_COLORS[e.kind] || "#26344f") + "22",
                    color: KIND_COLORS[e.kind] || "#8ea0bf" }}>
                    {e.kind}
                  </span>
                </td>
                <td className="muted" style={{ maxWidth: 380, overflow: "hidden",
                  textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {summarize(e)}
                </td>
                <td className="mono muted">{(e.hash || "").slice(0, 12)}…</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function summarize(e) {
  const p = e.payload || {};
  if (e.kind === "ALERT")
    return `${p.sentinel_id} → ${p.detection?.predicted_class} (${p.severity})`;
  if (e.kind === "VOTE")
    return `${p.voter_id} : ${p.approve ? "approuve" : "rejette"} ${p.alert_id?.slice(0, 8)}`;
  if (e.kind === "ALERT_CERTIFIED")
    return `${p.alert_id?.slice(0, 8)} certifié (${p.approvals} approbations)`;
  if (e.kind === "ACTION_PLANNED")
    return `${p.action_type} sur ${p.alert_id?.slice(0, 8)}`;
  return JSON.stringify(p).slice(0, 80);
}
