import { NextRequest } from "next/server";

import type { Role, SessionUser } from "@/lib/types";

export function getDemoUser(request: NextRequest): SessionUser | null {
  const role = request.cookies.get("demo-role")?.value as Role | undefined;
  const id = request.cookies.get("demo-user-id")?.value;
  const email = request.cookies.get("demo-email")?.value;

  if (!role || (role !== "admin" && role !== "customer")) {
    return null;
  }

  return {
    id: id ?? (role === "admin" ? "demo-admin-001" : "demo-customer-001"),
    email: email ?? (role === "admin" ? "admin@g4.local" : "customer@g4.local"),
    role,
  };
}

export function isAdmin(user: SessionUser | null) {
  return user?.role === "admin";
}
