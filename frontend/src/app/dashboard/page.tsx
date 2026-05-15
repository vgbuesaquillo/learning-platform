"use client";

import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import LearningDashboard from "@/components/dashboard/LearningDashboard";

const MODULE_ID = "356c96e0-fcd3-4e84-b191-eecd333231d6";

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  if (loading) return null;
  if (!user) {
    router.push("/login");
    return null;
  }

  return <LearningDashboard moduleId={MODULE_ID} />;
}
