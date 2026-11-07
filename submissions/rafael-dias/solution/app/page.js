import { loadData } from "../lib/data.mjs";
import Dashboard from "./dashboard";
export const dynamic = "force-dynamic";
export default async function Page() {
  const data = await loadData();
  return <Dashboard data={data} />;
}
