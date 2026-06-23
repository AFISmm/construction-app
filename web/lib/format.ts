export function fmtMoney(value: number | string | null | undefined): string {
  const n = typeof value === "string" ? parseFloat(value) : (value ?? 0);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(n);
}

export function toNum(value: unknown): number {
  if (value === null || value === undefined) return 0;
  if (typeof value === "object" && "toNumber" in (value as object)) {
    return (value as { toNumber(): number }).toNumber();
  }
  return Number(value) || 0;
}
