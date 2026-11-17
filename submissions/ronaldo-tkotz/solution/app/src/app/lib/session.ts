/** Stateless signed session cookie. Payload version 2 carries the app user id. */
export const SESSION_COOKIE = "veta_session";
const DEFAULT_TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7 days
const SESSION_VERSION = 2;

export interface SessionPayload {
  v: 2;
  uid: string;
  email: string;
  exp: number;
}

function enc(s: string): Uint8Array<ArrayBuffer> {
  return new Uint8Array(new TextEncoder().encode(s));
}

function b64urlEncode(bytes: Uint8Array): string {
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function b64urlDecode(str: string): Uint8Array<ArrayBuffer> {
  const padded = str + "=".repeat((4 - (str.length % 4)) % 4);
  const bin = atob(padded.replace(/-/g, "+").replace(/_/g, "/"));
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes;
}

async function hmacKey(): Promise<CryptoKey> {
  // Fail CLOSED in production (Cato 2026-07-04): a known fallback secret would let
  // anyone mint valid session cookies. The dev fallback survives only outside prod.
  const secret = process.env.AUTH_SECRET;
  if (!secret && process.env.NODE_ENV === "production") {
    throw new Error("AUTH_SECRET is required in production — refusing to sign/verify sessions with a known default.");
  }
  return crypto.subtle.importKey("raw", enc(secret || "veta-dev-insecure-secret-change-me"), { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"]);
}

export async function createSessionToken(user: { id: string; email: string }, ttlMs = DEFAULT_TTL_MS): Promise<string> {
  const payload: SessionPayload = { v: SESSION_VERSION, uid: user.id, email: user.email, exp: Date.now() + ttlMs };
  const data = b64urlEncode(enc(JSON.stringify(payload)));
  const sig = await crypto.subtle.sign("HMAC", await hmacKey(), enc(data));
  return `${data}.${b64urlEncode(new Uint8Array(sig))}`;
}

export async function verifySessionToken(token: string | undefined | null): Promise<SessionPayload | null> {
  if (!token) return null;
  const dot = token.indexOf(".");
  if (dot <= 0) return null;
  const data = token.slice(0, dot);
  const sig = token.slice(dot + 1);
  try {
    const valid = await crypto.subtle.verify("HMAC", await hmacKey(), b64urlDecode(sig), enc(data));
    if (!valid) return null;
    const payload = JSON.parse(new TextDecoder().decode(b64urlDecode(data))) as Partial<SessionPayload>;
    if (payload.v !== SESSION_VERSION) return null;
    if (typeof payload.uid !== "string" || typeof payload.email !== "string") return null;
    if (typeof payload.exp !== "number" || payload.exp < Date.now()) return null;
    return payload as SessionPayload;
  } catch {
    return null;
  }
}
