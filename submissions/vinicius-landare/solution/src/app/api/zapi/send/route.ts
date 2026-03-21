import { NextRequest, NextResponse } from "next/server";
import { sendWhatsAppText } from "@/lib/zapi";

export async function POST(req: NextRequest) {
  const instanceId = process.env.ZAPI_INSTANCE_ID;
  const token = process.env.ZAPI_TOKEN;
  const clientToken = process.env.ZAPI_CLIENT_TOKEN;

  if (!instanceId || !token || !clientToken) {
    return NextResponse.json(
      { error: "ZAPI não configurado completamente. Verifique ZAPI_INSTANCE_ID, ZAPI_TOKEN e ZAPI_CLIENT_TOKEN no .env" },
      { status: 400 }
    );
  }

  try {
    const { phone, message } = await req.json();

    if (!phone || !message) {
      return NextResponse.json({ error: "Telefone e mensagem são obrigatórios" }, { status: 400 });
    }

    const result = await sendWhatsAppText({ instanceId, token, clientToken }, phone, message);

    return NextResponse.json({ success: true, ...result });
  } catch (err) {
    console.error("ZAPI send error:", err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Falha ao enviar" },
      { status: 500 }
    );
  }
}
