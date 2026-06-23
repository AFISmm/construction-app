import ProjectGate from "@/components/ProjectGate";

export default async function ExpensesPage({
  searchParams,
}: {
  searchParams: Promise<{ pid?: string }>;
}) {
  const params = await searchParams;
  if (!params.pid) return <ProjectGate />;
  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-4">Payments</h1>
      <p className="text-gray-400">Coming soon — module in development.</p>
    </div>
  );
}
