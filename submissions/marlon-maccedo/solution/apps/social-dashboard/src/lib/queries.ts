import { query, csv } from './db'
import type {
  SocialOverview,
  PlatformEngagement,
  ContentTypeEngagement,
  CategoryEngagement,
  HeatmapCell,
  CreatorTierRow,
  SponsorComparison,
  SponsorCategoryRow,
  DisclosureRow,
  AudienceAgeRow,
  AudienceGenderRow,
  AgeEngagementRow,
} from '@/types'

const POSTS = csv('social_media_dataset.csv')

export async function getOverview(): Promise<SocialOverview> {
  const rows = await query<SocialOverview>(`
    SELECT
      COUNT(*)::INTEGER AS "totalPosts",
      SUM(views)::DOUBLE AS "totalViews",
      ROUND(AVG((likes + shares + comments_count)::DOUBLE / NULLIF(views, 0)) * 100, 2) AS "avgEngagementRate",
      COUNT(*) FILTER (WHERE is_sponsored = 'TRUE')::INTEGER AS "sponsoredCount",
      COUNT(*) FILTER (WHERE is_sponsored = 'FALSE')::INTEGER AS "organicCount"
    FROM ${POSTS}
  `)
  return rows[0]
}

export async function getEngagementByPlatform(): Promise<PlatformEngagement[]> {
  return query<PlatformEngagement>(`
    SELECT
      platform,
      ROUND(AVG((likes + shares + comments_count)::DOUBLE / NULLIF(views, 0)) * 100, 2) AS "avgEngagementRate",
      COUNT(*)::INTEGER AS "totalPosts"
    FROM ${POSTS}
    GROUP BY platform
    ORDER BY "avgEngagementRate" DESC
  `)
}

export async function getEngagementByContentType(): Promise<ContentTypeEngagement[]> {
  return query<ContentTypeEngagement>(`
    SELECT
      content_type AS "contentType",
      ROUND(AVG((likes + shares + comments_count)::DOUBLE / NULLIF(views, 0)) * 100, 2) AS "avgEngagementRate",
      COUNT(*)::INTEGER AS "totalPosts"
    FROM ${POSTS}
    GROUP BY content_type
    ORDER BY "avgEngagementRate" DESC
  `)
}

export async function getEngagementByCategory(): Promise<CategoryEngagement[]> {
  return query<CategoryEngagement>(`
    SELECT
      content_category AS "category",
      ROUND(AVG((likes + shares + comments_count)::DOUBLE / NULLIF(views, 0)) * 100, 2) AS "avgEngagementRate",
      COUNT(*)::INTEGER AS "totalPosts"
    FROM ${POSTS}
    GROUP BY content_category
    ORDER BY "avgEngagementRate" DESC
  `)
}

export async function getHeatmapData(): Promise<HeatmapCell[]> {
  return query<HeatmapCell>(`
    SELECT
      platform,
      content_type AS "contentType",
      ROUND(AVG((likes + shares + comments_count)::DOUBLE / NULLIF(views, 0)) * 100, 2) AS "avgEngagementPct",
      COUNT(*)::INTEGER AS "totalPosts"
    FROM ${POSTS}
    GROUP BY platform, content_type
    ORDER BY platform, content_type
  `)
}

export async function getCreatorTierAnalysis(): Promise<CreatorTierRow[]> {
  return query<CreatorTierRow>(`
    SELECT
      CASE
        WHEN follower_count < 10000   THEN 'nano (<10K)'
        WHEN follower_count < 100000  THEN 'micro (10K-100K)'
        WHEN follower_count < 1000000 THEN 'macro (100K-1M)'
        ELSE                               'mega (>1M)'
      END AS "tier",
      ROUND(AVG((likes + shares + comments_count)::DOUBLE / NULLIF(views, 0)) * 100, 2) AS "avgEngagementRate",
      COUNT(*)::INTEGER AS "totalPosts",
      ROUND(AVG(follower_count)) AS "avgFollowers"
    FROM ${POSTS}
    GROUP BY "tier"
    ORDER BY "avgEngagementRate" DESC
  `)
}

