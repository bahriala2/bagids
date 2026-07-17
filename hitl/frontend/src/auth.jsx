import { createContext, useContext, useState } from "react";
import { api, storeSession, clearSession, getStoredUser } from "./api";

const AuthCtx = createContext(null);

// Hiérarchie des rôles pour l'affichage conditionnel côté UI.
const RANK = { reader: 0, analyst: 1, admin: 2 };

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getStoredUser());

  async function login(username, password) {
    const res = await api.login(username, password);
    storeSession(res.access_token, res.user);
    setUser(res.user);
    return res.user;
  }
  function logout() {
    clearSession();
    setUser(null);
  }
  const can = (minRole) => user && RANK[user.role] >= RANK[minRole];

  return (
    <AuthCtx.Provider value={{ user, login, logout, can }}>
      {children}
    </AuthCtx.Provider>
  );
}

export const useAuth = () => useContext(AuthCtx);
