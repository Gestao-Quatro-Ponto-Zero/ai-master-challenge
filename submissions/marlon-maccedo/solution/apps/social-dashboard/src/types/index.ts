export interface SocialOverview {
  totalPosts: number
  totalViews: number
  avgEngagementRate: number
  sponsoredCount: number
  organicCount: number
}

export interface PlatformEngagement {
  platform: string
  avgEngagementRate: number
  totalPosts: number
}

export interface ContentTypeEngagement {
  contentType: string
  avgEngagementRate: number
  totalPosts: number
}

export interface CategoryEngagement {
  category: string
  avgEngagementRate: number
  totalPosts: number
}

export interface HeatmapCell {
  platform: string
  contentType: string
  avgEngagementPct: number
  totalPosts: number
}

export interface CreatorTierRow {
  tier: string
  avgEngagementRate: number
  totalPosts: number
  avgFollowers: number
}

export interface SponsorComparison {
  avgEngagementOrganic: number
  avgEngagementSponsored: number
  avgViewsOrganic: number
  avgViewsSponsored: number
  avgLikesOrganic: number
  avgLikesSponsored: number
  avgSharesOrganic: number
  avgSharesSponsored: number
  organicCount: number
  sponsoredCount: number
}

export interface SponsorCategoryRow {
  sponsorCategory: string
  avgEngagementRate: number
  totalPosts: number
}

export interface DisclosureRow {
  disclosureType: string
  avgEngagementRate: number
  totalPosts: number
}

export interface AudienceAgeRow {
  platform: string
  ageGroup: string
  totalPosts: number
}

export interface AudienceGenderRow {
  platform: string
  gender: string
  totalPosts: number
}

export interface AgeEngagementRow {
  ageGroup: string
  avgEngagementRate: number
  totalPosts: number
}

// ── Pre-computed analysis (from Python script) ────────────────────────────────

export interface TemporalRow {
  month: string
  avgEngagementRate: number
  totalPosts: number
  totalViews: number
}

export interface HashtagRow {
  hashtag: string
  avgEngagementRate: number
  totalPosts: number
}

export interface ContentLengthRow {
  lengthBucket: string
  avgEngagementRate: number
  totalPosts: number
  avgContentLength: number
}

export interface LanguagePerfRow {
  language: string
  avgEngagementRate: number
  totalPosts: number
}

export interface PostingByDayRow {
  day_of_week: string
  avgEngagementRate: number
  totalPosts: number
}

export interface CreatorEfficiencyRow {
  tier: string
  avgEngagementRate: number
  avgEngPer1KFollowers: number
  totalPosts: number
  avgFollowers: number
}

export interface LocationPerfRow {
  location: string
  avgEngagementRate: number
  totalPosts: number
}

export interface PlatformDayRow {
  platform: string
  day_of_week: string
  avgEngagementRate: number
  totalPosts: number
}

export interface SocialAnalysisOutput {
  temporal:           TemporalRow[]
  topHashtags:        HashtagRow[]
  contentLength:      ContentLengthRow[]
  languagePerf:       LanguagePerfRow[]
  postingByDay:       PostingByDayRow[]
  creatorEfficiency:  CreatorEfficiencyRow[]
  locationPerf:       LocationPerfRow[]
  platformDayHeatmap: PlatformDayRow[]
}
