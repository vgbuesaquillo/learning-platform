import type { Metadata } from "next";
import { AuthProvider } from "@/lib/auth-context";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "LearnPath — Aprendizaje con progreso real",
  description: "Plataforma educativa que mide comprensión, aplicación y metacognición",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body style={{
        margin: 0,
        fontFamily: "system-ui, -apple-system, sans-serif",
        background: "#f9fafb",
        minHeight: "100vh",
      }}>
        <AuthProvider>
          <Navbar />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
