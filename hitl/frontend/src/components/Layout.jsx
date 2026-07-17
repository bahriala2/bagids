import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { useAuth } from "../auth.jsx";
import { useTheme } from "../theme.jsx";
import { useI18n } from "../i18n.jsx";

const NAV = [
  { to: "/", ico: "▣", key: "nav_dashboard", end: true, role: "reader" },
  { to: "/incidents", ico: "⚠", key: "nav_incidents", role: "reader" },
  { to: "/investigations", ico: "🔎", key: "nav_investigations", role: "reader" },
  { to: "/attack-test", ico: "🎯", key: "nav_attacktest", role: "analyst" },
  { to: "/approvals", ico: "✋", key: "nav_approvals", role: "reader" },
  { to: "/ledger", ico: "⛓", key: "nav_ledger", role: "reader" },
  { to: "/governance", ico: "⚙", key: "nav_governance", role: "admin" },
];

const TITLE_KEY = {
  "/": "title_dashboard", "/incidents": "title_incidents",
  "/investigations": "title_investigations",
  "/attack-test": "title_attacktest",
  "/approvals": "title_approvals", "/ledger": "title_ledger",
  "/governance": "title_governance",
};

export default function Layout() {
  const { user, logout, can } = useAuth();
  const { theme, toggle } = useTheme();
  const { t, lang, cycleLang, nameOf } = useI18n();
  const loc = useLocation();
  const [hitl, setHitl] = useState(null);

  useEffect(() => {
    let alive = true;
    const poll = async () => {
      try {
        const r = await fetch("/api/health");
        const d = await r.json();
        if (alive) setHitl(d.hitl_enabled);
      } catch { /* backend indisponible */ }
    };
    poll();
    const id = setInterval(poll, 4000);
    return () => { alive = false; clearInterval(id); };
  }, []);

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <h1>BAg-IDS</h1>
          <span className="tag">{t("brand_tag")}</span>
        </div>
        <nav className="nav">
          {NAV.filter((n) => can(n.role)).map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end}
              className={({ isActive }) => (isActive ? "active" : "")}>
              <span className="ico">{n.ico}</span> {t(n.key)}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div>{user.full_name}</div>
          <div className="muted" style={{ textTransform: "capitalize" }}>
            {t("role")} : {user.role}
          </div>
          <button style={{ marginTop: 10, width: "100%" }} onClick={logout}>
            {t("logout")}
          </button>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div className="title">{t(TITLE_KEY[loc.pathname] || "title_dashboard")}</div>
          <div className="row">
            {hitl === null ? null : (
              <span className={`pill ${hitl ? "on" : "off"}`}>
                <span className="dot" />
                {hitl ? t("hitl_on") : t("hitl_off")}
              </span>
            )}
            <button className="ctrl-btn" onClick={cycleLang}
              title={t("language")}>
              <span className="ico">🌐</span>{lang.toUpperCase()}
            </button>
            <button className="ctrl-btn" onClick={toggle} title={t("theme")}>
              <span className="ico">{theme === "dark" ? "☀" : "🌙"}</span>
            </button>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
