"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

function toUsername(first: string, last: string): string {
  const cap = (s: string) => s.trim().charAt(0).toUpperCase() + s.trim().slice(1).toLowerCase();
  return cap(first) + cap(last);
}

export default function RegisterPage() {
  const router = useRouter();
  const [firstName, setFirstName] = useState("");
  const [lastName,  setLastName]  = useState("");
  const [email,     setEmail]     = useState("");
  const [password,  setPassword]  = useState("");
  const [confirm,   setConfirm]   = useState("");
  const [error,     setError]     = useState("");
  const [loading,   setLoading]   = useState(false);

  const username = firstName && lastName ? toUsername(firstName, lastName) : "";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirm) { setError("Las contraseñas no coinciden"); return; }
    setLoading(true);
    setError("");
    const res = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ firstName, lastName, email, password }),
    });
    if (res.ok) {
      router.push("/dashboard");
    } else {
      const data = await res.json();
      setError(data.error || "Error al registrar");
    }
    setLoading(false);
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-bold text-center text-white mb-2">Construction Budget</h1>
        <p className="text-center text-gray-400 text-sm mb-8">Crear cuenta</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 1. Nombre */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">Nombre</label>
            <input
              type="text"
              value={firstName}
              onChange={e => setFirstName(e.target.value)}
              required
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-orange-500"
              placeholder="Felipe"
            />
          </div>

          {/* 2. Apellido */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">Apellido</label>
            <input
              type="text"
              value={lastName}
              onChange={e => setLastName(e.target.value)}
              required
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-orange-500"
              placeholder="Serna"
            />
          </div>

          {/* 3. Correo electrónico */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">Correo electrónico</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-orange-500"
              placeholder="tu@ejemplo.com"
            />
          </div>

          {/* 4. Usuario (autogenerado, solo lectura) */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">
              Usuario <span className="text-gray-500 text-xs">(generado automáticamente)</span>
            </label>
            <input
              type="text"
              value={username}
              readOnly
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-gray-300 cursor-not-allowed"
              placeholder="NombreApellido"
            />
          </div>

          {/* Contraseña */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              minLength={6}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-orange-500"
              placeholder="Mínimo 6 caracteres"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-300 mb-1">Confirmar contraseña</label>
            <input
              type="password"
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
              required
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-orange-500"
              placeholder="Repite la contraseña"
            />
          </div>

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={loading || !username}
            className="w-full bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white font-semibold py-2 rounded-lg transition-colors"
          >
            {loading ? "Creando cuenta…" : "Crear cuenta"}
          </button>
        </form>

        <p className="text-center text-gray-500 text-sm mt-6">
          ¿Ya tienes cuenta?{" "}
          <Link href="/login" className="text-orange-400 hover:text-orange-300">
            Iniciar sesión
          </Link>
        </p>
      </div>
    </div>
  );
}
