import { csv, query } from '@/lib/db'
import type { DiagnosticOverview, Bottleneck, ChannelStats, TypeStats, PriorityStats } from '@/types'

const DS1 = csv('customer_support_tickets.csv')

// Resolution hours: timestamps can be inverted in the dataset, so use ABS
const RESOLUTION_HOURS = `ABS(DATE_DIFF('minute', "First Response Time", "Time to Resolution")) / 60.0`

// ── Cache ─────────────────────────────────────────────────────────────────────

let overviewCache: DiagnosticOverview | null = null
let bottleneckCache: Bottleneck[] | null = null
let channelCache: ChannelStats[] | null = null
let typeCache: TypeStats[] | null = null
let priorityCache: PriorityStats[] | null = null

// ── Queries ───────────────────────────────────────────────────────────────────

export async function getOverview(): Promise<DiagnosticOverview> {
  if (overviewCache) return overviewCache

  const rows = await query<Record<string, number>>(`
    SELECT
      COUNT(*)                                                              AS total,
      COUNT(*) FILTER (WHERE "Ticket Status" = 'Open')                     AS open_count,
      COUNT(*) FILTER (WHERE "Ticket Status" = 'Closed')                   AS closed_count,
      COUNT(*) FILTER (WHERE "Ticket Status" = 'Pending Customer Response') AS pending_count,
      ROUND(AVG(${RESOLUTION_HOURS}) FILTER (
        WHERE "Ticket Status" = 'Closed'
          AND "Time to Resolution" IS NOT NULL
          AND "First Response Time" IS NOT NULL
      ), 1) AS avg_resolution_hours,
      ROUND(AVG("Customer Satisfaction Rating") FILTER (
        WHERE "Ticket Status" = 'Closed'
      ), 2) AS avg_csat
    FROM ${DS1}
  `)

  const r = rows[0]
  overviewCache = {
    totalTickets:        r.total,
    openTickets:         r.open_count,
    closedTickets:       r.closed_count,
    pendingTickets:      r.pending_count,
    avgResolutionHours:  r.avg_resolution_hours,
    avgCsat:             r.avg_csat,
    backlogRate:         Math.round((1 - r.closed_count / r.total) * 100),
  }
  return overviewCache
}

export async function getBottlenecks(): Promise<Bottleneck[]> {
  if (bottleneckCache) return bottleneckCache

  bottleneckCache = await query<Bottleneck>(`
    SELECT
      "Ticket Channel"  AS channel,
      "Ticket Type"     AS type,
      COUNT(*)          AS n,
      ROUND(AVG(${RESOLUTION_HOURS}), 1) AS "avgHours",
      ROUND(AVG("Customer Satisfaction Rating"), 2) AS "avgCsat"
    FROM ${DS1}
    WHERE "Ticket Status" = 'Closed'
      AND "Time to Resolution" IS NOT NULL
      AND "First Response Time" IS NOT NULL
    GROUP BY 1, 2
    ORDER BY "avgHours" DESC
  `)
  return bottleneckCache
}

export async function getChannelStats(): Promise<ChannelStats[]> {
  if (channelCache) return channelCache

  channelCache = await query<ChannelStats>(`
    SELECT
      "Ticket Channel" AS channel,
      COUNT(*) AS total,
      COUNT(*) FILTER (WHERE "Ticket Status" = 'Closed') AS closed,
      ROUND(AVG("Customer Satisfaction Rating") FILTER (WHERE "Ticket Status" = 'Closed'), 2) AS "avgCsat",
      ROUND(AVG(${RESOLUTION_HOURS}) FILTER (
        WHERE "Ticket Status" = 'Closed'
          AND "Time to Resolution" IS NOT NULL
      ), 1) AS "avgHours"
    FROM ${DS1}
    GROUP BY 1
    ORDER BY "avgCsat" ASC
  `)
  return channelCache
}

export async function getTypeStats(): Promise<TypeStats[]> {
  if (typeCache) return typeCache

  typeCache = await query<TypeStats>(`
    SELECT
      "Ticket Type" AS type,
      COUNT(*) AS total,
      COUNT(*) FILTER (WHERE "Ticket Status" = 'Open')                      AS open,
      COUNT(*) FILTER (WHERE "Ticket Status" = 'Closed')                    AS closed,
      COUNT(*) FILTER (WHERE "Ticket Status" = 'Pending Customer Response') AS pending,
      ROUND(AVG("Customer Satisfaction Rating") FILTER (WHERE "Ticket Status" = 'Closed'), 2) AS "avgCsat",
      ROUND(AVG(${RESOLUTION_HOURS}) FILTER (
        WHERE "Ticket Status" = 'Closed'
          AND "Time to Resolution" IS NOT NULL
      ), 1) AS "avgHours"
    FROM ${DS1}
    GROUP BY 1
    ORDER BY total DESC
  `)
  return typeCache
}

export async function getPriorityStats(): Promise<PriorityStats[]> {
  if (priorityCache) return priorityCache

  const ORDER = `CASE "Ticket Priority" WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 WHEN 'Low' THEN 4 END`

  priorityCache = await query<PriorityStats>(`
    SELECT
      "Ticket Priority" AS priority,
      COUNT(*) AS total,
      ROUND(AVG("Customer Satisfaction Rating") FILTER (WHERE "Ticket Status" = 'Closed'), 2) AS "avgCsat",
      ROUND(AVG(${RESOLUTION_HOURS}) FILTER (
        WHERE "Ticket Status" = 'Closed'
          AND "Time to Resolution" IS NOT NULL
      ), 1) AS "avgHours"
    FROM ${DS1}
    GROUP BY 1
    ORDER BY ${ORDER}
  `)
  return priorityCache
}
