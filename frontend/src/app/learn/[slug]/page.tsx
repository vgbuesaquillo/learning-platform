"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { themesApi, itemsApi, LearningItem_, Theme_ } from "@/lib/api";

const NAME_TO_SLUG: Record<string, string> = {
  "Inglés comunicativo": "english",
  "Metodología de investigación": "research",
  "Programación": "programming",
  "Deportes y salud": "sports",
};

const SLUG_TO_NAME: Record<string, string> = {};
for (const [k, v] of Object.entries(NAME_TO_SLUG)) SLUG_TO_NAME[v] = k;

interface LearnPageProps {
  params: { slug: string };
}

const i18n = (slug: string) => {
  const isEn = slug === "english";
  return {
    notFoundTitle: isEn ? "Topic not found" : "Eje no encontrado",
    notFoundBack: isEn ? "Back to home" : "Volver al inicio",
    loading: isEn ? "Loading content..." : "Cargando contenido...",
    doneTitle: isEn ? "You completed all items!" : "¡Completaste todos los ítems!",
    doneDesc: isEn ? "Keep practicing to reach expert level." : "Seguí practicando para alcanzar el nivel experto.",
    backHome: isEn ? "Back to home" : "Volver al inicio",
    reviewAgain: isEn ? "Review again" : "Repasar de nuevo",
    emptyTitle: isEn ? "No content available" : "Sin contenido disponible",
    difficulty: isEn ? "difficulty" : "dificultad",
    knowIt: isEn ? "\u2713 I know it" : "\u2713 Lo sé",
    dontKnow: isEn ? "\u2717 I don\u2019t know" : "\u2717 No lo sé",
    saving: isEn ? "Saving..." : "Guardando...",
    finish: isEn ? "\u2713 Finish" : "\u2713 Finalizar",
    backTo: isEn ? "Back to" : "Volver a",
  };
};

export default function LearnPage({ params }: LearnPageProps) {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [theme, setTheme] = useState<Theme_ | null>(null);
  const [items, setItems] = useState<LearningItem_[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [done, setDone] = useState(false);

  const themeName = SLUG_TO_NAME[params.slug];
  const txt = i18n(params.slug);

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [user, authLoading, router]);

  useEffect(() => {
    if (!user || !themeName) return;
    setLoading(true);
    Promise.all([
      themesApi.list(),
      itemsApi.list(),
    ]).then(([allThemes, allItems]) => {
      const t = allThemes.find((th) => th.name === themeName);
      if (!t) { setLoading(false); return; }
      setTheme(t);
      const filtered = allItems.filter((i) => i.theme_id === t.id);
      setItems(filtered);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [user, themeName]);

  const handleAdvance = useCallback(async (weight: number) => {
    const item = items[currentIdx];
    if (!item || saving) return;
    setSaving(true);
    try {
      await itemsApi.view(item.id, { weight });
    } catch { /* ignore */ }
    setSaving(false);
    if (currentIdx + 1 < items.length) {
      setCurrentIdx((i) => i + 1);
    } else {
      setDone(true);
    }
  }, [items, currentIdx, saving]);

  if (authLoading || !user) return null;

  if (!themeName) {
    return (
      <div style={container}>
        <h1 style={{ fontSize: "1.25rem" }}>{txt.notFoundTitle}</h1>
        <Link href="/" style={{ color: "#1d4ed8" }}>{txt.notFoundBack}</Link>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={container}>
        <p style={{ color: "#9ca3af" }}>{txt.loading}</p>
      </div>
    );
  }

  if (done) {
    return (
      <div style={container}>
        <div style={card}>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#22c55e", marginBottom: 8 }}>
            {txt.doneTitle}
          </h2>
          <p style={{ color: "#6b7280", marginBottom: "1rem" }}>
            {txt.doneDesc}
          </p>
          <div style={{ display: "flex", gap: 8 }}>
            <Link href="/" style={btnPrimary}>{txt.backHome}</Link>
            <button onClick={() => { setCurrentIdx(0); setDone(false); }} style={btnSecondary}>
              {txt.reviewAgain}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!theme || items.length === 0) {
    return (
      <div style={container}>
        <h1 style={{ fontSize: "1.25rem" }}>{txt.emptyTitle}</h1>
        <Link href="/" style={{ color: "#1d4ed8" }}>{txt.backHome}</Link>
      </div>
    );
  }

  const item = items[currentIdx];
  const category = item.item_metadata?.category || "";
  const difficulty = item.item_metadata?.difficulty || 1;
  const isLast = currentIdx + 1 >= items.length;

  return (
    <div style={container}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <Link href="/" style={{ color: "#6b7280", fontSize: "0.875rem", textDecoration: "none" }}>
          &larr; {txt.backTo} {theme.name}
        </Link>
        <span style={{ fontSize: "0.75rem", color: "#9ca3af" }}>
          {currentIdx + 1} / {items.length}
        </span>
      </div>

      <div style={{ marginBottom: "1.5rem" }}>
        <div style={{ height: 6, background: "#e5e7eb", borderRadius: 3, overflow: "hidden" }}>
          <div style={{
            height: "100%", width: `${((currentIdx + 1) / items.length) * 100}%`,
            background: "#3b82f6", borderRadius: 3, transition: "width 0.3s",
          }} />
        </div>
      </div>

      <div style={card}>
        {category && (
          <span style={{
            fontSize: "0.7rem", fontWeight: 600, color: "#6b7280",
            textTransform: "uppercase", letterSpacing: "0.05em",
          }}>
            {category}
          </span>
        )}

        <h2 style={{
          fontSize: "1.5rem", fontWeight: 700, marginTop: 8, marginBottom: 4,
          color: "#111827",
        }}>
          {item.content}
        </h2>

        <p style={{ fontSize: "0.875rem", color: "#6b7280" }}>
          {item.item_type.replace("_", " ")}
          {difficulty > 1 && ` · ${txt.difficulty} ${difficulty}`}
        </p>
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: "1rem" }}>
        {!isLast && (
          <button
            onClick={() => handleAdvance(0)}
            disabled={saving}
            style={{
              ...btnSecondary, flex: 1, textAlign: "center",
              opacity: saving ? 0.6 : 1,
            }}
          >
            {saving ? txt.saving : txt.dontKnow}
          </button>
        )}
        <button
          onClick={() => handleAdvance(isLast ? 0.5 : 0.5)}
          disabled={saving}
          style={{
            ...(isLast ? btnPrimary : btnPrimary), flex: 1, textAlign: "center",
            opacity: saving ? 0.6 : 1,
          }}
        >
          {saving ? txt.saving : isLast ? txt.finish : txt.knowIt}
        </button>
      </div>
    </div>
  );
}

const container: React.CSSProperties = {
  maxWidth: 600, margin: "2rem auto", padding: "0 1.5rem",
};

const card: React.CSSProperties = {
  background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12,
  padding: "1.5rem",
};

const btnPrimary: React.CSSProperties = {
  display: "inline-block", padding: "0.75rem 1.5rem", background: "#1d4ed8", color: "#fff",
  borderRadius: 8, fontSize: "1rem", fontWeight: 600, border: "none", cursor: "pointer",
  textDecoration: "none",
};

const btnSecondary: React.CSSProperties = {
  display: "inline-block", padding: "0.75rem 1.5rem", background: "#fff", color: "#374151",
  borderRadius: 8, fontSize: "1rem", fontWeight: 600, border: "1px solid #d1d5db",
  cursor: "pointer", textDecoration: "none",
};
