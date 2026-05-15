"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import EvidenceForm from "@/components/learning/EvidenceForm";

const MODULE_ID = "356c96e0-fcd3-4e84-b191-eecd333231d6";

interface Activity {
  id: string;
  title: string;
  description?: string;
}

export default function EvidencePage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [activities, setActivities] = useState<Activity[]>([]);
  const [selectedActivity, setSelectedActivity] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    if (!user) { router.push("/login"); return; }

    fetch(`http://localhost:9000/api/v1/activities/module/${MODULE_ID}`)
      .then((r) => r.json())
      .then((data) => {
        setActivities(data);
        if (data.length > 0) setSelectedActivity(data[0].id);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user, authLoading, router]);

  if (authLoading || loading) return null;
  if (!user) return null;

  const currentActivity = activities.find((a) => a.id === selectedActivity);

  return (
    <div style={{ maxWidth: 700, margin: "2rem auto", padding: "0 1.5rem" }}>
      <h1 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "1.5rem" }}>
        Registrar evidencia de aprendizaje
      </h1>

      {activities.length > 0 && (
        <div style={{ marginBottom: "1rem" }}>
          <label style={{ fontSize: "0.875rem", fontWeight: 500, display: "block", marginBottom: 4 }}>
            Actividad
          </label>
          <select
            value={selectedActivity}
            onChange={(e) => setSelectedActivity(e.target.value)}
            style={{
              width: "100%", padding: "0.5rem", borderRadius: 6,
              border: "1px solid #d1d5db", fontSize: "0.875rem",
            }}
          >
            {activities.map((a) => (
              <option key={a.id} value={a.id}>{a.title}</option>
            ))}
          </select>
        </div>
      )}

      {currentActivity && (
        <EvidenceForm
          activityId={selectedActivity}
          activityTitle={currentActivity.title}
          onSuccess={(ev) => console.log("Evidencia creada:", ev.id)}
        />
      )}
    </div>
  );
}
