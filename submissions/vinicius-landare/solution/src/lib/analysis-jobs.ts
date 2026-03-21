import fs from "fs";
import path from "path";

/**
 * Sistema de jobs assíncronos para análise de perfil.
 * Jobs rodam em background e o frontend faz polling para acompanhar.
 */

export interface AnalyzedPost {
  url: string;
  description: string;
  type: string;
  likes: number;
  comments: number;
  shares: number;
  views: number;
  engagement_rate: number;
}

export interface AnalysisJob {
  id: string;
  status: "collecting_profile" | "analyzing_posts" | "completed" | "error";
  profile: string;
  platform: string;
  created_at: string;
  updated_at: string;
  total_posts: number;
  analyzed_posts: number;
  posts: AnalyzedPost[];
  summary?: {
    avg_engagement: number;
    avg_views: number;
    avg_likes: number;
    best_post?: AnalyzedPost;
    worst_post?: AnalyzedPost;
  };
  error?: string;
}

const JOBS_PATH = path.join(process.cwd(), "public", "data", "analysis-jobs.json");

function readJobs(): Record<string, AnalysisJob> {
  try {
    return JSON.parse(fs.readFileSync(JOBS_PATH, "utf-8"));
  } catch {
    return {};
  }
}

function writeJobs(jobs: Record<string, AnalysisJob>) {
  fs.writeFileSync(JOBS_PATH, JSON.stringify(jobs, null, 2), "utf-8");
}

export function createJob(profile: string, platform: string): AnalysisJob {
  const jobs = readJobs();
  const id = `job-${Date.now()}`;
  const job: AnalysisJob = {
    id,
    status: "collecting_profile",
    profile,
    platform,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    total_posts: 0,
    analyzed_posts: 0,
    posts: [],
  };
  jobs[id] = job;
  writeJobs(jobs);
  return job;
}

export function updateJob(id: string, update: Partial<AnalysisJob>): AnalysisJob | null {
  const jobs = readJobs();
  if (!jobs[id]) return null;
  Object.assign(jobs[id], update, { updated_at: new Date().toISOString() });
  writeJobs(jobs);
  return jobs[id];
}

export function getJob(id: string): AnalysisJob | null {
  const jobs = readJobs();
  return jobs[id] || null;
}

export function addPostToJob(id: string, post: AnalyzedPost): AnalysisJob | null {
  const jobs = readJobs();
  if (!jobs[id]) return null;
  jobs[id].posts.push(post);
  jobs[id].analyzed_posts = jobs[id].posts.length;
  jobs[id].updated_at = new Date().toISOString();

  // Se terminou todos os posts, calcular summary
  if (jobs[id].analyzed_posts >= jobs[id].total_posts && jobs[id].total_posts > 0) {
    const posts = jobs[id].posts;
    const sorted = [...posts].sort((a, b) => b.engagement_rate - a.engagement_rate);
    jobs[id].summary = {
      avg_engagement: Math.round(posts.reduce((a, p) => a + p.engagement_rate, 0) / posts.length * 100) / 100,
      avg_views: Math.round(posts.reduce((a, p) => a + p.views, 0) / posts.length),
      avg_likes: Math.round(posts.reduce((a, p) => a + p.likes, 0) / posts.length),
      best_post: sorted[0],
      worst_post: sorted[sorted.length - 1],
    };
    jobs[id].status = "completed";
  }

  writeJobs(jobs);
  return jobs[id];
}
