"""Ligação contínua no canal telefone (Jó, 2026-11-16: "manter o tempo todo ligado a escuta e resposta sem eu ter que
ficar mandando audio como whats").

O microfone fica aberto do Ligar ao Desligar. No navegador, um detector de fala por energia percebe quando o cliente
começa e termina de falar (pausa de 0,8 s) e manda só aquele trecho, em WAV 16 kHz, para a página. A página transcreve
nesta máquina, a IA responde, a voz da atendente toca e a escuta volta sozinha. Enquanto a atendente fala, a escuta
fica pausada (meia via), para a própria voz dela não voltar como fala do cliente.

O áudio só existe na memória do navegador e do processo; nada é gravado nem enviado à IA externa.
"""
from __future__ import annotations

import base64

import streamlit as st

# Parâmetros do detector de fala (navegador). Valores ajustados na bateria com microfone falso de 2026-11-16.
PAUSA_FIM_MS = 800        # silêncio que fecha a fala do cliente
FALA_MINIMA_MS = 350      # abaixo disso é ruído (tosse, clique)
FALA_MAXIMA_S = 25        # fala longa é enviada assim mesmo (o servidor aceita até 60 s)
# A resposta leva de 6 a 8 s nesta CPU (transcrição 3,5 s, IA 2,1 s, voz 1 s; medido em 2026-11-16). Com o gatilho em
# 1,5 s a frase de espera tocava em quase toda resposta e soava robótica (Jó, 2026-11-16 21:16 BRT). Agora ela só toca
# depois de 4 s de silêncio e no máximo uma vez a cada 3 falas do cliente, variando a frase.
ESPERA_MS = 4000
ESPERA_A_CADA = 3
FRASES_ESPERA = ("Hum, deixa eu ver aqui.", "Só um segundinho.", "Tá, já te falo.")

HTML = """
<div class="lig">
  <span class="ponto"></span>
  <span class="estado">Conectando o microfone...</span>
  <button class="desligar" type="button">Desligar</button>
</div>
<div class="nivel"><div class="barra"></div></div>
"""

CSS = """
.lig { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 12px;
       background: var(--st-secondary-background-color); font-family: var(--st-font); }
.ponto { width: 12px; height: 12px; border-radius: 50%; background: #94A3B8; flex: none; }
.estado { flex: 1; color: var(--st-text-color); font-size: 15px; }
.desligar { background: #B91C1C; color: #fff; border: 0; border-radius: 8px; padding: 8px 16px; font-size: 14px;
            cursor: pointer; min-height: 40px; }
.desligar:disabled { opacity: .45; cursor: default; }
.nivel { height: 4px; margin-top: 6px; border-radius: 2px; background: var(--st-secondary-background-color);
         overflow: hidden; }
.barra { height: 100%; width: 0%; background: #1E40AF; transition: width 80ms linear; }
.ouvindo .ponto { background: #15803D; animation: pulso 1.4s ease-in-out infinite; }
.falando .ponto { background: #1E40AF; }
.pensando .ponto { background: #B45309; animation: pulso .8s ease-in-out infinite; }
.atendente .ponto { background: #7C3AED; }
.encerrada .ponto { background: #64748B; }
@keyframes pulso { 50% { opacity: .35; } }
@media (prefers-reduced-motion: reduce) { .ponto { animation: none !important; } }
"""

