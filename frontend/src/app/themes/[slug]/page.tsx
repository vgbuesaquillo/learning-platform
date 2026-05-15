"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface ThemePageProps {
  params: { slug: string };
}

const THEME_MAP: Record<string, { name: string; desc: string }> = {
  english: { name: "Inglés", desc: "Vocabulario, frases, gramática y más" },
  research: { name: "Investigación", desc: "Metodología de investigación científica" },
  programming: { name: "Programación", desc: "Fundamentos y práctica de programación" },
};

export default function ThemePage({ params }: ThemePageProps) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const theme = THEME_MAP[params.slug];

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [user, loading, router]);

  if (loading || !user) return null;
  if (!theme) {
    return (
      <div style={container}>
        <h1 style={{ fontSize: "1.25rem" }}>Tema no encontrado</h1>
        <Link href="/" style={{ color: "#1d4ed8" }}>Volver al inicio</Link>
      </div>
    );
  }

  return (
    <div style={container}>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 4 }}>{theme.name}</h1>
      <p style={{ color: "#6b7280", marginBottom: "1.5rem" }}>{theme.desc}</p>
      <div style={card}>
        <p style={{ fontSize: "0.875rem", color: "#374151" }}>
          Contenido de aprendizaje próximo. Seleccioná una opción:
        </p>
        <div style={{ display: "flex", gap: 8, marginTop: "1rem", flexWrap: "wrap" }}>
          <Link href="/evidence" style={btn}>Registrar evidencia</Link>
          <Link href="/dashboard" style={{ ...btn, background: "#fff", color: "#374151", border: "1px solid #d1d5db" }}>
            Ver dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}

const container: React.CSSProperties = {
  maxWidth: 700, margin: "2rem auto", padding: "0 1.5rem",
};

const card: React.CSSProperties = {
  background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12,
  padding: "1.5rem",
};

const btn: React.CSSProperties = {
  padding: "0.5rem 1rem", background: "#1d4ed8", color: "#fff",
  borderRadius: 8, fontSize: "0.875rem", fontWeight: 600,
  textDecoration: "none",
};
