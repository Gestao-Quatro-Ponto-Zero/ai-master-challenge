import { useQuery, useMutation } from "@tanstack/react-query";
import { queryClient, apiRequest } from "@/lib/queryClient";
import type { Ticket } from "@shared/schema";

export function useTickets(status?: string) {
  return useQuery<Ticket[]>({
    queryKey: ["/api/tickets", status],
    queryFn: () => fetch(`/api/tickets${status ? `?status=${status}` : ""}`, { credentials: "include" }).then(r => r.json()),
  });
}

export function useMyTickets() {
  return useQuery<Ticket[]>({
    queryKey: ["/api/tickets/mine"],
    queryFn: () => fetch("/api/tickets/mine", { credentials: "include" }).then(r => r.json()),
  });
}

export function useTicket(id: number) {
  return useQuery<Ticket>({
    queryKey: ["/api/tickets", id],
    queryFn: () => fetch(`/api/tickets/${id}`, { credentials: "include" }).then(r => r.json()),
    enabled: !!id,
  });
}

export function useCreateTicket() {
  return useMutation({
    mutationFn: (data: any) => apiRequest("POST", "/api/tickets", data).then(r => r.json()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/tickets"] });
      queryClient.invalidateQueries({ queryKey: ["/api/tickets/mine"] });
    },
  });
}

export function useUpdateTicket() {
  return useMutation({
    mutationFn: ({ id, ...data }: any) => apiRequest("PATCH", `/api/tickets/${id}`, data).then(r => r.json()),
    onSuccess: (_data: any, vars: any) => {
      queryClient.invalidateQueries({ queryKey: ["/api/tickets", vars.id] });
      queryClient.invalidateQueries({ queryKey: ["/api/tickets"] });
    },
  });
}

export function useClassifyTicket() {
  return useMutation({
    mutationFn: (description: string) => apiRequest("POST", "/api/tickets/classify", { description }).then(r => r.json()),
  });
}

export function useSuggestResponse() {
  return useMutation({
    mutationFn: (id: number) => apiRequest("POST", `/api/tickets/${id}/suggest-response`, {}).then(r => r.json()),
  });
}

export function useTicketMessages(ticketId: number) {
  return useQuery({
    queryKey: ["/api/tickets", ticketId, "messages"],
    queryFn: () => fetch(`/api/tickets/${ticketId}/messages`, { credentials: "include" }).then(r => r.json()),
    enabled: !!ticketId,
    refetchInterval: 5000,
  });
}

export function useSendTicketMessage() {
  return useMutation({
    mutationFn: ({ ticketId, message }: { ticketId: number; message: string }) =>
      apiRequest("POST", `/api/tickets/${ticketId}/messages`, { message }).then(r => r.json()),
    onSuccess: (_data: any, vars: any) => {
      queryClient.invalidateQueries({ queryKey: ["/api/tickets", vars.ticketId, "messages"] });
    },
  });
}
