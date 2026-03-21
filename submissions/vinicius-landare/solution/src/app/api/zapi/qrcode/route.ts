import { NextResponse } from "next/server";
import { getQRCode } from "@/lib/zapi";

export async function GET() {
  const instanceId = process.env.ZAPI_INSTANCE_ID;
  const token = process.env.ZAPI_TOKEN;
  const clientToken = process.env.ZAPI_CLIENT_TOKEN;

  if (!instanceId || !token) {
    return NextResponse.json({ error: "ZAPI não configurado" }, { status: 400 });
  }

  if (!clientToken) {
    return NextResponse.json({ error: "ZAPI_CLIENT_TOKEN não configurado. Vá em Z-API > Segurança > Token de segurança." }, { status: 400 });
  }

  const result = await getQRCode({ instanceId, token, clientToken });

  if (result.error) {
    return NextResponse.json({ error: result.error });
  }

  return NextResponse.json({ qrcode: result.value });
}
