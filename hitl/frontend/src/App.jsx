import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import Layout from "./components/Layout.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Incidents from "./pages/Incidents.jsx";
import Investigations from "./pages/Investigations.jsx";
import Approvals from "./pages/Approvals.jsx";
import Ledger from "./pages/Ledger.jsx";
import Governance from "./pages/Governance.jsx";
import AttackTest from "./pages/AttackTest.jsx";

function Protected({ children }) {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={<Protected><Layout /></Protected>}
      >
        <Route index element={<Dashboard />} />
        <Route path="incidents" element={<Incidents />} />
        <Route path="investigations" element={<Investigations />} />
        <Route path="approvals" element={<Approvals />} />
        <Route path="attack-test" element={<AttackTest />} />
        <Route path="ledger" element={<Ledger />} />
        <Route path="governance" element={<Governance />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
