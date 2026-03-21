import { NextRequest, NextResponse } from "next/server";
import { updateEntryStatus } from "@/lib/calendar-store";

export async function POST(req: NextRequest) {
  const { id } = await req.json();
  if (!id) return NextResponse.json({ error: "Missing id" }, { status: 400 });

  const entry = updateEntryStatus(id, "aprovado", {
    approved_by: "gestor",
    approved_at: new Date().toISOString(),
  });

  if (!entry) return NextResponse.json({ error: "Entry not found" }, { status: 404 });
  return NextResponse.json({ success: true, entry });
}
