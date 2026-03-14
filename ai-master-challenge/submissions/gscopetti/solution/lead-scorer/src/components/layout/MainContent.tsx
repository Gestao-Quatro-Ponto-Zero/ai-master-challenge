import type { ReactNode } from 'react';

interface MainContentProps {
  children: ReactNode;
}

export function MainContent({ children }: MainContentProps) {
  return (
    <main className="flex-1 overflow-auto">
      <div className="p-6 max-w-7xl mx-auto">
        {children}
      </div>
    </main>
  );
}
