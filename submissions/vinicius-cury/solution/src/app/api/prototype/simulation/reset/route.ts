import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

// Default operators to re-seed after reset
const DEFAULT_OPERATORS = [
  {
    name: "Ana Silva",
    status: "available",
    active_tickets: 0,
    max_capacity: 5,
    specialties: ["Hardware issue", "Network problem"],
    total_resolved: 0,
  },
  {
    name: "Carlos Santos",
    status: "available",
    active_tickets: 0,
    max_capacity: 5,
    specialties: ["Software issue", "Installation support"],
    total_resolved: 0,
  },
  {
    name: "Juliana Lima",
    status: "available",
    active_tickets: 0,
    max_capacity: 6,
    specialties: ["Product recommendation", "Peripheral compatibility", "Backup recovery"],
    total_resolved: 0,
  },
  {
    name: "Maria Oliveira",
    status: "available",
    active_tickets: 0,
    max_capacity: 4,
    specialties: ["Account access", "Password reset", "Data loss"],
    total_resolved: 0,
  },
  {
    name: "Pedro Costa",
    status: "available",
    active_tickets: 0,
    max_capacity: 4,
    specialties: ["Third-party integration", "Storage issue"],
    total_resolved: 0,
  },
];

export async function POST() {
  const supabase = await createClient();

  // Delete in correct order (messages first due to FK)
  const { error: msgError } = await supabase
    .from("messages")
    .delete()
    .neq("id", "00000000-0000-0000-0000-000000000000");

  if (msgError) {
    return NextResponse.json(
      { error: "Erro ao limpar mensagens", details: msgError.message },
      { status: 500 }
    );
  }

  const { error: convError } = await supabase
    .from("conversations")
    .delete()
    .neq("id", "00000000-0000-0000-0000-000000000000");

  if (convError) {
    return NextResponse.json(
      { error: "Erro ao limpar conversas", details: convError.message },
      { status: 500 }
    );
  }

  const { error: simError } = await supabase
    .from("simulation_runs")
    .delete()
    .neq("id", "00000000-0000-0000-0000-000000000000");

  if (simError) {
    return NextResponse.json(
      { error: "Erro ao limpar simulações", details: simError.message },
      { status: 500 }
    );
  }

  // Reset operators: delete all and re-insert defaults
  const { error: opDeleteError } = await supabase
    .from("operators")
    .delete()
    .neq("id", "00000000-0000-0000-0000-000000000000");

  if (opDeleteError) {
    return NextResponse.json(
      { error: "Erro ao limpar operadores", details: opDeleteError.message },
      { status: 500 }
    );
  }

  const { error: opInsertError } = await supabase
    .from("operators")
    .insert(DEFAULT_OPERATORS);

  if (opInsertError) {
    return NextResponse.json(
      { error: "Erro ao recriar operadores", details: opInsertError.message },
      { status: 500 }
    );
  }

  return NextResponse.json({
    message: "Dados do protótipo resetados com sucesso.",
    tables_cleared: ["messages", "conversations", "simulation_runs", "operators"],
    operators_reseeded: true,
  });
}
