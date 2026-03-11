export interface MetricsSummary {
  totalPosts: number;
  totalLikes: number;
  totalComments: number;
  totalShares: number;
  totalImpressions: number;
  totalReach: number;
  avgEngagementRate: number;
}

export interface MetricsOverTime {
  date: string;
  likes: number;
  comments: number;
  shares: number;
  impressions: number;
  reach: number;
  engagementRate: number;
}

export interface PostPerformance {
  id: string;
  caption: string | null;
  platform: string;
  publishedAt: string;
  likes: number;
  comments: number;
  shares: number;
  engagementRate: number;
}

export type DateRange = "7d" | "30d" | "90d" | "1y" | "custom";

export type PlatformFilter = "all" | "instagram" | "facebook" | "tiktok" | "twitter" | "youtube" | "linkedin";
