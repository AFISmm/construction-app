"use server";
import { prisma } from "@/lib/db";
import { revalidatePath } from "next/cache";

export async function updateBudgetLine(id: number, projectId: number, amount: number) {
  await prisma.budget_lines.update({
    where: { id, project_id: projectId },
    data: { budgeted_amount: amount },
  });
  revalidatePath("/budget");
  revalidatePath("/dashboard");
}
