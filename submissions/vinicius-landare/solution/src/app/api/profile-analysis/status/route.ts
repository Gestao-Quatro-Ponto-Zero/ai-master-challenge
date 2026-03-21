import { NextRequest, NextResponse } from "next/server";
import { getJob } from "@/lib/analysis-jobs";

export async function GET(req: NextRequest) {
  const jobId = req.nextUrl.searchParams.get("id");
  if (!jobId) return NextResponse.json({ error: "Missing job id" }, { status: 400 });

  const job = getJob(jobId);
  if (!job) return NextResponse.json({ error: "Job não encontrado" }, { status: 404 });

  return NextResponse.json(job);
}
