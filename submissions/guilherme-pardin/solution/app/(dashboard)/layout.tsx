import { AuthGate } from "@/components/shared/AuthGate";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AuthGate>{children}</AuthGate>;
}
