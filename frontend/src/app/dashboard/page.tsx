"use client";

import LearningDashboard from "@/components/dashboard/LearningDashboard";

// ID del módulo demo (se obtiene del seed)
const DEMO_MODULE_ID = ""; // Reemplazar con UUID real del módulo tras seed

export default function DashboardPage() {
  if (!DEMO_MODULE_ID) {
    return (
      <div style={{ padding: "2rem", fontFamily: "system-ui, sans-serif" }}>
        <h2 style={{ marginBottom: "1rem" }}>Dashboard de Progreso Real</h2>
        <div style={{
          background: "#fefce8",
          border: "1px solid #fde047",
          borderRadius: 8,
          padding: "1rem",
          fontSize: "0.875rem",
        }}>
          <strong>Setup inicial:</strong>
          <ol style={{ margin: "0.5rem 0 0 1.2rem", lineHeight: 2 }}>
            <li>Ejecutar seed: <code>docker compose exec backend python scripts/seed.py</code></li>
            <li>Registrarse en <code>/api/v1/auth/register</code></li>
            <li>Obtener el UUID del módulo desde <code>/api/v1/docs</code></li>
            <li>Reemplazar <code>DEMO_MODULE_ID</code> en esta página</li>
          </ol>
        </div>
      </div>
    );
  }

  return <LearningDashboard moduleId={DEMO_MODULE_ID} />;
}
