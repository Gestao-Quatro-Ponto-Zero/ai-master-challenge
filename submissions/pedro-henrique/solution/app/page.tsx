import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export default async function Home() {
  const cookieStore = await cookies();
  const role = cookieStore.get("demo-role")?.value;

  if (role === "admin") {
    redirect("/admin");
  }

  if (role === "customer") {
    redirect("/customer/new");
  }

  redirect("/login");
}
