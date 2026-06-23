import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth";
import Sidebar from "@/components/Sidebar";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const user = await getSession();
  if (!user) redirect("/login");

  return (
    <div className="flex h-screen overflow-hidden bg-gray-950">
      <Sidebar userEmail={user.email} />
      <main className="flex-1 overflow-y-auto p-6">{children}</main>
    </div>
  );
}
