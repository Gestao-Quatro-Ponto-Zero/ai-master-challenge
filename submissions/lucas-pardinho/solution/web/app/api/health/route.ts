import { getDataStatus } from "@/lib/data";

export const dynamic = "force-dynamic";

export async function GET() {
  const data = await getDataStatus();
  const healthy = data.source !== "unavailable";

  return Response.json(
    {
      status: healthy ? "ok" : "unavailable",
      service: "g4-focus-web",
      data: {
        source: data.source,
        availableFiles: data.availableFiles.length,
        expectedFiles: data.availableFiles.length + data.missingFiles.length,
      },
      timestamp: new Date().toISOString(),
    },
    { status: healthy ? 200 : 503 },
  );
}
