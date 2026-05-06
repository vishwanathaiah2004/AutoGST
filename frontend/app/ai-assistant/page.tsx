"use client";
import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import toast from "react-hot-toast";
import { Send, Bot, User, Sparkles, RefreshCw } from "lucide-react";
import clsx from "clsx";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  return (
    <div className={clsx("flex gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
      <div className={clsx(
        "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1",
        isUser ? "bg-indigo-600" : "bg-slate-700"
      )}>
        {isUser ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-white" />}
      </div>
      <div className={clsx(
        "max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
        isUser
          ? "bg-indigo-600 text-white rounded-tr-sm"
          : "bg-white border border-slate-200 text-slate-800 rounded-tl-sm shadow-sm"
      )}>
        {msg.content.split("\n").map((line, i) => {
          const formatted = line
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\*(.*?)\*/g, "<em>$1</em>");
          return (
            <p
              key={i}
              className={line === "" ? "h-2" : ""}
              dangerouslySetInnerHTML={{ __html: formatted }}
            />
          );
        })}
        <p className="text-xs mt-1.5 opacity-60">
          {msg.timestamp.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
        </p>
      </div>
    </div>
  );
}

export default function AIAssistantPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "👋 Hi! I'm **AutoGST AI**, your expert assistant for Indian GST and income tax queries.\n\nI can help you with:\n- GST rates, ITC claims, and filing deadlines\n- Income tax slabs and deduction planning\n- GSTR-1, GSTR-3B guidance\n- HSN/SAC codes and compliance\n\nWhat would you like to know?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text?: string) => {
    const messageText = text || input.trim();
    if (!messageText || loading) return;

    const userMsg: Message = { role: "user", content: messageText, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }));
      const res = await api.post("/ai/chat", { message: messageText, history });
      const assistantMsg: Message = {
        role: "assistant",
        content: res.data.reply,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || "AI service unavailable. Please set GEMINI_API_KEY in backend .env";
      toast.error(errMsg, { duration: 5000 });
      setMessages(prev => [...prev, {
        role: "assistant",
        content: `⚠️ ${errMsg}`,
        timestamp: new Date(),
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([{
      role: "assistant",
      content: "Chat cleared. How can I help you with GST or tax queries?",
      timestamp: new Date(),
    }]);
  };

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 5rem)' }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl lg:text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-500" />
            AI Tax Assistant
          </h1>
          <p className="text-slate-500 text-xs lg:text-sm mt-1">
            Powered by Google Gemini · Ask anything about GST, income tax, and compliance
          </p>
        </div>
        <button onClick={clearChat} className="btn-secondary flex items-center gap-2 text-sm">
          <RefreshCw className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Clear Chat</span>
        </button>
      </div>

      {/* Chat Window — full width, fills remaining height */}
      <div className="flex-1 flex flex-col card overflow-hidden min-h-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, i) => (
            <MessageBubble key={i} msg={msg} />
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                <div className="flex gap-1 items-center h-5">
                  {[0, 1, 2].map(i => (
                    <div
                      key={i}
                      className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="border-t border-slate-100 p-3">
          <div className="flex gap-2 items-end">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about GST rates, ITC, tax filing, deductions…"
              rows={2}
              className="flex-1 resize-none border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              disabled={loading}
            />
            <button
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              className="btn-primary p-2.5 rounded-xl disabled:opacity-40"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-slate-400 mt-1.5 px-1">
            Shift+Enter for new line · Enter to send
          </p>
        </div>
      </div>
    </div>
  );
} 