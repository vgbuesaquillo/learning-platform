"use client";

import EvidenceForm from "@/components/learning/EvidenceForm";

// ID de actividad demo (tras ejecutar seed)
const DEMO_ACTIVITY_ID = "00000000-0000-0000-0000-000000000001";

export default function EvidencePage() {
  return (
    <div style={{ maxWidth: 700, margin: "2rem auto", padding: "0 1.5rem" }}>
      <h1 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "1.5rem" }}>
        Registrar evidencia de aprendizaje
      </h1>
      <EvidenceForm
        activityId={DEMO_ACTIVITY_ID}
        activityTitle="Mapa de literatura: estado del arte inicial"
        onSuccess={(ev) => console.log("Evidencia creada:", ev.id)}
      />
    </div>
  );
}
