export type BoqExportRow = {
  sno: string;
  description: string;
  unit: string;
  qty: number;
  rate: number;
  amount: number;
  category: string;
  notes?: string;
};

export function recalcBoqItem(item: BoqExportRow): BoqExportRow {
  const qty = Number(item.qty) || 0;
  const rate = Number(item.rate) || 0;
  return { ...item, qty, rate, amount: Math.round(qty * rate * 100) / 100 };
}

export function downloadBoqCsv(
  items: BoqExportRow[],
  gst?: Record<string, number | string>,
  filename = "boq.csv",
) {
  const header = ["#", "Description", "Unit", "Qty", "Rate", "Amount", "Category"];
  const rows = items.map((it) => [
    it.sno,
    it.description,
    it.unit,
    String(it.qty),
    String(it.rate),
    String(it.amount),
    it.category,
  ]);
  const lines = [header, ...rows];
  if (gst) {
    lines.push([]);
    lines.push(["Material", String(gst.material_subtotal ?? "")]);
    lines.push(["Labour", String(gst.labour_subtotal ?? "")]);
    lines.push(["GST", String(gst.gst_amount ?? "")]);
    lines.push(["Grand Total (incl. GST)", String(gst.grand_total_with_gst ?? "")]);
  }
  const csv = lines.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function exportBoqViaApi(
  apiBase: string,
  items: BoqExportRow[],
  format: "csv" | "xlsx" | "pdf",
  gst?: Record<string, unknown>,
  companyName?: string,
) {
  const res = await fetch(`${apiBase.replace(/\/$/, "")}/export/boq`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      items,
      gst_breakdown: gst,
      format,
      company_name: companyName ?? "Blueprint Reader BOQ",
    }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `Export failed (${res.status})`);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `boq.${format === "xlsx" ? "xlsx" : format}`;
  a.click();
  URL.revokeObjectURL(url);
}
