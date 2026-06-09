import type { TicketChannel } from "./types";

const CHANNELS: TicketChannel[] = ["Email", "Chat", "Phone", "Social media"];

export interface SimulationSample {
  customer_name: string;
  customer_email: string;
  ticket_type: string;
  ticket_priority: string;
  subject: string;
  description: string;
}

export function pickRandomChannel(): TicketChannel {
  return CHANNELS[Math.floor(Math.random() * CHANNELS.length)];
}

export function pickSamples<T>(pool: T[], count: number): T[] {
  const result: T[] = [];
  for (let i = 0; i < count; i++) {
    result.push(pool[Math.floor(Math.random() * pool.length)]);
  }
  return result;
}
