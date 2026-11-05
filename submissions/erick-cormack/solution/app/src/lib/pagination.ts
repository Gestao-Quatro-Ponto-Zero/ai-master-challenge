export const PIPELINE_PAGE_SIZE = 25;

export function paginate<T>(items: T[], requestedPage: number) {
  const totalPages = Math.max(1, Math.ceil(items.length / PIPELINE_PAGE_SIZE));
  const page = Math.min(totalPages, Math.max(1, requestedPage));
  const start = (page - 1) * PIPELINE_PAGE_SIZE;
  return { page, totalPages, start, items: items.slice(start, start + PIPELINE_PAGE_SIZE) };
}