JS = """
const ESTADOS = {
  ouvindo: 'Ouvindo. Pode falar.',
  falando: 'Você está falando...',
  pensando: 'Entendendo e respondendo...',
  atendente: 'Atendente falando...',
  encerrada: 'Ligação encerrada.',
  erro: 'Sem acesso ao microfone. Libere o microfone no navegador ou digite abaixo.',
};

function estado(S, nome) {
  S.estado = nome;
  S.caixa.className = 'lig ' + nome;
  S.texto.textContent = ESTADOS[nome];
  S.botao.disabled = nome === 'encerrada' || nome === 'erro';
}

function wavBase64(amostras, taxa) {
  const alvo = 16000, fator = taxa / alvo, n = Math.floor(amostras.length / fator);
  const buf = new ArrayBuffer(44 + n * 2), v = new DataView(buf);
  const txt = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
  txt(0, 'RIFF'); v.setUint32(4, 36 + n * 2, true); txt(8, 'WAVE'); txt(12, 'fmt ');
  v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
  v.setUint32(24, alvo, true); v.setUint32(28, alvo * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true);
  txt(36, 'data'); v.setUint32(40, n * 2, true);
  for (let i = 0; i < n; i++) {
    const ini = Math.floor(i * fator), fim = Math.max(ini + 1, Math.floor((i + 1) * fator));
    let soma = 0; for (let j = ini; j < fim; j++) soma += amostras[j];
    const x = Math.max(-1, Math.min(1, soma / (fim - ini)));
    v.setInt16(44 + i * 2, x < 0 ? x * 0x8000 : x * 0x7fff, true);
  }
  let bin = ''; const bytes = new Uint8Array(buf);
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(bin);
}

async function abrirMicrofone(S) {
  try {
    S.stream = await navigator.mediaDevices.getUserMedia({ audio: {
      echoCancellation: true, noiseSuppression: true, autoGainControl: true, channelCount: 1 } });
  } catch (e) { estado(S, 'erro'); return; }
  S.ctx = new (window.AudioContext || window.webkitAudioContext)();
  const fonte = S.ctx.createMediaStreamSource(S.stream);
  S.proc = S.ctx.createScriptProcessor(2048, 1, 1);
  const msPorBloco = 2048 / S.ctx.sampleRate * 1000;
  S.proc.onaudioprocess = (ev) => {
    const x = ev.inputBuffer.getChannelData(0);
    let q = 0; for (let i = 0; i < x.length; i++) q += x[i] * x[i];
    const rms = Math.sqrt(q / x.length);
    S.barra.style.width = Math.min(100, rms * 900) + '%';
    if (S.estado !== 'ouvindo' && S.estado !== 'falando') return;
    if (performance.now() < S.surdoAte) return;
    const bloco = new Float32Array(x);
    const inicio = Math.max(0.012, S.ruido * 3), fimLim = Math.max(0.008, S.ruido * 2);
    if (S.estado === 'ouvindo') {
      S.antes.push(bloco); if (S.antes.length > 6) S.antes.shift();     // ~250 ms antes da fala
      if (rms > inicio) { S.acima += msPorBloco; } else { S.acima = 0; S.ruido = S.ruido * 0.95 + rms * 0.05; }
      if (S.acima >= 120) { S.fala = S.antes.slice(); S.antes = []; S.silencio = 0; S.durFala = 0; estado(S, 'falando'); }
      return;
    }
    S.fala.push(bloco); S.durFala += msPorBloco;
    S.silencio = rms < fimLim ? S.silencio + msPorBloco : 0;
    if (S.silencio >= S.cfg.pausa || S.durFala >= S.cfg.maxima * 1000) {
      const util = S.durFala - S.silencio;
      const partes = S.fala; S.fala = [];
      if (util < S.cfg.minima) { estado(S, 'ouvindo'); return; }
      let total = 0; partes.forEach(p => total += p.length);
      const tudo = new Float32Array(total); let o = 0; partes.forEach(p => { tudo.set(p, o); o += p.length; });
      S.enviado += 1; S.aguardando = S.enviado;
      estado(S, 'pensando');
      clearTimeout(S.timerEspera);
      S.timerEspera = setTimeout(() => {
        if (S.estado !== 'pensando' || !S.espera.length) return;
        if (S.ultimaEspera && S.enviado - S.ultimaEspera < S.cfg.esperaACada) return;
        S.ultimaEspera = S.enviado;
        S.audioEspera.src = 'data:audio/wav;base64,' + S.espera[S.nEspera++ % S.espera.length];
        S.audioEspera.play().catch(() => {});
      }, S.cfg.espera);
      S.enviar('fala', { seq: S.enviado, wav: wavBase64(tudo, S.ctx.sampleRate) });
    }
  };
  fonte.connect(S.proc); S.proc.connect(S.ctx.destination);
  if (S.estado === 'conectando') estado(S, S.pendenteFala ? 'atendente' : 'ouvindo');
  if (S.pendenteFala) { const f = S.pendenteFala; S.pendenteFala = null; tocar(S, f); }
}

function tocar(S, fala) {
  if (!S.stream) { S.pendenteFala = fala; return; }
  clearTimeout(S.timerEspera);
  if (!S.audioEspera.paused && !S.audioEspera.ended) {           // termina a frase de espera antes da resposta
    S.audioEspera.onended = () => { S.audioEspera.onended = null; tocar(S, fala); };
    return;
  }
  estado(S, 'atendente');
  S.audio.src = 'data:audio/wav;base64,' + fala;
  S.audio.play().catch(() => voltar(S));
}

function voltar(S) {
  clearTimeout(S.timerEspera);
  if (S.encerrar) { fechar(S); return; }
  S.surdoAte = performance.now() + 300;                              // cauda do alto-falante
  estado(S, 'ouvindo');
}

function fechar(S) {
  if (S.fechada) return;
  S.fechada = true;
  clearTimeout(S.timerEspera);
  try { S.audioEspera.pause(); } catch (e) {}
  try { S.proc && S.proc.disconnect(); } catch (e) {}
  try { S.stream && S.stream.getTracks().forEach(t => t.stop()); } catch (e) {}
  try { S.ctx && S.ctx.close(); } catch (e) {}
  S.barra.style.width = '0%';
  estado(S, 'encerrada');
}

export default function (component) {
  const { data, setTriggerValue, parentElement } = component;
  let S = parentElement.__ligacao;
  if (!S) {
    S = parentElement.__ligacao = {
      caixa: parentElement.querySelector('.lig'), texto: parentElement.querySelector('.estado'),
      botao: parentElement.querySelector('.desligar'), barra: parentElement.querySelector('.barra'),
      audio: new Audio(), estado: 'conectando', ruido: 0.004, acima: 0, antes: [], fala: [], silencio: 0,
      durFala: 0, surdoAte: 0, enviado: 0, aguardando: 0, falaTocada: 0, cfg: data.cfg,
      audioEspera: new Audio(), espera: data.espera || [], nEspera: 0, ultimaEspera: 0, timerEspera: null,
    };
    S.audio.onended = () => voltar(S);
    S.botao.onclick = () => { S.encerrar = true; S.audio.pause(); fechar(S); S.enviar('desligar', true); };
    abrirMicrofone(S);
  }
  S.enviar = setTriggerValue;
  if (data.encerrada) S.encerrar = true;
  if (data.fala && data.fala_id > S.falaTocada) {
    S.falaTocada = data.fala_id;
    tocar(S, data.fala);
  } else if (data.processado >= S.aguardando && S.estado === 'pensando') {
    voltar(S);                                                       // fala sem resposta (áudio recusado)
  } else if (S.encerrar && S.estado !== 'atendente') {
    fechar(S);
  }
  return () => fechar(S);
}
"""

