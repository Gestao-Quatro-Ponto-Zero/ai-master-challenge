import { NextRequest, NextResponse } from "next/server";
import { rescheduleEntry } from "@/lib/calendar-store";

export async function POST(req: NextRequest) {
  const { id, date, time } = await req.json();
  if (!id || !date || !time) {
    return NextResponse.json({ error: "Missing id, date, or time" }, { status: 400 });
  }

  const entry = rescheduleEntry(id, date, time);
  if (!entry) return NextResponse.json({ error: "Entry not found" }, { status: 404 });
  return NextResponse.json({ success: true, entry });
}
