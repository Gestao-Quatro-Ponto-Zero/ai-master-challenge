"use client";

import { useState, useRef, useCallback } from "react";

interface InfoTooltipProps {
  text: string;
}

export function InfoTooltip({ text }: InfoTooltipProps) {
  const [pos, setPos] = useState<{ top: number; left: number; below: boolean } | null>(null);
  const btnRef = useRef<HTMLButtonElement>(null);

  const show = useCallback(() => {
    if (btnRef.current) {
      const r = btnRef.current.getBoundingClientRect();
      const cx = r.left + r.width / 2;
      // If button is in the top 120px of viewport, show tooltip below instead
      const below = r.top < 120;
      setPos({ top: below ? r.bottom + 8 : r.top - 8, left: cx, below });
    }
  }, []);

  const hide = useCallback(() => setPos(null), []);

  return (
    <span className="inline-block ml-0.5 align-middle">
      <button
        ref={btnRef}
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={hide}
        className="text-gray-600 hover:text-gray-400 transition-colors focus:outline-none"
        aria-label="Informação"
        tabIndex={-1}
      >
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {pos && (
        <div
          className="fixed z-[9999] w-64 pointer-events-none"
          style={{
            top: pos.top,
            left: pos.left,
            transform: pos.below
              ? "translateX(-50%)"
              : "translateX(-50%) translateY(-100%)",
          }}
        >
          {/* Arrow on top when tooltip is below the button */}
          {pos.below && (
            <div className="flex justify-center mb-0.5">
              <div className="w-2 h-2 bg-gray-800 border-l border-t border-gray-600 rotate-45" />
            </div>
          )}

          <div className="bg-gray-800 border border-gray-600 text-gray-200 text-xs rounded-xl px-3 py-2.5 shadow-2xl shadow-black/50 leading-relaxed">
            {text}
          </div>

          {/* Arrow below tooltip when tooltip is above the button */}
          {!pos.below && (
            <div className="flex justify-center -mt-px">
              <div className="w-2 h-2 bg-gray-800 border-r border-b border-gray-600 rotate-45" />
            </div>
          )}
        </div>
      )}
    </span>
  );
}
