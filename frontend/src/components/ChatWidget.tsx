import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { MessageCircle, Send, X, Sparkles } from "lucide-react";
import { useAgentChat } from "@/api/agent";
import { Button } from "@/components/ui/Button";

interface Msg {
  role: "user" | "assistant";
  content: string;
}

function newSessionId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `s_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: "assistant",
      content: "Hi! I'm Stayfinder's AI concierge. Ask me about hotels — e.g., 'Find me a hotel in Rome for 2 guests next weekend'.",
    },
  ]);
  const [sessionId] = useState(newSessionId);
  const chat = useAgentChat();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, open]);

  async function send() {
    const text = input.trim();
    if (!text || chat.isPending) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    try {
      const r = await chat.mutateAsync({ message: text, session_id: sessionId });
      setMessages((m) => [...m, { role: "assistant", content: r.response }]);
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Sorry, I couldn't process that. Please try again." },
      ]);
    }
  }

  return (
    <>
      <button
        onClick={() => setOpen((o) => !o)}
        className="fixed bottom-6 right-6 z-50 h-14 w-14 rounded-full bg-accent hover:bg-accent-dark text-white shadow-lg shadow-accent/30 grid place-items-center transition-transform hover:scale-105"
        aria-label="Open chat"
      >
        {open ? <X className="h-6 w-6" /> : <MessageCircle className="h-6 w-6" />}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.18 }}
            className="fixed bottom-24 right-6 z-50 w-[92vw] max-w-sm rounded-2xl bg-white shadow-2xl border border-slate-200 overflow-hidden flex flex-col"
            style={{ maxHeight: "70vh" }}
          >
            <div className="bg-gradient-to-r from-brand-700 to-brand-500 p-4 text-white">
              <p className="flex items-center gap-2 font-bold">
                <Sparkles className="h-4 w-4" /> Stayfinder AI
              </p>
              <p className="text-xs text-brand-100">Powered by Llama 3.3 via Groq</p>
            </div>

            <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={
                    "max-w-[85%] rounded-2xl px-3 py-2 text-sm whitespace-pre-wrap " +
                    (m.role === "user"
                      ? "bg-brand-600 text-white ml-auto rounded-br-sm"
                      : "bg-slate-100 text-slate-800 rounded-bl-sm")
                  }
                >
                  {m.content}
                </div>
              ))}
              {chat.isPending && (
                <div className="bg-slate-100 text-slate-500 rounded-2xl px-3 py-2 text-sm w-fit rounded-bl-sm">
                  <span className="inline-block animate-pulse">…thinking</span>
                </div>
              )}
            </div>

            <div className="border-t border-slate-200 p-2 flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send();
                  }
                }}
                placeholder="Ask about hotels…"
                className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
              <Button size="md" onClick={send} loading={chat.isPending} disabled={!input.trim()}>
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
