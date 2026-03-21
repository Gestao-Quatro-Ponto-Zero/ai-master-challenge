/**
 * ZAPI Client — Integração WhatsApp
 * Documentação: https://developer.z-api.io/
 */

interface ZAPIConfig {
  instanceId: string;
  token: string;
  clientToken?: string;
}

function getHeaders(clientToken?: string): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (clientToken) {
    headers["client-token"] = clientToken;
  }
  return headers;
}

interface SendTextResponse {
  zapiMessageId?: string;
  messageId?: string;
  id?: string;
  phone?: string;
  status?: string;
  error?: string;
}

interface ConnectionStatus {
  connected: boolean;
  smartphoneConnected?: boolean;
  session?: string;
  error?: string;
}

export async function sendWhatsAppText(
  config: ZAPIConfig,
  phone: string,
  message: string
): Promise<SendTextResponse> {
  const url = `https://api.z-api.io/instances/${config.instanceId}/token/${config.token}/send-text`;

  const res = await fetch(url, {
    method: "POST",
    headers: getHeaders(config.clientToken),
    body: JSON.stringify({
      phone: phone.replace(/\D/g, ""),
      message,
    }),
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`ZAPI send failed (${res.status}): ${error}`);
  }

  return res.json();
}

export async function checkConnection(config: ZAPIConfig): Promise<ConnectionStatus> {
  const url = `https://api.z-api.io/instances/${config.instanceId}/token/${config.token}/status`;

  try {
    const res = await fetch(url, {
      method: "GET",
      headers: getHeaders(config.clientToken),
    });

    if (!res.ok) {
      return { connected: false, error: `Status ${res.status}` };
    }

    const data = await res.json();
    return {
      connected: data.connected === true || data.smartphoneConnected === true,
      smartphoneConnected: data.smartphoneConnected,
      session: data.session,
    };
  } catch (err) {
    return {
      connected: false,
      error: err instanceof Error ? err.message : "Connection check failed",
    };
  }
}

export async function getQRCode(config: ZAPIConfig): Promise<{ value?: string; error?: string }> {
  const url = `https://api.z-api.io/instances/${config.instanceId}/token/${config.token}/qr-code/image`;

  try {
    const res = await fetch(url, {
      method: "GET",
      headers: getHeaders(config.clientToken),
    });

    if (!res.ok) {
      return { error: `Status ${res.status}` };
    }

    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("image")) {
      const buffer = await res.arrayBuffer();
      const base64 = Buffer.from(buffer).toString("base64");
      return { value: `data:${contentType};base64,${base64}` };
    }

    const data = await res.json();
    return { value: data.value || data.qrcode };
  } catch (err) {
    return { error: err instanceof Error ? err.message : "QR code fetch failed" };
  }
}
