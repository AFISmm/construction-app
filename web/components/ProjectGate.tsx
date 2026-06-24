import { cookies } from "next/headers";
import { t, Lang } from "@/lib/lang";

export default async function ProjectGate() {
  const lang = ((await cookies()).get("ck_lang")?.value ?? "en") as Lang;
  return (
    <div className="flex items-center justify-center h-64">
      <p className="text-gray-400 text-sm">{t("lbl_select_project", lang)}</p>
    </div>
  );
}
