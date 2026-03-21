import { NextResponse } from "next/server";
import { checkConnection } from "@/lib/zapi";

function getZAPIConfig() {
  return {
    instanceId: process.env.ZAPI_INSTANCE_ID || "",
    token: process.env.ZAPI_TOKEN || "",
    clientToken: process.env.ZAPI_CLIENT_TOKEN || undefined,
  };
}

export async function GET() {
  const config = getZAPIConfig();

  if (!config.instanceId || !config.token) {
    return NextResponse.json({
      configured: false,
      connected: false,
      error: "ZAPI_INSTANCE_ID e ZAPI_TOKEN não configurados no .env",
    });
  }

  if (!config.clientToken) {
    return NextResponse.json({
      configured: true,
      connected: false,
      needsClientToken: true,
      error: "ZAPI_CLIENT_TOKEN não configurado. Vá em Z-API > Instância > Segurança > Token de segurança.",
    });
  }

  const status = await checkConnection(config);

  return NextResponse.json({
    configured: true,
    ...status,
  });
}

export async function POST() {
  return GET();
}
