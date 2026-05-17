"use client";

import { useEffect, useState } from "react";
import { progressApi, type LearningDashboard, type DomainLevel } from "@/lib/api";
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer
} from "recharts";

// Mapa visual para niveles de dominio
const LEVEL_CONFIG: Record<DomainLevel, { label: string; color: string; bg: string }> = {
  novato:       { label: "Novato",       color: "#ef4444", bg: "#fef2f2" },
  intermedio:   { label: "Intermedio",   color: "#f59e0b", bg: "#fffbeb" },
  competente:   { label: "Competente",   color: "#3b82f6", bg: "#eff6ff" },
  experto:      { label: "Experto",      color: "#10b981", bg: "#ecfdf5" },
};

interface Props {
  moduleId: string;
}

export default function LearningDashboard({ moduleId }: Props) {
  const [data, setData] = useState<LearningDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    progressApi
      .dashboard(moduleId)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [moduleId]);

  if (loading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;
  if (!data) return null;

  const level = LEVEL_CONFIG[data.highest_level_achieved] || { label: data.highest_level_achieved, color: "#6b7280", bg: "#f3f4f6" };

  // Datos para radar de competencias
  const radarData = data.competency_breakdown.map((cp) => ({
    subject: cp.competency_name.split(" ").slice(0, 2).join(" "), // acortar nombre
    score: cp.domain_score,
    consistency: cp.consistency_score,
  }));

  // Datos de evolución temporal (última competencia con historial)
  const firstWithHistory = data.competency_breakdown.find(
    (cp) => cp.history.length > 1
  );
  const evolutionData = firstWithHistory?.history.slice(-8).map((h) => ({
    fecha: new Date(h.date).toLocaleDateString("es", { day: "numeric", month: "short" }),
    score: h.score,
    dominio: h.domain_score,
  })) || [];

  // Brecha metacognitiva: positivo = sobreconfianza
  const gap = data.avg_confidence_vs_score;
  const gapLabel = gap > 10
    ? "Sobreconfianza — crees saber más de lo que demuestras"
    : gap < -10
    ? "Infraconfianza — demuestras más de lo que crees"
    : "Buena calibración metacognitiva";
  const gapColor = Math.abs(gap) > 10 ? "#f59e0b" : "#10b981";

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", maxWidth: 900, margin: "0 auto", padding: "1.5rem" }}>
      {/* Encabezado */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0 }}>
          {data.module_title}
        </h1>
        <p style={{ color: "#6b7280", marginTop: 4, fontSize: "0.9rem" }}>
          Dashboard de aprendizaje real — más allá del % de avance
        </p>
      </div>

      {/* Métricas principales */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem", marginBottom: "1.5rem" }}>
        <MetricCard
          title="Nivel alcanzado"
          value={level.label}
          color={level.color}
          bg={level.bg}
          sub={`Dominio: ${data.overall_domain_score.toFixed(0)}/100`}
        />
        <MetricCard
          title="Evidencias"
          value={`${data.approved_evidences}/${data.total_evidences}`}
          color="#3b82f6"
          bg="#eff6ff"
          sub="aprobadas / totales"
        />
        <MetricCard
          title="Consistencia"
          value={`${data.consistency_index.toFixed(0)}%`}
          color="#8b5cf6"
          bg="#f5f3ff"
          sub="regularidad en el desempeño"
        />
        <MetricCard
          title="Competencias en experto"
          value={`${data.competencies_at_expert}`}
          color="#10b981"
          bg="#ecfdf5"
          sub={`de ${data.competency_breakdown.length} totales`}
        />
      </div>

      {/* Brecha metacognitiva */}
      <div style={{
        background: "#f9fafb",
        borderLeft: `4px solid ${gapColor}`,
        padding: "0.75rem 1rem",
        borderRadius: "0 8px 8px 0",
        marginBottom: "1.5rem",
        fontSize: "0.875rem",
      }}>
        <strong>Metacognición:</strong> {gapLabel}
        <span style={{ color: gapColor, marginLeft: 8, fontWeight: 600 }}>
          {gap > 0 ? "+" : ""}{gap.toFixed(1)} puntos de brecha
        </span>
      </div>

      {/* Gráficas */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginBottom: "1.5rem" }}>
        {/* Radar de competencias */}
        <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12, padding: "1rem" }}>
          <h3 style={{ fontSize: "0.9rem", fontWeight: 600, margin: "0 0 1rem" }}>
            Mapa de competencias
          </h3>
          <ResponsiveContainer width="100%" height={220}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
              <Radar name="Dominio" dataKey="score" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
              <Radar name="Consistencia" dataKey="consistency" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.15} />
              <Tooltip formatter={(v: number) => `${v.toFixed(0)}/100`} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Evolución temporal */}
        <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12, padding: "1rem" }}>
          <h3 style={{ fontSize: "0.9rem", fontWeight: 600, margin: "0 0 1rem" }}>
            Evolución del dominio
          </h3>
          {evolutionData.length > 1 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={evolutionData}>
                <XAxis dataKey="fecha" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Tooltip />
                <Line type="monotone" dataKey="score" stroke="#f59e0b" dot={false} name="Evidencia" />
                <Line type="monotone" dataKey="dominio" stroke="#3b82f6" strokeWidth={2} dot={false} name="Dominio acum." />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState message="Necesitás al menos 2 evidencias para ver la evolución" />
          )}
        </div>
      </div>

      {/* Detalle por competencia */}
      <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12, padding: "1rem" }}>
        <h3 style={{ fontSize: "0.9rem", fontWeight: 600, margin: "0 0 1rem" }}>
          Detalle por competencia
        </h3>
        {data.competency_breakdown.map((cp) => {
          const lvl = LEVEL_CONFIG[cp.current_level] || { label: cp.current_level, color: "#6b7280", bg: "#f3f4f6" };
          return (
            <div key={cp.competency_id} style={{ marginBottom: "1rem", paddingBottom: "1rem", borderBottom: "1px solid #f3f4f6" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                <span style={{ fontSize: "0.875rem", fontWeight: 500 }}>{cp.competency_name}</span>
                <span style={{
                  padding: "2px 10px",
                  borderRadius: 20,
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  background: lvl.bg,
                  color: lvl.color,
                }}>
                  {lvl.label}
                </span>
              </div>
              <ProgressBar value={cp.domain_score} color={lvl.color} />
              <div style={{ display: "flex", gap: "1rem", marginTop: 4, fontSize: "0.75rem", color: "#9ca3af" }}>
                <span>Dominio: {cp.domain_score.toFixed(0)}/100</span>
                <span>Consistencia: {cp.consistency_score.toFixed(0)}%</span>
                <span>Evidencias: {cp.evidence_count}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Subcomponentes ─────────────────────────────────────────────────────────

function MetricCard({ title, value, color, bg, sub }: {
  title: string; value: string; color: string; bg: string; sub: string;
}) {
  return (
    <div style={{ background: bg, borderRadius: 12, padding: "1rem" }}>
      <p style={{ fontSize: "0.75rem", color: "#6b7280", margin: "0 0 4px" }}>{title}</p>
      <p style={{ fontSize: "1.5rem", fontWeight: 700, color, margin: "0 0 2px" }}>{value}</p>
      <p style={{ fontSize: "0.7rem", color: "#9ca3af", margin: 0 }}>{sub}</p>
    </div>
  );
}

function ProgressBar({ value, color }: { value: number; color: string }) {
  return (
    <div style={{ height: 6, background: "#f3f4f6", borderRadius: 3, overflow: "hidden" }}>
      <div style={{
        height: "100%",
        width: `${Math.min(value, 100)}%`,
        background: color,
        borderRadius: 3,
        transition: "width 0.6s ease",
      }} />
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div style={{ padding: "1.5rem" }}>
      {[1, 2, 3].map((i) => (
        <div key={i} style={{
          height: 80, background: "#f3f4f6",
          borderRadius: 12, marginBottom: "1rem",
          animation: "pulse 1.5s infinite"
        }} />
      ))}
    </div>
  );
}

function ErrorMessage({ message }: { message: string }) {
  return (
    <div style={{
      background: "#fef2f2", border: "1px solid #fecaca",
      borderRadius: 8, padding: "1rem", color: "#dc2626"
    }}>
      Error: {message}
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div style={{ textAlign: "center", padding: "2rem", color: "#9ca3af", fontSize: "0.875rem" }}>
      {message}
    </div>
  );
}