export async function getSponsorshipComparison(): Promise<SponsorComparison> {
  const rows = await query<{
    group: string
    avgEngagementRate: number
    avgViews: number
    avgLikes: number
    avgShares: number
    cnt: number
  }>(`
    SELECT
      CASE WHEN is_sponsored = 'TRUE' THEN 'sponsored' ELSE 'organic' END AS "group",
      ROUND(AVG((likes + shares + comments_count)::DOUBLE / NULLIF(views, 0)) * 100, 2) AS "avgEngagementRate",
      ROUND(AVG(views)) AS "avgViews",
      ROUND(AVG(likes)) AS "avgLikes",
      ROUND(AVG(shares)) AS "avgShares",
      COUNT(*)::INTEGER AS cnt
    FROM ${POSTS}
    GROUP BY "group"
  `)

  const organic   = rows.find(r => r.group === 'organic')
  const sponsored = rows.find(r => r.group === 'sponsored')

  return {
    avgEngagementOrganic:   organic?.avgEngagementRate ?? 0,
    avgEngagementSponsored: sponsored?.avgEngagementRate ?? 0,
    avgViewsOrganic:        organic?.avgViews ?? 0,
    avgViewsSponsored:      sponsored?.avgViews ?? 0,
    avgLikesOrganic:        organic?.avgLikes ?? 0,
    avgLikesSponsored:      sponsored?.avgLikes ?? 0,
    avgSharesOrganic:       organic?.avgShares ?? 0,
    avgSharesSponsored:     sponsored?.avgShares ?? 0,
    organicCount:           organic?.cnt ?? 0,
    sponsoredCount:         sponsored?.cnt ?? 0,
  }
}

export async function getSponsorshipByCategory(): Promise<SponsorCategoryRow[]> {
  return query<SponsorCategoryRow>(`
    SELECT
      COALESCE(sponsor_category, 'none') AS "sponsorCategory",
      ROUND(AVG((likes + shares + comments_count)::DOUBLE / NULLIF(views, 0)) * 100, 2) AS "avgEngagementRate",
      COUNT(*)::INTEGER AS "totalPosts"
    FROM ${POSTS}
    WHERE is_sponsored = 'TRUE'
    GROUP BY sponsor_category
    ORDER BY "avgEngagementRate" DESC
  `)
}

export async function getDisclosureTypeAnalysis(): Promise<DisclosureRow[]> {
  return query<DisclosureRow>(`
    SELECT
      COALESCE(disclosure_type, 'none') AS "disclosureType",
      ROUND(AVG((likes + shares + comments_count)::DOUBLE / NULLIF(views, 0)) * 100, 2) AS "avgEngagementRate",
      COUNT(*)::INTEGER AS "totalPosts"
    FROM ${POSTS}
    WHERE is_sponsored = 'TRUE'
    GROUP BY disclosure_type
    ORDER BY "totalPosts" DESC
  `)
}

export async function getSponsoredHeatmap(type: 'TRUE' | 'FALSE'): Promise<HeatmapCell[]> {
  return query<HeatmapCell>(`
    SELECT
      platform,
      content_type AS "contentType",
      ROUND(AVG((likes + shares + comments_count)::DOUBLE / NULLIF(views, 0)) * 100, 2) AS "avgEngagementPct",
      COUNT(*)::INTEGER AS "totalPosts"
    FROM ${POSTS}
    WHERE is_sponsored = '${type}'
    GROUP BY platform, content_type
    ORDER BY platform, content_type
  `)
}

export async function getAudienceByPlatform(): Promise<AudienceAgeRow[]> {
  return query<AudienceAgeRow>(`
    SELECT
      platform,
      audience_age_distribution AS "ageGroup",
      COUNT(*)::INTEGER AS "totalPosts"
    FROM ${POSTS}
    WHERE audience_age_distribution IS NOT NULL
      AND audience_age_distribution != 'unknown'
    GROUP BY platform, audience_age_distribution
    ORDER BY platform, "totalPosts" DESC
  `)
}

export async function getGenderByPlatform(): Promise<AudienceGenderRow[]> {
  return query<AudienceGenderRow>(`
    SELECT
      platform,
      audience_gender_distribution AS "gender",
      COUNT(*)::INTEGER AS "totalPosts"
    FROM ${POSTS}
    WHERE audience_gender_distribution IS NOT NULL
      AND audience_gender_distribution != 'unknown'
    GROUP BY platform, audience_gender_distribution
    ORDER BY platform, "totalPosts" DESC
  `)
}

export async function getEngagementByAgeGroup(): Promise<AgeEngagementRow[]> {
  return query<AgeEngagementRow>(`
    SELECT
      audience_age_distribution AS "ageGroup",
      ROUND(AVG((likes + shares + comments_count)::DOUBLE / NULLIF(views, 0)) * 100, 2) AS "avgEngagementRate",
      COUNT(*)::INTEGER AS "totalPosts"
    FROM ${POSTS}
    WHERE audience_age_distribution IS NOT NULL
      AND audience_age_distribution != 'unknown'
    GROUP BY audience_age_distribution
    ORDER BY "avgEngagementRate" DESC
  `)
}
