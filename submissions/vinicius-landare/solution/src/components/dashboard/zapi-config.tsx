"use client";

import { useState, useEffect, useCallback } from "react";

interface ZAPIStatus {
  configured: boolean;
  connected: boolean;
  needsClientToken?: boolean;
  error?: string;
}

export function ZAPIConfig() {
  const [status, setStatus] = useState<ZAPIStatus | null>(null);
  const [checking, setChecking] = useState(false);
  const [open, setOpen] = useState(false);
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [loadingQR, setLoadingQR] = useState(false);

  const checkStatus = useCallback(async () => {
    setChecking(true);
    try {
      const res = await fetch("/api/zapi/status");
      const data = await res.json();
      setStatus(data);
    } catch {
      setStatus({ configured: false, connected: false, error: "Falha ao verificar" });
    }
    setChecking(false);
  }, []);

  async function loadQRCode() {
    setLoadingQR(true);
    setQrCode(null);
    try {
      const res = await fetch("/api/zapi/qrcode");
      const data = await res.json();
      if (data.qrcode) {
        setQrCode(data.qrcode);
      }
    } catch { /* empty */ }
    setLoadingQR(false);
  }

  useEffect(() => { checkStatus(); }, [checkStatus]);

  // Quando abre o modal e está desconectado, carrega QR
  useEffect(() => {
    if (open && status?.configured && !status?.connected) {
      loadQRCode();
    }
  }, [open, status?.configured, status?.connected]);

  const label = !status
    ? "WhatsApp"
    : status.connected
      ? "WhatsApp Conectado"
      : status.configured
        ? "WhatsApp Desconectado"
        : "Conectar WhatsApp";

  const dotColor = !status
    ? "bg-slate-400"
    : status.connected
      ? "bg-emerald-400"
      : status.configured
        ? "bg-amber-400"
        : "bg-slate-400";

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 px-3 py-1 bg-white/10 rounded-full text-xs border border-white/10 hover:bg-white/20 transition-colors"
      >
        <span className={`w-2 h-2 rounded-full ${dotColor} ${checking ? "animate-pulse" : ""}`} />
        <span className="text-white/80">{checking ? "Verificando..." : label}</span>
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setOpen(false)}>
          <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold text-[#0F1B2D]">Conexão WhatsApp (Z-API)</h3>
              <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-600 text-xl">&times;</button>
            </div>

            {/* Status */}
            <div className={`p-4 rounded-xl mb-4 ${
              status?.connected
                ? "bg-emerald-50 border border-emerald-200"
                : status?.configured
                  ? "bg-amber-50 border border-amber-200"
                  : "bg-slate-50 border border-slate-200"
            }`}>
              <div className="flex items-center gap-2 mb-1">
                <span className={`w-3 h-3 rounded-full ${dotColor}`} />
                <span className={`text-sm font-medium ${
                  status?.connected ? "text-emerald-700" : status?.configured ? "text-amber-700" : "text-slate-600"
                }`}>
                  {status?.connected
                    ? "WhatsApp conectado e pronto para enviar mensagens"
                    : status?.configured
                      ? "Z-API configurado, mas WhatsApp desconectado"
                      : "Z-API não configurado"}
                </span>
              </div>
              {status?.error && status.error !== "Status 400" && (
                <p className="text-xs text-red-600 mt-1">{status.error}</p>
              )}
            </div>

            {/* Não configurado */}
            {!status?.configured && (
              <div className="space-y-3 mb-4">
                <p className="text-xs text-slate-600">Para conectar o WhatsApp, configure as variáveis no arquivo <code className="bg-slate-100 px-1 rounded">.env</code>:</p>
                <div className="bg-slate-900 rounded-lg p-3 font-mono text-xs text-emerald-400">
                  <p>ZAPI_INSTANCE_ID=&quot;seu-instance-id&quot;</p>
                  <p>ZAPI_TOKEN=&quot;seu-token&quot;</p>
                </div>
                <p className="text-[10px] text-slate-400">Encontre suas credenciais em app.z-api.io na sua instância.</p>
              </div>
            )}

            {/* Falta client-token */}
            {status?.needsClientToken && (
              <div className="space-y-3 mb-4">
                <p className="text-xs text-slate-600">
                  Falta o <strong>Token de Segurança</strong> (client-token). Adicione no arquivo <code className="bg-slate-100 px-1 rounded">.env</code>:
                </p>
                <div className="bg-slate-900 rounded-lg p-3 font-mono text-xs text-emerald-400">
                  <p>ZAPI_CLIENT_TOKEN=&quot;seu-client-token&quot;</p>
                </div>
                <p className="text-[10px] text-slate-400">
                  Encontre em: Z-API → sua instância → aba Segurança → Token de segurança.
                  Após preencher, reinicie o servidor (npm run dev).
                </p>
              </div>
            )}

            {/* Configurado mas desconectado — mostrar QR Code */}
            {status?.configured && !status?.connected && !status?.needsClientToken && (
              <div className="space-y-3 mb-4">
                <p className="text-xs text-slate-600">
                  Escaneie o QR Code abaixo com o WhatsApp do seu celular para conectar:
                </p>

                <div className="flex justify-center p-4 bg-white border border-slate-200 rounded-xl">
                  {loadingQR ? (
                    <div className="w-48 h-48 flex items-center justify-center">
                      <div className="w-8 h-8 border-2 border-[#E8734A] border-t-transparent rounded-full animate-spin" />
                    </div>
                  ) : qrCode ? (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img src={qrCode} alt="QR Code WhatsApp" className="w-48 h-48" />
                  ) : (
                    <div className="w-48 h-48 flex items-center justify-center text-center">
                      <p className="text-xs text-slate-400">QR Code não disponível. Use o painel Z-API.</p>
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={loadQRCode}
                    disabled={loadingQR}
                    className="flex-1 px-3 py-2 text-xs border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 disabled:opacity-50"
                  >
                    {loadingQR ? "Carregando..." : "Atualizar QR Code"}
                  </button>
                  <a
                    href="https://app.z-api.io"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 px-3 py-2 bg-[#0F1B2D] text-white text-xs text-center rounded-lg hover:bg-[#1A2D47] transition-colors"
                  >
                    Abrir painel Z-API
                  </a>
                </div>

                <div className="bg-slate-50 rounded-lg p-3 text-[11px] text-slate-500 space-y-1">
                  <p className="font-medium text-slate-600">Como escanear:</p>
                  <p>1. Abra o WhatsApp no celular</p>
                  <p>2. Toque em Configurações → Aparelhos conectados</p>
                  <p>3. Toque em Conectar aparelho</p>
                  <p>4. Aponte a câmera para o QR Code acima</p>
                </div>
              </div>
            )}

            {/* Conectado */}
            {status?.connected && (
              <div className="space-y-2 mb-4">
                <p className="text-xs text-slate-600">
                  Seu WhatsApp está conectado. Você pode enviar mensagens para influenciadores
                  diretamente pela aba Influenciadores.
                </p>
              </div>
            )}

            <button
              onClick={checkStatus}
              disabled={checking}
              className="w-full px-4 py-2 border border-slate-300 text-slate-700 text-sm rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50"
            >
              {checking ? "Verificando..." : "Verificar conexão"}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
