import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface ChatRequest {
  message: string;
  session_id: string;
}
export interface ChatResponse {
  response: string;
  session_id: string;
}

export function useAgentChat() {
  return useMutation({
    mutationFn: async (body: ChatRequest) => {
      const r = await api.post<ChatResponse>("/api/v1/agent/chat", body);
      return r.data;
    },
  });
}
