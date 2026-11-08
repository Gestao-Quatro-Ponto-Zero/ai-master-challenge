import { Dashboard } from "@/components/Dashboard";
import { getPipeline } from "@/lib/data";

export default async function Page() {
  const data = await getPipeline();
  return <Dashboard data={data} />;
}
