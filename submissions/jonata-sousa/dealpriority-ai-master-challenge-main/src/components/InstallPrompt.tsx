import { useState, useEffect } from "react";
import { Download, X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

export function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [showBanner, setShowBanner] = useState(false);
  const [isIOS, setIsIOS] = useState(false);
  const [showIOSTip, setShowIOSTip] = useState(false);

  useEffect(() => {
    // Don't show in iframes (Lovable preview)
    try {
      if (window.self !== window.top) return;
    } catch {
      return;
    }

    // Check if already installed
    if (window.matchMedia("(display-mode: standalone)").matches) return;

    // iOS detection
    const ua = navigator.userAgent;
    const isiOS = /iPad|iPhone|iPod/.test(ua) && !(window as any).MSStream;
    setIsIOS(isiOS);

    if (isiOS) {
      const dismissed = sessionStorage.getItem("pwa-ios-dismissed");
      if (!dismissed) setShowIOSTip(true);
      return;
    }

    // Android / Chrome
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      const dismissed = sessionStorage.getItem("pwa-dismissed");
      if (!dismissed) setShowBanner(true);
    };

    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    await deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === "accepted") {
      setShowBanner(false);
    }
    setDeferredPrompt(null);
  };

  const dismiss = () => {
    setShowBanner(false);
    setShowIOSTip(false);
    sessionStorage.setItem("pwa-dismissed", "1");
    sessionStorage.setItem("pwa-ios-dismissed", "1");
  };

  if (showIOSTip) {
    return (
      <div className="fixed bottom-4 left-4 right-4 z-50 mx-auto max-w-md bg-card border rounded-xl shadow-lg p-4 animate-in slide-in-from-bottom-4">
        <div className="flex items-start gap-3">
          <Download className="h-5 w-5 text-primary mt-0.5 shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-foreground">Instalar DealPriority</p>
            <p className="text-xs text-muted-foreground mt-1">
              Toque em <span className="font-semibold">Compartilhar</span> (ícone ↑) e depois em{" "}
              <span className="font-semibold">Adicionar à Tela de Início</span>.
            </p>
          </div>
          <button onClick={dismiss} className="text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    );
  }

  if (!showBanner) return null;

  return (
    <div className="fixed bottom-4 left-4 right-4 z-50 mx-auto max-w-md bg-card border rounded-xl shadow-lg p-4 animate-in slide-in-from-bottom-4">
      <div className="flex items-center gap-3">
        <Download className="h-5 w-5 text-primary shrink-0" />
        <div className="flex-1">
          <p className="text-sm font-semibold text-foreground">Instalar DealPriority</p>
          <p className="text-xs text-muted-foreground mt-0.5">Acesse direto da sua tela inicial.</p>
        </div>
        <Button size="sm" onClick={handleInstall} className="h-8 text-xs">
          Instalar
        </Button>
        <button onClick={dismiss} className="text-muted-foreground hover:text-foreground">
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
