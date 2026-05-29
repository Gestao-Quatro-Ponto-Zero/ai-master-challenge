import { toFile } from "openai";
import { NextRequest } from "next/server";

import { fail, ok, readBody } from "@/lib/api";
import { getOpenAIClient } from "@/lib/openai";
import { startTimer } from "@/lib/observability";

type TranscribeBody = {
  audio_path?: string;
  audio_base64?: string;
};

export async function POST(request: NextRequest) {
  const timer = startTimer();
  const body = await readBody<TranscribeBody>(request);

  if (!body || (!body.audio_path && !body.audio_base64)) {
    return fail("Informe audio_path ou audio_base64", 400);
  }

  const openai = getOpenAIClient();

  if (!openai || !body.audio_base64) {
    timer.done("transcribe_ms_fallback");
    return ok({
      text: "Transcrição de demonstração: cliente relatou dificuldade de acesso e pediu ajuda imediata.",
      latency_ms: 800,
      mode: "fallback",
    });
  }

  try {
    const base64 = body.audio_base64.includes(",") ? body.audio_base64.split(",")[1] : body.audio_base64;
    const buffer = Buffer.from(base64, "base64");

    const file = await toFile(buffer, "ticket-audio.webm", { type: "audio/webm" });
    const transcript = await openai.audio.transcriptions.create({
      model: "whisper-1",
      file,
      response_format: "verbose_json",
    });

    const elapsed = timer.done("transcribe_ms");

    return ok({
      text: transcript.text,
      latency_ms: elapsed,
      mode: "openai",
    });
  } catch (error) {
    return fail("Falha na transcrição de áudio", 500, String(error));
  }
}
