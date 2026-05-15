"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

export default function Navbar() {
  const { user, loading, logout } = useAuth();

  return (
    <nav style={nav}>
      <div style={inner}>
        <Link href="/" style={logo}>LearnPath</Link>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <Link href="/evidence" style={link}>Evidencia</Link>
          <Link href="/dashboard" style={link}>Dashboard</Link>
          {loading ? null : user ? (
            <>
              <span style={{ fontSize: "0.8rem", color: "#6b7280" }}>
                {user.full_name}
              </span>
              <button onClick={logout} style={logoutBtn}>Salir</button>
            </>
          ) : (
            <>
              <Link href="/login" style={link}>Ingresar</Link>
              <Link href="/register" style={registerBtn}>Registrarse</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

const nav: React.CSSProperties = {
  background: "#fff", borderBottom: "1px solid #e5e7eb",
  position: "sticky", top: 0, zIndex: 50,
};

const inner: React.CSSProperties = {
  display: "flex", justifyContent: "space-between", alignItems: "center",
  maxWidth: 960, margin: "0 auto", padding: "0.75rem 1.5rem",
};

const logo: React.CSSProperties = {
  fontWeight: 700, fontSize: "1.1rem", color: "#1d4ed8",
  textDecoration: "none",
};

const link: React.CSSProperties = {
  fontSize: "0.875rem", color: "#374151", textDecoration: "none",
  fontWeight: 500,
};

const registerBtn: React.CSSProperties = {
  fontSize: "0.875rem", fontWeight: 600, color: "#fff",
  background: "#1d4ed8", padding: "0.375rem 0.875rem", borderRadius: 8,
  textDecoration: "none",
};

const logoutBtn: React.CSSProperties = {
  fontSize: "0.8rem", color: "#dc2626", background: "none",
  border: "1px solid #fecaca", borderRadius: 6, padding: "0.25rem 0.625rem",
  cursor: "pointer",
};
