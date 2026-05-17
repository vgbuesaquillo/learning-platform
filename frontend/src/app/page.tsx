"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { progressApi, ThemeProgressSummary } from "@/lib/api";

const NAME_TO_SLUG: Record<string, string> = {
  "Inglés comunicativo": "english",
  "Metodología de investigación": "research",
  "Programación": "programming",
  "Deportes y salud": "sports",
};

const LEVEL_COLORS: Record<string, string> = {
  novato: "#ef4444",
  intermedio: "#f59e0b",
  competente: "#3b82f6",
  experto: "#22c55e",
};

export default function HomePage() {
  const { user } = useAuth();
  const [themes, setThemes] = useState<ThemeProgressSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      progressApi.themesProgress()
        .then((data) => setThemes(data.themes))
        .catch(() => {})
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [user]);

  return (
    <div style={{ maxWidth: 700, margin: "2rem auto", padding: "0 1.5rem" }}>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 4 }}>
        LearnPath
      </h1>
      <p style={{ color: "#6b7280", marginBottom: "1.5rem" }}>
        {user ? "Elegí un eje para empezar a aprender:" : "Iniciá sesión para empezar a aprender"}
      </p>

      {!user ? (
        <div style={{ display: "grid", gap: "1rem" }}>
          {["Inglés comunicativo", "Metodología de investigación", "Programación", "Deportes y salud"].map((name) => (
            <Link key={name} href="/login" style={themeCard}>
              <strong style={{ fontSize: "1rem", color: "#1d4ed8" }}>{name}</strong>
            </Link>
          ))}
        </div>
      ) : loading ? (
        <p style={{ color: "#9ca3af" }}>Cargando...</p>
      ) : (
        <div style={{ display: "grid", gap: "1rem" }}>
          {themes.map((t) => {
            const slug = NAME_TO_SLUG[t.theme_name] || t.theme_name.toLowerCase().replace(/\s+/g, "-");
            const pct = Math.round(t.overall_mastery * 100);
            const color = LEVEL_COLORS[t.level] || "#6b7280";
            return (
              <Link key={t.theme_id} href={`/learn/${slug}`} style={themeCard}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <strong style={{ fontSize: "1rem", color: "#1d4ed8" }}>{t.theme_name}</strong>
                  <span style={{
                    fontSize: "0.75rem", fontWeight: 600, color: "#fff",
                    background: color, padding: "2px 10px", borderRadius: 999,
                  }}>
                    {t.level}
                  </span>
                </div>
                <div style={{ marginTop: 8 }}>
                  <div style={{ height: 8, background: "#e5e7eb", borderRadius: 4, overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${pct}%`, background: color, borderRadius: 4, transition: "width 0.3s" }} />
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginTop: 2 }}>
                    <span style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                      {t.completed_items}/{t.total_items} ítems
                    </span>
                    <span style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                      {pct}%
                    </span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

const themeCard: React.CSSProperties = {
  display: "flex", flexDirection: "column", gap: 4,
  background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12,
  padding: "1rem 1.25rem", textDecoration: "none",
  transition: "box-shadow 0.15s",
};
