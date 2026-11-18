import { redirect } from "next/navigation";

/**
 * Screen 1 (the three claims) left the app in D49: those answers now come from a deck built from
 * marked charts. Old links and marks that point here land on the overview.
 */
export default function Tela1() {
  redirect("/");
}
