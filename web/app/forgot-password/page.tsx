"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    setLoading(true);
    setError("");
    const res = await fetch("/api/auth/reset-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (res.ok) {
      setSuccess(true);
      setTimeout(() => router.push("/login"), 2000);
    } else {
      const data = await res.json();
      setError(data.error || "Reset failed");
    }
    setLoading(false);
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-bold text-center text-white mb-2">
          Construction Budget
        </h1>
        <p className="text-center text-gray-400 text-sm mb-8">Reset your password</p>

        {success ? (
          <div className="text-center">
            <p className="text-green-400 font-semibold mb-2">Password updated!</p>
            <p className="text-gray-400 text-sm">Redirecting to sign in…</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-gray-300 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-orange-500"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-300 mb-1">New Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-orange-500"
                placeholder="Min 6 characters"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-300 mb-1">Confirm Password</label>
              <input
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-orange-500"
                placeholder="Repeat password"
              />
            </div>
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white font-semibold py-2 rounded-lg transition-colors"
            >
              {loading ? "Updating…" : "Reset Password"}
            </button>
          </form>
        )}

        <p className="text-center text-gray-500 text-sm mt-6">
          <Link href="/login" className="text-orange-400 hover:text-orange-300">
            Back to Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
