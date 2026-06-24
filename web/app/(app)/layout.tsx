import { Suspense } from "react";
import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth";
import Sidebar from "@/components/Sidebar";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const user = await getSession();
  if (!user) redirect("/login");

  const displayName = user.username ?? user.email;

  return (
    <div className="flex h-screen overflow-hidden bg-gray-950">
      <Suspense fallback={<div className="w-56 bg-gray-900 border-r border-gray-800" />}>
        <Sidebar userDisplay={displayName} />
      </Suspense>
      <main className="flex-1 overflow-y-auto p-6">{children}</main>
    </div>
  );
}
