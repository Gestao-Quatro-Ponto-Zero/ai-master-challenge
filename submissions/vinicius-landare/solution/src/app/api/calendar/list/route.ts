import { NextRequest, NextResponse } from "next/server";
import { readCalendar } from "@/lib/calendar-store";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const status = searchParams.get("status");
  const from = searchParams.get("from");
  const to = searchParams.get("to");

  const cal = readCalendar();
  let entries = cal.entries;

  if (status) {
    entries = entries.filter((e) => e.status === status);
  }
  if (from) {
    entries = entries.filter((e) => e.scheduled_date >= from);
  }
  if (to) {
    entries = entries.filter((e) => e.scheduled_date <= to);
  }

  return NextResponse.json({
    total: entries.length,
    entries: entries.sort((a, b) => a.scheduled_date.localeCompare(b.scheduled_date)),
  });
}
