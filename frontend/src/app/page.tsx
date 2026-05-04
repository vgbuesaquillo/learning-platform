"use client";

import Link from "next/link";

export default function HomePage() {
  return (
    <div style={{ padding: 20 }}>
      <h1>LearnPath MVP</h1>
      <p>Seleccione un tema para empezar:</p>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        <li style={{ marginBottom: 10 }}>
          <Link href="/themes/english" style={{ textDecoration: 'none', color: '#0070f3', fontWeight: 'bold' }}>
            Inglés
          </Link>
        </li>
        <li style={{ marginBottom: 10 }}>
          <Link href="/themes/research" style={{ textDecoration: 'none', color: '#0070f3', fontWeight: 'bold' }}>
            Investigación
          </Link>
        </li>
        <li style={{ marginBottom: 10 }}>
          <Link href="/themes/programming" style={{ textDecoration: 'none', color: '#0070f3', fontWeight: 'bold' }}>
            Programación
          </Link>
        </li>
      </ul>
    </div>
  );
}
