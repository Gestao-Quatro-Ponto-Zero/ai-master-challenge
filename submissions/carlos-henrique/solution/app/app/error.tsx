"use client";

import { ErrorState } from "@/components/ui";

export default function ErrorPage({ reset }: { error: Error; reset: () => void }) {
  return <ErrorState title="This section could not load" message="A required local artifact is unavailable or invalid." action={reset} />;
}
