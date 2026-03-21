"use client";

import { useEffect, useRef, useState } from "react";

interface Props {
  onClose: () => void;
}

const W = 400;
const H = 500;
const PLATFORM_COUNT = 50;
const PLATFORM_SPACING = 65;
const JUMP_FORCE = -8.5;
const GRAVITY = 0.4;

function createGame() {
  const platforms: { x: number; y: number; w: number; touched: boolean; id: number }[] = [];
  platforms.push({ x: 0, y: H - 15, w: W, touched: true, id: 0 });
  for (let i = 1; i <= PLATFORM_COUNT; i++) {
    platforms.push({
      x: 20 + Math.random() * (W - 100),
      y: H - 15 - i * PLATFORM_SPACING,
      w: 50 + Math.random() * 30,
      touched: false,
      id: i,
    });
  }
  return {
    player: { x: W / 2 - 10, y: H - 35, vx: 0, vy: 0, lastPlatId: -1 },
    platforms,
    camera: 0,
    maxHeight: 0,
    trophyY: H - 15 - PLATFORM_COUNT * PLATFORM_SPACING - 60,
    state: "playing" as "playing" | "won" | "lost",
    keys: new Set<string>(),
  };
}

export function MiniGame({ onClose }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const gameRef = useRef(createGame());
  const [displayState, setDisplayState] = useState<"playing" | "won" | "lost">("playing");
  const [score, setScore] = useState(0);
  const [gameKey, setGameKey] = useState(0);

  function restart() {
    gameRef.current = createGame();
    setDisplayState("playing");
    setScore(0);
    setGameKey(k => k + 1);
  }

  // Keyboard
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      gameRef.current.keys.add(e.key);
      if (e.key === " " || e.key === "ArrowUp" || e.key === "w") e.preventDefault();
    };
    const onKeyUp = (e: KeyboardEvent) => { gameRef.current.keys.delete(e.key); };
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);
    return () => { window.removeEventListener("keydown", onKeyDown); window.removeEventListener("keyup", onKeyUp); };
  }, []);

  // Game loop — restarts when gameKey changes
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let running = true;

    function loop() {
      if (!running || !ctx) return;
      const g = gameRef.current;
      if (g.state !== "playing") { requestAnimationFrame(loop); return; }

      const p = g.player;

      // Input
      if (g.keys.has("ArrowLeft") || g.keys.has("a")) p.vx = -4;
      else if (g.keys.has("ArrowRight") || g.keys.has("d")) p.vx = 4;
      else p.vx *= 0.82;

      p.x += p.vx;
      if (p.x < -20) p.x = W;
      if (p.x > W) p.x = -20;

      p.vy += GRAVITY;
      p.y += p.vy;

      // Colisão plataformas — só pula uma vez por plataforma
      if (p.vy > 0) {
        for (const plat of g.platforms) {
          const py = plat.y - g.camera;
          if (
            p.x + 20 > plat.x &&
            p.x < plat.x + plat.w &&
            p.y + 20 >= py &&
            p.y + 20 <= py + 10 &&
            p.lastPlatId !== plat.id
          ) {
            p.y = py - 20;
            p.vy = JUMP_FORCE;
            p.lastPlatId = plat.id;
            plat.touched = true;
          }
        }
      }
      // Reset lastPlatId quando está no ar caindo livremente
      if (p.vy > 2) p.lastPlatId = -1;

      // Camera
      const worldY = g.camera + p.y;
      if (worldY < g.maxHeight) g.maxHeight = worldY;
      const target = g.camera + p.y - H * 0.4;
      if (target < g.camera) g.camera += (target - g.camera) * 0.1;

      setScore(Math.max(0, Math.floor(-g.maxHeight / 10)));

      // Morte
      if (p.y > H + 50) {
        g.state = "lost";
        setDisplayState("lost");
        return;
      }

      // Vitória
      const tsy = g.trophyY - g.camera;
      if (p.y < tsy + 40 && p.y + 20 > tsy && p.x > W / 2 - 30 && p.x < W / 2 + 30) {
        g.state = "won";
        setDisplayState("won");
        return;
      }

      // ===== DRAW =====
      const grad = ctx.createLinearGradient(0, 0, 0, H);
      grad.addColorStop(0, "#0a1220");
      grad.addColorStop(0.5, "#0F1B2D");
      grad.addColorStop(1, "#1A2D47");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, W, H);

      // Estrelas
      ctx.fillStyle = "rgba(255,255,255,0.35)";
      for (let i = 0; i < 50; i++) {
        const sx = (i * 97 + 30) % W;
        const sy = ((i * 137 + 50) + g.camera * 0.08) % H;
        ctx.fillRect(sx, sy, 1.2, 1.2);
      }

      // Plataformas
      for (const plat of g.platforms) {
        const py = plat.y - g.camera;
        if (py > H + 20 || py < -20) continue;
        ctx.fillStyle = plat.touched ? "#E8734A" : "#2a3f5f";
        ctx.beginPath();
        ctx.roundRect(plat.x, py, plat.w, 7, 3);
        ctx.fill();
        ctx.fillStyle = plat.touched ? "#f4a261" : "#3a5577";
        ctx.fillRect(plat.x + 3, py, plat.w - 6, 2);
      }

      // Troféu
      if (tsy > -60 && tsy < H + 60) {
        const tx = W / 2 - 15;
        const glow = ctx.createRadialGradient(tx + 15, tsy + 20, 5, tx + 15, tsy + 20, 30);
        glow.addColorStop(0, "rgba(255, 215, 0, 0.3)");
        glow.addColorStop(1, "rgba(255, 215, 0, 0)");
        ctx.fillStyle = glow;
        ctx.fillRect(tx - 20, tsy - 15, 70, 70);
        ctx.fillStyle = "#FFD700";
        ctx.beginPath();
        ctx.moveTo(tx + 5, tsy + 5); ctx.lineTo(tx + 25, tsy + 5);
        ctx.lineTo(tx + 22, tsy + 25); ctx.lineTo(tx + 8, tsy + 25);
        ctx.closePath(); ctx.fill();
        ctx.fillStyle = "#DAA520";
        ctx.fillRect(tx + 10, tsy + 25, 10, 4);
        ctx.fillRect(tx + 7, tsy + 29, 16, 4);
        ctx.strokeStyle = "#FFD700"; ctx.lineWidth = 2.5;
        ctx.beginPath(); ctx.arc(tx + 3, tsy + 15, 5, -Math.PI / 2, Math.PI / 2); ctx.stroke();
        ctx.beginPath(); ctx.arc(tx + 27, tsy + 15, 5, Math.PI / 2, -Math.PI / 2); ctx.stroke();
        ctx.fillStyle = "#0F1B2D"; ctx.font = "bold 9px sans-serif"; ctx.textAlign = "center";
        ctx.fillText("G4", tx + 15, tsy + 20); ctx.textAlign = "start";
      }

      // Jogador
      const px = p.x, py = p.y;
      ctx.fillStyle = "#E8734A";
      ctx.beginPath(); ctx.roundRect(px + 4, py + 6, 12, 12, 3); ctx.fill();
      ctx.fillStyle = "#FCD5CE";
      ctx.beginPath(); ctx.arc(px + 10, py + 3, 6, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = "#0F1B2D";
      ctx.fillRect(px + 7, py + 1, 2, 2.5); ctx.fillRect(px + 11, py + 1, 2, 2.5);
      ctx.fillStyle = "#1A2D47";
      if (p.vy < 0) { ctx.fillRect(px + 6, py + 18, 3, 2); ctx.fillRect(px + 11, py + 18, 3, 2); }
      else { ctx.fillRect(px + 6, py + 18, 3, 4); ctx.fillRect(px + 11, py + 18, 3, 4); }

      // Trail
      if (p.vy < -4) {
        ctx.fillStyle = `rgba(232, 115, 74, 0.25)`;
        for (let t = 1; t <= 2; t++) {
          ctx.beginPath(); ctx.arc(px + 10, py + 22 + t * 7, 3 - t, 0, Math.PI * 2); ctx.fill();
        }
      }

      // Barra de progresso
      const totalH = Math.abs(g.trophyY);
      const progress = Math.min(1, Math.abs(g.maxHeight) / totalH);
      ctx.fillStyle = "rgba(255,255,255,0.05)";
      ctx.fillRect(W - 8, 20, 4, H - 40);
      ctx.fillStyle = "#E8734A";
      ctx.fillRect(W - 8, 20 + (H - 40) * (1 - progress), 4, (H - 40) * progress);

      requestAnimationFrame(loop);
    }

    requestAnimationFrame(loop);
    return () => { running = false; };
  }, [gameKey]);

  return (
    <div className="bg-[#0F1B2D] rounded-2xl border border-[#E8734A]/20 p-3 relative">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <span className="text-[10px] text-white/40">G4 Jump</span>
          <span className="text-xs text-[#E8734A] font-mono font-bold">{score}m</span>
        </div>
        <button onClick={onClose} className="text-white/30 hover:text-white/60 text-xs">fechar</button>
      </div>

      <canvas ref={canvasRef} width={W} height={H} className="w-full rounded-xl" style={{ maxWidth: 400, margin: "0 auto", display: "block" }} />

      {displayState === "won" && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/70 rounded-2xl">
          <div className="text-center">
            <p className="text-3xl mb-2">🏆</p>
            <p className="text-sm font-bold text-[#FFD700]">Troféu G4!</p>
            <p className="text-xs text-white/50 mb-3">{score}m</p>
            <button onClick={restart} className="px-4 py-2 bg-[#E8734A] text-white text-xs rounded-lg hover:bg-[#d4653f]">Jogar novamente</button>
          </div>
        </div>
      )}

      {displayState === "lost" && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/70 rounded-2xl">
          <div className="text-center">
            <p className="text-sm font-bold text-red-400 mb-1">Caiu!</p>
            <p className="text-xs text-white/50 mb-3">{score}m</p>
            <button onClick={restart} className="px-4 py-2 bg-[#E8734A] text-white text-xs rounded-lg hover:bg-[#d4653f]">Tentar novamente</button>
          </div>
        </div>
      )}

      <p className="text-[9px] text-white/20 text-center mt-2">Setas ou A/D para mover · Suba até o troféu G4</p>
    </div>
  );
}
