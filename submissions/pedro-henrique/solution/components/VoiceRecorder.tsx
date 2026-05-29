"use client";

import type React from "react";

const BAR_HEIGHTS = [8, 18, 12, 22, 9, 20, 14, 10, 18, 8];
const BAR_DURATIONS = ["0.45s", "0.6s", "0.5s", "0.38s", "0.55s", "0.42s", "0.58s", "0.48s", "0.52s", "0.44s"];

type Props = { status: "recording" | "transcribing" };

export function VoiceRecorder({ status }: Props) {
  if (status === "transcribing") {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 4px" }}>
        <span
          style={{
            width: 18, height: 18, borderRadius: "50%",
            border: "2px solid #7c3aed", borderTopColor: "transparent",
            animation: "spin 0.7s linear infinite",
            display: "inline-block", flexShrink: 0,
          }}
        />
        <span style={{ fontSize: "0.875rem", fontWeight: 600, color: "#7c3aed" }}>
          Transcrevendo áudio…
        </span>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 4px" }}>
      <span
        style={{
          width: 9, height: 9, borderRadius: "50%", background: "#ef4444", flexShrink: 0,
          animation: "rec-dot-blink 1s ease-in-out infinite",
        }}
      />
      <div className="voice-waveform">
        {BAR_HEIGHTS.map((h, i) => (
          <span
            key={i}
            className="voice-wave-bar"
            style={{
              height: h,
              "--wave-dur": BAR_DURATIONS[i],
              animationDelay: `${i * 0.04}s`,
            } as React.CSSProperties}
          />
        ))}
      </div>
      <span style={{ fontSize: "0.75rem", color: "#64748b" }}>
        Clique no microfone para parar
      </span>
    </div>
  );
}
