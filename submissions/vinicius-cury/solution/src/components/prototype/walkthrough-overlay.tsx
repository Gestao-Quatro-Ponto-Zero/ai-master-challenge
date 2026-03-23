"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { X, ChevronRight, RotateCcw } from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────────

interface WalkthroughStep {
  id: string;
  title: string;
  description: string;
  targetSelector?: string;
  position?: "top" | "bottom" | "left" | "right";
  isModal?: boolean;
  action?: "type-and-send" | "navigate" | "wait";
  actionPayload?: string;
  waitMs?: number;
}

interface WalkthroughOverlayProps {
  isActive: boolean;
  onClose: () => void;
  onSendMessage?: (content: string) => Promise<void>;
  chatInputRef?: React.RefObject<HTMLInputElement | null>;
}

// ─── Steps ───────────────────────────────────────────────────────────

const STEPS: WalkthroughStep[] = [
  {
    id: "welcome",
    title: "Bem-vindo ao Protótipo OptiFlow",
    description:
      "Este tour guiado demonstra o sistema de suporte inteligente: classificação automática, roteamento por cenário e dashboard do operador. Clique 'Próximo' para começar.",
    isModal: true,
  },
  {
    id: "chat-intro",
    title: "Chat de Atendimento",
    description:
      "Aqui o cliente descreve seu problema. O sistema classifica automaticamente usando IA (84.6% de acurácia).",
    targetSelector: "[data-walkthrough='chat-widget']",
    position: "right",
  },
  {
    id: "prefill-message",
    title: "Enviando mensagem de teste",
    description:
      "Observe a mensagem sendo digitada automaticamente e enviada para classificação...",
    targetSelector: "[data-walkthrough='chat-input']",
    position: "top",
    action: "type-and-send",
    actionPayload:
      "Meu notebook Dell não liga desde ontem. Já tentei reiniciar mas a tela fica preta e o LED pisca.",
  },
  {
    id: "classification-panel",
    title: "Pipeline de Classificação",
    description:
      "Veja a classificação em tempo real: categoria, sub-classificação, cenário de roteamento e ação recomendada.",
    targetSelector: "[data-walkthrough='classification-panel']",
    position: "left",
  },
  {
    id: "wait-response",
    title: "Processando classificação...",
    description:
      "Aguarde a classificação ser concluída pelo modelo de IA. O pipeline mostra cada etapa em sequência.",
    targetSelector: "[data-walkthrough='classification-panel']",
    position: "left",
    action: "wait",
    waitMs: 3000,
  },
  {
    id: "kb-response",
    title: "Resposta da Base de Conhecimento",
    description:
      "O sistema busca na base de conhecimento e sintetiza uma resposta personalizada para o cliente.",
    targetSelector: "[data-walkthrough='chat-widget']",
    position: "right",
  },
  {
    id: "escalation-preview",
    title: "Escalonamento Inteligente",
    description:
      "Se o cliente não estiver satisfeito, o sistema escala para um operador humano com todo o contexto preservado.",
    targetSelector: "[data-walkthrough='chat-widget']",
    position: "right",
  },
  {
    id: "navigate-operador",
    title: "Painel do Operador",
    description:
      "No painel do operador, tickets escalados aparecem em tempo real, classificados e priorizados.",
    isModal: true,
    action: "navigate",
    actionPayload: "/prototype/operador",
  },
  {
    id: "queue-highlight",
    title: "Fila de Tickets",
    description:
      "Tickets organizados por cenário e SLA. Badges coloridos indicam a urgência.",
    targetSelector: "[data-walkthrough='queue-list']",
    position: "right",
  },
  {
    id: "navigate-simulador",
    title: "Simulador de Tickets",
    description:
      "O simulador permite testar o sistema com tickets reais do dataset.",
    isModal: true,
    action: "navigate",
    actionPayload: "/prototype/simulador",
  },
  {
    id: "simulation",
    title: "Controles de Simulação",
    description:
      "Experimente! Configure a quantidade de tickets e veja as métricas ao vivo.",
    targetSelector: "[data-walkthrough='simulation-controls']",
    position: "bottom",
  },
  {
    id: "complete",
    title: "Tour completo!",
    description:
      "Explore livremente. Use o botão 'Resetar Dados' no Simulador para limpar e recomeçar.",
    isModal: true,
  },
];

const STORAGE_KEY = "optiflow-walkthrough-completed";

// ─── Tooltip Arrow ───────────────────────────────────────────────────

function getArrowClasses(position: "top" | "bottom" | "left" | "right") {
  switch (position) {
    case "top":
      return "bottom-[-6px] left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent border-t-white";
    case "bottom":
      return "top-[-6px] left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent border-b-white";
    case "left":
      return "right-[-6px] top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent border-l-white";
    case "right":
      return "left-[-6px] top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent border-r-white";
  }
}

