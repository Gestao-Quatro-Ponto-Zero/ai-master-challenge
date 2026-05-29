import OpenAI from "openai";

let singleton: OpenAI | null = null;

export function getOpenAIClient() {
  if (!process.env.OPENAI_API_KEY) {
    return null;
  }

  if (!singleton) {
    singleton = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  }

  return singleton;
}
