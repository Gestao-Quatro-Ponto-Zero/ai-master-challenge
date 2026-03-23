interface PageHeaderProps {
  title: string;
  description: string;
}

export function PageHeader({ title, description }: PageHeaderProps) {
  return (
    <div className="border-b bg-background px-6 py-4">
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
}
