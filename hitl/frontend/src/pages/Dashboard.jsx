import { useEffect, useState } from "react";
import {
  PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  Tooltip, Legend,
} from "recharts";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { useI18n } from "../i18n.jsx";

const COLORS = { benign: "#2ecc71", attack: "#ff5c6c", rejected: "#f0a202" };

function DetectionControl() {
  const { t } = useI18n();
  const { can } = useAuth();
  const [st, setSt] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try { const s = await api.detectionStatus(); if (alive) setSt(s); }
      catch { /* ignore */ }
    };
    tick();
    const id = setInterval(tick, 2500);
    return () => { alive = false; clearInterval(id); };
  }, []);

  const running = st?.running;
  async function toggle() {
    setBusy(true);
    try { running ? await api.detectionStop() : await api.detectionStart(); }
    finally { setTimeout(() => setBusy(false), 1500); }
  }

  return (
    <div className="card" style={{ display: "flex", alignItems: "center",
      justifyContent: "space-between", gap: 16, marginBottom: 16 }}>
      <div className="row" style={{ gap: 14 }}>
        <span className={`pill ${running ? "on" : "off"}`}>
          <span className="dot" />
          {running ? t("detection_running") : t("detection_stopped")}
        </span>
        <span className="muted">
          {t("flows_processed")}: <b style={{ color: "var(--accent)" }}>
            {st?.flows_processed ?? 0}</b>
          {running && st?.sentinel_online === false
            && ` · ${t("sentinel_starting")}`}
        </span>
      </div>
      {can("analyst") && (
        <button className={`toggle-btn ${running ? "danger" : "success"}`}
          onClick={toggle} disabled={busy}>
          {busy ? "…" : running ? t("stop_detection") : t("start_detection")}
        </button>
      )}
    </div>
  );
}

function Stat({ val, lbl, sub, color }) {
  return (
    <div className="card stat">
      <span className="val" style={{ color }}>{val}</span>
      <span className="lbl">{lbl}</span>
      {sub && <span className="sub">{sub}</span>}
    </div>
  );
}

export default function Dashboard() {
  const { t } = useI18n();
  const { can } = useAuth();
  const [data, setData] = useState(null);

  // Flux temps réel via WebSocket, avec repli sur polling REST.
  useEffect(() => {
    let ws, poll, alive = true;
    const apply = (d) => { if (alive) setData(d); };
    try {
      ws = new WebSocket(
        `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);
      ws.onmessage = (ev) => apply(JSON.parse(ev.data));
      ws.onerror = () => { if (!poll) startPoll(); };
    } catch { startPoll(); }
    function startPoll() {
      const tick = async () => {
        try {
          const d = await api.dashboard();
          apply({ metrics: d.metrics, hitl: d.hitl, pending: [],
                  events: d.recent_events });
        } catch { /* ignore */ }
      };
      tick(); poll = setInterval(tick, 3000);
    }
    return () => { alive = false; ws && ws.close(); poll && clearInterval(poll); };
  }, []);

  if (!data) return <div className="empty">{t("loading")}</div>;
  const m = data.metrics || {};
  const verdicts = [
    { name: t("benign"), key: "benign", value: m.verdict_benign || 0 },
    { name: t("attack"), key: "attack", value: m.verdict_attack || 0 },
    { name: t("rejected"), key: "rejected", value: m.verdict_rejected || 0 },
  ];

  return (
    <>
      <DetectionControl />
      <div className="grid cols-4">
        <Stat val={m.flows_processed ?? 0} lbl={t("flows_processed")}
          sub={m.sentinel_online ? t("sentinel_online") : t("sentinel_offline")}
          color="#4f8cff" />
        <Stat val={m.verdict_attack ?? 0} lbl={t("attacks_detected")}
          sub={`${m.incidents_certified ?? 0} ${t("certified")}`} color="#ff5c6c" />
        <Stat val={`${m.agents_online ?? 0}/${m.agents_total ?? 4}`}
          lbl={t("agents_online")} sub="Sentinel · Notary · Executor · DataSci"
          color="#2ecc71" />
        <Stat val={(data.pending || []).length} lbl={t("awaiting_approval")}
          sub={data.hitl?.hitl_enabled ? t("hitl_active") : t("hitl_inactive")}
          color="#f0a202" />
      </div>

      <div className="grid cols-2" style={{ marginTop: 16 }}>
        <div className="card">
          <h3>{t("verdict_split")}</h3>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={verdicts} dataKey="value" nameKey="name"
                innerRadius={55} outerRadius={90} paddingAngle={2}>
                {verdicts.map((v) => <Cell key={v.key} fill={COLORS[v.key]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: "#16223a", border: "none" }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h3>{t("verdict_counts")}</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={verdicts}>
              <XAxis dataKey="name" stroke="#8ea0bf" />
              <YAxis stroke="#8ea0bf" />
              <Tooltip contentStyle={{ background: "#16223a", border: "none" }} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {verdicts.map((v) => <Cell key={v.key} fill={COLORS[v.key]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h3>{t("recent_activity")}</h3>
        {(data.events || []).length === 0
          ? <div className="muted">{t("no_events")}</div>
          : (data.events || []).map((e, i) => (
            <div className="event-line" key={i}>
              <span className="t">
                {new Date(e.ts * 1000).toLocaleTimeString()}
              </span>
              <span>{e.message}</span>
            </div>
          ))}
      </div>
    </>
  );
}
