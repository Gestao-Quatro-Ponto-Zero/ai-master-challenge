import { NextResponse } from "next/server";
import { generateChatReply, generateDraftReply } from "@/lib/openai";
import { createServerClient } from "@/lib/supabase/server";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { ticket_id, message, mode } = body as {
      ticket_id: string;
      message?: string;
      mode: "reply" | "draft";
    };

    const supabase = createServerClient();
    const { data: ticket, error } = await supabase
      .from("tickets")
      .select("*, ticket_messages(*)")
      .eq("id", ticket_id)
      .single();

    if (error || !ticket) {
      return NextResponse.json({ error: "Ticket não encontrado." }, { status: 404 });
    }

    const topic = ticket.topic_group_llm ?? ticket.topic_group;
    let articlesQuery = supabase.from("knowledge_articles").select("title, content, topic_group");
    if (topic) {
      articlesQuery = articlesQuery.or(`topic_group.eq.${topic},topic_group.is.null`);
    }
    const { data: articles } = await articlesQuery.limit(5);

    const ragContext =
      articles?.map((a) => `## ${a.title}\n${a.content}`).join("\n\n") ??
      "Sem artigos na base.";

    const ticketMeta = `Ticket #${ticket.ticket_number} | ${ticket.ticket_type} | ${ticket.topic_group ?? "N/A"} | conf ${ticket.confidence ?? 0}%`;

    if (mode === "draft") {
      const draft = await generateDraftReply(
        ticket.subject,
        ticket.description,
        ticket.topic_group_llm ?? ticket.topic_group ?? "Miscellaneous",
        ragContext
      );
      return NextResponse.json({ content: draft });
    }

    if (message) {
      await supabase.from("ticket_messages").insert({
        ticket_id,
        role: "customer",
        content: message,
      });
    }

    const history = (ticket.ticket_messages ?? [])
      .sort(
        (a: { created_at: string }, b: { created_at: string }) =>
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      )
      .filter((m: { role: string }) => m.role !== "system")
      .map((m: { role: string; content: string }) => ({
        role: m.role === "customer" ? ("user" as const) : ("assistant" as const),
        content: m.content,
      }));

    if (message) {
      history.push({ role: "user", content: message });
    }

    const reply = await generateChatReply(history, ragContext, ticketMeta);

    await supabase.from("ticket_messages").insert({
      ticket_id,
      role: "agent",
      content: reply,
    });

    if (ticket.status === "human_required" || ticket.status === "pending_review") {
      await supabase
        .from("tickets")
        .update({ status: "pending_customer" })
        .eq("id", ticket_id);
    }

    return NextResponse.json({ content: reply });
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Erro no chat" },
      { status: 500 }
    );
  }
}
