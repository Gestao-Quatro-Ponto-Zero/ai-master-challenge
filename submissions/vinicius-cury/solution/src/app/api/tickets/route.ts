import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

interface RawTicket {
  "Ticket ID": string;
  "Customer Name": string;
  "Customer Email": string;
  "Customer Age": string;
  "Customer Gender": string;
  "Product Purchased": string;
  "Date of Purchase": string;
  "Ticket Type": string;
  "Ticket Subject": string;
  "Ticket Description": string;
  "Ticket Status": string;
  Resolution: string;
  "Ticket Priority": string;
  "Ticket Channel": string;
  "First Response Time": string;
  "Time to Resolution": string;
  "Customer Satisfaction Rating": string;
}

export interface Ticket {
  id: number;
  customerName: string;
  customerAge: number;
  customerGender: string;
  product: string;
  dateOfPurchase: string;
  type: string;
  subject: string;
  status: string;
  priority: string;
  channel: string;
  firstResponseTime: string | null;
  timeToResolution: string | null;
  resolutionDurationHours: number | null;
  csatRating: number | null;
  csatSegment: string | null;
}

function parseCSV(content: string): RawTicket[] {
  const lines = content.split("\n");
  const headers = parseCSVLine(lines[0]);
  const rows: RawTicket[] = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    const values = parseCSVLine(line);
    if (values.length !== headers.length) continue;
    const row: Record<string, string> = {};
    headers.forEach((h, idx) => {
      row[h] = values[idx];
    });
    rows.push(row as unknown as RawTicket);
  }
  return rows;
}

function parseCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (inQuotes) {
      if (char === '"' && line[i + 1] === '"') {
        current += '"';
        i++;
      } else if (char === '"') {
        inQuotes = false;
      } else {
        current += char;
      }
    } else {
      if (char === '"') {
        inQuotes = true;
      } else if (char === ",") {
        result.push(current.trim());
        current = "";
      } else {
        current += char;
      }
    }
  }
  result.push(current.trim());
  return result;
}

let cachedTickets: Ticket[] | null = null;

function loadTickets(): Ticket[] {
  if (cachedTickets) return cachedTickets;

  const csvPath = path.join(process.cwd(), "data", "customer_support_tickets.csv");
  const content = fs.readFileSync(csvPath, "utf-8");
  const raw = parseCSV(content);

  cachedTickets = raw.map((r) => {
    const status = r["Ticket Status"];
    const frt = r["First Response Time"] || null;
    const ttr = r["Time to Resolution"] || null;
    let resolutionDurationHours: number | null = null;

    // Only compute resolution duration for Closed tickets with both timestamps
    if (status === "Closed" && frt && ttr) {
      const frtDate = new Date(frt);
      const ttrDate = new Date(ttr);
      if (!isNaN(frtDate.getTime()) && !isNaN(ttrDate.getTime())) {
        resolutionDurationHours =
          Math.abs(ttrDate.getTime() - frtDate.getTime()) / (1000 * 60 * 60);
      }
    }

    const csatRaw = parseFloat(r["Customer Satisfaction Rating"]);
    const csatRating = isNaN(csatRaw) ? null : csatRaw;
    let csatSegment: string | null = null;
    if (csatRating !== null) {
      if (csatRating >= 4) csatSegment = "Satisfeito";
      else if (csatRating === 3) csatSegment = "Neutro";
      else csatSegment = "Insatisfeito";
    }

    return {
      id: parseInt(r["Ticket ID"]),
      customerName: r["Customer Name"],
      customerAge: parseInt(r["Customer Age"]),
      customerGender: r["Customer Gender"],
      product: r["Product Purchased"],
      dateOfPurchase: r["Date of Purchase"],
      type: r["Ticket Type"],
      subject: r["Ticket Subject"],
      status: r["Ticket Status"],
      priority: r["Ticket Priority"],
      channel: r["Ticket Channel"],
      firstResponseTime: frt,
      timeToResolution: ttr,
      resolutionDurationHours,
      csatRating,
      csatSegment,
    };
  });

  return cachedTickets;
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  let tickets = loadTickets();

  // Apply filters
  const channel = searchParams.get("channel");
  const priority = searchParams.get("priority");
  const type = searchParams.get("type");
  const subject = searchParams.get("subject");
  const status = searchParams.get("status");
  const csatSegment = searchParams.get("csatSegment");

  if (channel) tickets = tickets.filter((t) => t.channel === channel);
  if (priority) tickets = tickets.filter((t) => t.priority === priority);
  if (type) tickets = tickets.filter((t) => t.type === type);
  if (subject) tickets = tickets.filter((t) => t.subject === subject);
  if (status) tickets = tickets.filter((t) => t.status === status);
  if (csatSegment) tickets = tickets.filter((t) => t.csatSegment === csatSegment);

  return NextResponse.json(tickets);
}