// ─── Main Component ─────────────────────────────────────────────────

export function WalkthroughOverlay({
  isActive,
  onClose,
  onSendMessage,
  chatInputRef,
}: WalkthroughOverlayProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [tooltipStyle, setTooltipStyle] = useState<React.CSSProperties>({});
  const [highlightStyle, setHighlightStyle] = useState<React.CSSProperties>({});
  const [isTyping, setIsTyping] = useState(false);
  const router = useRouter();
  const typingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const waitTimerRef = useRef<NodeJS.Timeout | null>(null);

  const step = STEPS[currentStep];
  const totalSteps = STEPS.length;

  // ─── Position tooltip near target element ──────────────────────────

  const positionTooltip = useCallback(() => {
    if (!step || step.isModal || !step.targetSelector) return;

    const target = document.querySelector(step.targetSelector);
    if (!target) return;

    const rect = target.getBoundingClientRect();
    const padding = 8;
    const tooltipWidth = 340;
    const tooltipHeight = 180;
    const pos = step.position || "bottom";

    // Highlight box
    setHighlightStyle({
      top: rect.top - padding,
      left: rect.left - padding,
      width: rect.width + padding * 2,
      height: rect.height + padding * 2,
    });

    // Tooltip position
    let top = 0;
    let left = 0;

    switch (pos) {
      case "top":
        top = rect.top - tooltipHeight - padding - 12;
        left = rect.left + rect.width / 2 - tooltipWidth / 2;
        break;
      case "bottom":
        top = rect.bottom + padding + 12;
        left = rect.left + rect.width / 2 - tooltipWidth / 2;
        break;
      case "left":
        top = rect.top + rect.height / 2 - tooltipHeight / 2;
        left = rect.left - tooltipWidth - padding - 12;
        break;
      case "right":
        top = rect.top + rect.height / 2 - tooltipHeight / 2;
        left = rect.right + padding + 12;
        break;
    }

    // Clamp to viewport
    top = Math.max(8, Math.min(top, window.innerHeight - tooltipHeight - 8));
    left = Math.max(8, Math.min(left, window.innerWidth - tooltipWidth - 8));

    setTooltipStyle({ top, left, width: tooltipWidth });
  }, [step]);

  useEffect(() => {
    if (!isActive) return;
    positionTooltip();
    window.addEventListener("resize", positionTooltip);
    window.addEventListener("scroll", positionTooltip, true);
    return () => {
      window.removeEventListener("resize", positionTooltip);
      window.removeEventListener("scroll", positionTooltip, true);
    };
  }, [isActive, currentStep, positionTooltip]);

  // Re-position after a short delay (for elements that render async)
  useEffect(() => {
    if (!isActive) return;
    const timer = setTimeout(positionTooltip, 300);
    return () => clearTimeout(timer);
  }, [isActive, currentStep, positionTooltip]);

  // ─── Cleanup timers on unmount ─────────────────────────────────────

  useEffect(() => {
    return () => {
      if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
      if (waitTimerRef.current) clearTimeout(waitTimerRef.current);
    };
  }, []);

  // ─── Handle step actions ───────────────────────────────────────────

  const executeStepAction = useCallback(
    async (stepData: WalkthroughStep) => {
      if (stepData.action === "type-and-send" && stepData.actionPayload) {
        if (!chatInputRef?.current || !onSendMessage) {
          // Skip typing if no refs available
          return;
        }

        setIsTyping(true);
        const text = stepData.actionPayload;
        let charIndex = 0;

        // Clear input first
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
          window.HTMLInputElement.prototype,
          "value"
        )?.set;

        const typeNextChar = () => {
          if (charIndex <= text.length && chatInputRef.current) {
            nativeInputValueSetter?.call(
              chatInputRef.current,
              text.substring(0, charIndex)
            );
            chatInputRef.current.dispatchEvent(
              new Event("input", { bubbles: true })
            );
            charIndex++;
            typingTimerRef.current = setTimeout(typeNextChar, 25);
          } else {
            setIsTyping(false);
            // Auto-send after typing completes
            setTimeout(() => {
              onSendMessage(text);
            }, 400);
          }
        };

        typeNextChar();
      } else if (stepData.action === "navigate" && stepData.actionPayload) {
        router.push(stepData.actionPayload);
      } else if (stepData.action === "wait" && stepData.waitMs) {
        await new Promise<void>((resolve) => {
          waitTimerRef.current = setTimeout(resolve, stepData.waitMs);
        });
      }
    },
    [chatInputRef, onSendMessage, router]
  );

  // Execute action when step changes
  useEffect(() => {
    if (!isActive || !step) return;

    if (step.action) {
      executeStepAction(step);
    }
  }, [isActive, currentStep, step, executeStepAction]);

  // ─── Navigation ────────────────────────────────────────────────────

  const handleNext = useCallback(() => {
    if (isTyping) return;

    if (currentStep < totalSteps - 1) {
      setCurrentStep((prev) => prev + 1);
    } else {
      // Tour complete
      localStorage.setItem(STORAGE_KEY, "true");
      onClose();
    }
  }, [currentStep, totalSteps, onClose, isTyping]);

  const handleClose = useCallback(() => {
    localStorage.setItem(STORAGE_KEY, "true");
    if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
    if (waitTimerRef.current) clearTimeout(waitTimerRef.current);
    setIsTyping(false);
    onClose();
  }, [onClose]);

  if (!isActive || !step) return null;

  // ─── Modal step ────────────────────────────────────────────────────

  if (step.isModal) {
    return (
      <div className="fixed inset-0 z-[100] flex items-center justify-center">
        {/* Backdrop */}
        <div className="absolute inset-0 bg-black/60" />

        {/* Modal */}
        <div className="relative z-10 mx-4 w-full max-w-md rounded-xl border bg-white p-6 shadow-2xl">
          {/* Step counter */}
          <div className="mb-4 flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">
              Passo {currentStep + 1} de {totalSteps}
            </span>
            <button
              onClick={handleClose}
              className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <h2 className="text-lg font-semibold">{step.title}</h2>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            {step.description}
          </p>

          <div className="mt-6 flex items-center justify-between">
            <Button variant="ghost" size="sm" onClick={handleClose}>
              Pular Tour
            </Button>
            <Button size="sm" onClick={handleNext} className="gap-1">
              {currentStep === totalSteps - 1 ? (
                "Finalizar"
              ) : (
                <>
                  Próximo
                  <ChevronRight className="h-4 w-4" />
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // ─── Tooltip step (with highlight) ─────────────────────────────────

  return (
    <div className="fixed inset-0 z-[100]">
      {/* Semi-transparent overlay with hole */}
      <div className="absolute inset-0 bg-black/50" onClick={handleClose} />

      {/* Highlight cutout */}
      <div
        className="absolute z-10 rounded-lg ring-4 ring-primary/50"
        style={{
          ...highlightStyle,
          backgroundColor: "transparent",
          boxShadow: "0 0 0 9999px rgba(0,0,0,0.5)",
          pointerEvents: "none",
        }}
      />

      {/* Tooltip */}
      <div
        className="absolute z-20 rounded-xl border bg-white p-4 shadow-2xl"
        style={tooltipStyle}
      >
        {/* Arrow */}
        <div
          className={cn(
            "absolute h-0 w-0 border-[6px]",
            getArrowClasses(step.position || "bottom")
          )}
        />

        {/* Step counter */}
        <div className="mb-2 flex items-center justify-between">
          <span className="text-xs font-medium text-muted-foreground">
            Passo {currentStep + 1} de {totalSteps}
          </span>
          <button
            onClick={handleClose}
            className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>

        <h3 className="text-sm font-semibold">{step.title}</h3>
        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
          {step.description}
        </p>

        <div className="mt-3 flex items-center justify-between">
          <Button variant="ghost" size="sm" onClick={handleClose} className="h-7 px-2 text-xs">
            Pular Tour
          </Button>
          <Button
            size="sm"
            onClick={handleNext}
            disabled={isTyping}
            className="h-7 gap-1 px-3 text-xs"
          >
            {isTyping ? (
              "Digitando..."
            ) : currentStep === totalSteps - 1 ? (
              "Finalizar"
            ) : (
              <>
                Próximo
                <ChevronRight className="h-3.5 w-3.5" />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

// ─── Hook for walkthrough state ──────────────────────────────────────

export function useWalkthrough() {
  const [isActive, setIsActive] = useState(false);

  const start = useCallback(() => setIsActive(true), []);
  const close = useCallback(() => setIsActive(false), []);

  const hasCompleted =
    typeof window !== "undefined"
      ? localStorage.getItem(STORAGE_KEY) === "true"
      : false;

  const reset = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  return { isActive, start, close, hasCompleted, reset };
}

// ─── Start Tour Button ──────────────────────────────────────────────

export function StartTourButton({ onClick }: { onClick: () => void }) {
  return (
    <Button
      variant="outline"
      size="sm"
      onClick={onClick}
      className="gap-1.5"
    >
      <RotateCcw className="h-3.5 w-3.5" />
      Iniciar Tour Guiado
    </Button>
  );
}
