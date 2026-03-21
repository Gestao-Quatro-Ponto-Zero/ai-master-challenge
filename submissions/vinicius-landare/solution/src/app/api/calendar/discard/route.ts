import { NextRequest, NextResponse } from "next/server";
import { removeEntry } from "@/lib/calendar-store";

export async function POST(req: NextRequest) {
  const { id } = await req.json();
  if (!id) return NextResponse.json({ error: "Missing id" }, { status: 400 });

  const removed = removeEntry(id);
  if (!removed) return NextResponse.json({ error: "Entry not found" }, { status: 404 });
  return NextResponse.json({ success: true, removed: id });
}
