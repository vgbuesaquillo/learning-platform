"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError("Completa todos los campos");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={container}>
      <form onSubmit={handleSubmit} style={card}>
        <h1 style={title}>Iniciar sesión</h1>

        <label style={label}>Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="tu@email.com"
          style={input}
        />

        <label style={label}>Contraseña</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          style={input}
        />

        {error && <div style={errorBox}>{error}</div>}

        <button type="submit" disabled={submitting} style={primaryBtn}>
          {submitting ? "Ingresando..." : "Ingresar"}
        </button>

        <p style={{ fontSize: "0.875rem", color: "#6b7280", textAlign: "center", marginTop: "1rem" }}>
          ¿No tenés cuenta?{" "}
          <Link href="/register" style={{ color: "#1d4ed8", fontWeight: 600 }}>
            Registrate
          </Link>
        </p>
      </form>
    </div>
  );
}

const container: React.CSSProperties = {
  display: "flex", justifyContent: "center", alignItems: "center",
  minHeight: "100vh", padding: "1rem",
};

const card: React.CSSProperties = {
  background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12,
  padding: "2rem", width: "100%", maxWidth: 400,
};

const title: React.CSSProperties = {
  fontSize: "1.25rem", fontWeight: 700, margin: "0 0 1.5rem", textAlign: "center",
};

const label: React.CSSProperties = {
  display: "block", fontSize: "0.875rem", fontWeight: 500,
  color: "#374151", marginBottom: 4,
};

const input: React.CSSProperties = {
  width: "100%", padding: "0.625rem 0.75rem", borderRadius: 8,
  border: "1px solid #d1d5db", fontSize: "0.875rem",
  boxSizing: "border-box", marginBottom: "1rem", outline: "none",
};

const errorBox: React.CSSProperties = {
  background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8,
  padding: "0.75rem", color: "#dc2626", fontSize: "0.875rem", marginBottom: "1rem",
};

const primaryBtn: React.CSSProperties = {
  width: "100%", padding: "0.625rem", background: "#1d4ed8", color: "#fff",
  border: "none", borderRadius: 8, cursor: "pointer",
  fontSize: "0.875rem", fontWeight: 600,
};
