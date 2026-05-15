"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

const THEMES = [
  { slug: "english", name: "Inglés", desc: "Vocabulario, frases y gramática" },
  { slug: "research", name: "Investigación", desc: "Metodología de investigación científica" },
  { slug: "programming", name: "Programación", desc: "Fundamentos de programación" },
];

export default function HomePage() {
  const { user } = useAuth();

  return (
    <div style={{ maxWidth: 700, margin: "2rem auto", padding: "0 1.5rem" }}>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 4 }}>
        LearnPath
      </h1>
      <p style={{ color: "#6b7280", marginBottom: "1.5rem" }}>
        {user ? "Elegí un tema para empezar a aprender:" : "Iniciá sesión para empezar a aprender"}
      </p>
      <div style={{ display: "grid", gap: "1rem" }}>
        {THEMES.map((t) => (
          <Link
            key={t.slug}
            href={user ? `/themes/${t.slug}` : "/login"}
            style={themeCard}
          >
            <strong style={{ fontSize: "1rem", color: "#1d4ed8" }}>{t.name}</strong>
            <span style={{ fontSize: "0.8rem", color: "#6b7280" }}>{t.desc}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}

const themeCard: React.CSSProperties = {
  display: "flex", flexDirection: "column", gap: 4,
  background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12,
  padding: "1rem 1.25rem", textDecoration: "none",
  transition: "box-shadow 0.15s",
};

