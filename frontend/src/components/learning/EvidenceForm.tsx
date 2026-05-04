"use client";

import { useState } from "react";
import { evidenceApi, type Evidence } from "@/lib/api";

interface Props {
  activityId: string;
  activityTitle: string;
  onSuccess?: (evidence: Evidence) => void;
}

const CONFIDENCE_LABELS = ["", "Muy bajo", "Bajo", "Medio", "Alto", "Muy alto"];

export default function EvidenceForm({ activityId, activityTitle, onSuccess }: Props) {
  const [content, setContent] = useState("");
  const [reflection, setReflection] = useState("");
  const [confidence, setConfidence] = useState(3);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSave = async (submit = false) => {
    if (!content.trim()) {
      setError("El contenido de la evidencia es obligatorio");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const ev = await evidenceApi.create({
        activity_id: activityId,
        content,
        reflection: reflection || undefined,
        confidence_level: confidence,
      });
      if (submit) {
        await evidenceApi.submit(ev.id);
      }
      setSuccess(true);
      onSuccess?.(ev);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al guardar");
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <div style={{
        background: "#ecfdf5", border: "1px solid #6ee7b7",
        borderRadius: 12, padding: "1.5rem", textAlign: "center"
      }}>
        <div style={{ fontSize: "2rem", marginBottom: 8 }}>✓</div>
        <p style={{ color: "#059669", fontWeight: 600, margin: 0 }}>
          Evidencia registrada exitosamente
        </p>
        <button
          onClick={() => { setSuccess(false); setContent(""); setReflection(""); }}
          style={{ marginTop: 12, color: "#6b7280", background: "none", border: "none", cursor: "pointer", fontSize: "0.875rem" }}
        >
          Registrar otra evidencia
        </button>
      </div>
    );
  }

  return (
    <div style={{
      background: "#fff",
      border: "1px solid #e5e7eb",
      borderRadius: 12,
      padding: "1.5rem",
      fontFamily: "system-ui, sans-serif",
    }}>
      <h2 style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 1.25rem" }}>
        Registrar evidencia: {activityTitle}
      </h2>

      {/* Contenido principal */}
      <label style={labelStyle}>
        Tu trabajo / respuesta
        <span style={{ color: "#ef4444" }}> *</span>
      </label>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Describe tu trabajo, reflexiones, análisis o resultados..."
        rows={6}
        style={textareaStyle}
      />

      {/* Reflexión metacognitiva */}
      <label style={{ ...labelStyle, marginTop: "1rem" }}>
        Reflexión metacognitiva
        <span style={{ color: "#9ca3af", fontSize: "0.75rem", marginLeft: 6 }}>
          ¿Qué aprendiste? ¿Qué te costó más? ¿Cómo cambió tu comprensión?
        </span>
      </label>
      <textarea
        value={reflection}
        onChange={(e) => setReflection(e.target.value)}
        placeholder="Reflexiona sobre tu proceso de aprendizaje..."
        rows={3}
        style={textareaStyle}
      />

      {/* Nivel de confianza */}
      <label style={{ ...labelStyle, marginTop: "1rem" }}>
        ¿Qué tan seguro/a te sentís con este tema?
      </label>
      <div style={{ display: "flex", gap: 8, marginTop: 6, flexWrap: "wrap" }}>
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => setConfidence(n)}
            style={{
              padding: "6px 14px",
              borderRadius: 20,
              border: "1.5px solid",
              borderColor: confidence === n ? "#3b82f6" : "#e5e7eb",
              background: confidence === n ? "#eff6ff" : "#fff",
              color: confidence === n ? "#1d4ed8" : "#6b7280",
              cursor: "pointer",
              fontSize: "0.8rem",
              fontWeight: confidence === n ? 600 : 400,
              transition: "all 0.15s",
            }}
          >
            {n} — {CONFIDENCE_LABELS[n]}
          </button>
        ))}
      </div>
      <p style={{ fontSize: "0.75rem", color: "#9ca3af", marginTop: 4 }}>
        Este dato permite calcular tu brecha metacognitiva (confianza vs desempeño real)
      </p>

      {/* Error */}
      {error && (
        <div style={{
          background: "#fef2f2", border: "1px solid #fecaca",
          borderRadius: 8, padding: "0.75rem", color: "#dc2626",
          fontSize: "0.875rem", marginTop: "1rem"
        }}>
          {error}
        </div>
      )}

      {/* Acciones */}
      <div style={{ display: "flex", gap: 8, marginTop: "1.25rem" }}>
        <button
          type="button"
          onClick={() => handleSave(false)}
          disabled={submitting}
          style={secondaryBtnStyle}
        >
          Guardar borrador
        </button>
        <button
          type="button"
          onClick={() => handleSave(true)}
          disabled={submitting}
          style={primaryBtnStyle}
        >
          {submitting ? "Enviando..." : "Enviar para revisión"}
        </button>
      </div>
    </div>
  );
}

const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: "0.875rem",
  fontWeight: 500,
  color: "#374151",
  marginBottom: 4,
};

const textareaStyle: React.CSSProperties = {
  width: "100%",
  padding: "0.625rem 0.75rem",
  borderRadius: 8,
  border: "1px solid #d1d5db",
  fontSize: "0.875rem",
  lineHeight: 1.6,
  resize: "vertical",
  fontFamily: "inherit",
  boxSizing: "border-box",
  outline: "none",
};

const primaryBtnStyle: React.CSSProperties = {
  padding: "0.5rem 1.25rem",
  background: "#1d4ed8",
  color: "#fff",
  border: "none",
  borderRadius: 8,
  cursor: "pointer",
  fontSize: "0.875rem",
  fontWeight: 600,
};

const secondaryBtnStyle: React.CSSProperties = {
  padding: "0.5rem 1.25rem",
  background: "#fff",
  color: "#374151",
  border: "1px solid #d1d5db",
  borderRadius: 8,
  cursor: "pointer",
  fontSize: "0.875rem",
  fontWeight: 500,
};
