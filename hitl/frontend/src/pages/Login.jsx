import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { useTheme } from "../theme.jsx";
import { useI18n } from "../i18n.jsx";

export default function Login() {
  const { login } = useAuth();
  const { theme, toggle } = useTheme();
  const { t, lang, cycleLang } = useI18n();
  const nav = useNavigate();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setErr("");
    try {
      await login(username, password);
      nav("/");
    } catch (ex) {
      setErr(ex.message || "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <div style={{ position: "fixed", top: 18, insetInlineEnd: 18,
        display: "flex", gap: 8 }}>
        <button className="ctrl-btn" onClick={cycleLang}>
          <span className="ico">🌐</span>{lang.toUpperCase()}</button>
        <button className="ctrl-btn" onClick={toggle}>
          <span className="ico">{theme === "dark" ? "☀" : "🌙"}</span></button>
      </div>
      <form className="login-card" onSubmit={submit}>
        <h1>BAg-IDS</h1>
        <div className="sub">{t("login_sub")}</div>
        <div className="field">
          <label>{t("username")}</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)}
            autoFocus />
        </div>
        <div className="field">
          <label>{t("password")}</label>
          <input type="password" value={password}
            onChange={(e) => setPassword(e.target.value)} />
        </div>
        <button className="primary" style={{ width: "100%" }} disabled={busy}>
          {busy ? t("login_busy") : t("login_btn")}
        </button>
        {err && <div className="err">{err}</div>}
        <div className="hint">
          {t("demo_accounts")}<br />
          admin / admin123 · analyste / analyste123 · lecteur / lecteur123
        </div>
      </form>
    </div>
  );
}