_componente = st.components.v2.component("ligacao_g4", html=HTML, css=CSS, js=JS)


def ligacao(fala_wav: bytes | None, fala_id: int, processado: int, encerrada: bool, key: str,
            espera: list[bytes] | None = None):
    """Monta a ligação e devolve o resultado com as trilhas `fala` ({seq, wav}) e `desligar`."""
    dados = {"fala": base64.b64encode(fala_wav).decode() if fala_wav else None, "fala_id": fala_id,
             "processado": processado, "encerrada": encerrada,
             "espera": [base64.b64encode(w).decode() for w in espera or [] if w],
             "cfg": {"pausa": PAUSA_FIM_MS, "minima": FALA_MINIMA_MS, "maxima": FALA_MAXIMA_S, "espera": ESPERA_MS,
                     "esperaACada": ESPERA_A_CADA}}
    return _componente(data=dados, key=key, on_fala_change=lambda: None, on_desligar_change=lambda: None)


def audio_da_fala(valor) -> tuple[int, bytes] | None:
    """Fala enviada pelo navegador: (sequência, WAV). Valor fora do formato é ignorado."""
    if not isinstance(valor, dict) or not isinstance(valor.get("wav"), str):
        return None
    try:
        return int(valor.get("seq", 0)), base64.b64decode(valor["wav"], validate=True)
    except (ValueError, TypeError):
        return None


__all__ = ["ligacao", "audio_da_fala", "ESPERA_A_CADA", "ESPERA_MS", "FRASES_ESPERA", "PAUSA_FIM_MS", "FALA_MINIMA_MS", "FALA_MAXIMA_S"]
