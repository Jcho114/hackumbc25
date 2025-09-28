import { useState, useRef, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useParams } from "react-router-dom";

type Message = {
  role: "user" | "assistant" | "system";
  text: string;
  type?: "text" | "mcp_call" | "mcp_result";
};

const Chat = () => {
  const { sessionId } = useParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (prompt: string) => {
    if (!prompt.trim()) return;

    setMessages((prev) => [...prev, { role: "user", text: prompt }]);
    setInput("");
    setLoading(true);

    abortControllerRef.current = new AbortController();

    // Build full history string for the assistant
    const fullHistory = [...messages, { role: "user", text: prompt }]
      .map((m) => `${m.role.toUpperCase()}: ${m.text}`)
      .join("\n");

    try {
      const res = await fetch(
        `http://localhost:8000/gemini?session_id=${sessionId}&prompt=${encodeURIComponent(
          fullHistory
        )}`,
        { method: "POST", signal: abortControllerRef.current.signal }
      );

      if (!res.body) throw new Error("No stream returned");

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let assistantText = "";

      // Add placeholder assistant message
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "", type: "text" },
      ]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });

        chunk.split("\n").forEach((line) => {
          if (line.startsWith("TEXT::")) {
            assistantText += line.replace("TEXT::", "");
            setMessages((prev) => {
              if (prev.length === 0) return prev;
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last.role === "assistant") {
                updated[updated.length - 1] = {
                  ...last,
                  text: assistantText,
                };
              } else {
                updated.push({
                  role: "assistant",
                  text: assistantText,
                  type: "text",
                });
              }
              return updated;
            });
          } else if (line.startsWith("MCP_CALL::")) {
            const toolName = line.replace("MCP_CALL::", "");
            setMessages((prev) => [
              ...prev,
              {
                role: "system",
                text: `🔧 Called MCP: ${toolName}`,
                type: "mcp_call",
              },
            ]);
          } else if (line.startsWith("MCP_RESULT::")) {
            const result = line.replace("MCP_RESULT::", "");
            setMessages((prev) => [
              ...prev,
              {
                role: "system",
                text: `📥 MCP result: ${result}`,
                type: "mcp_result",
              },
            ]);
          }
        });
      }
    } catch (err) {
      console.error("Streaming error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="absolute w-1/4 h-[95%] m-4 z-10 p-4 flex flex-col gap-2">
      <div className="w-fit">
        <h1 className="text-l font-bold text-center">CHAT</h1>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-2 text-sm mb-2 p-2 border rounded-md">
        {messages.map((msg, i) => {
          let className = "text-left";

          if (msg.role === "user") className = "text-right text-blue-600";
          else if (msg.type === "text") className = "text-left text-gray-800";
          else if (msg.type === "mcp_call")
            className = "text-left text-sm italic text-yellow-600";
          else if (msg.type === "mcp_result")
            className = "text-left text-sm italic text-green-600";

          return (
            <div key={i} className={className}>
              {msg.text}
            </div>
          );
        })}
        <div ref={chatEndRef} />
      </div>

      {/* Input as a form */}
      <form
        className="w-full"
        onSubmit={(e) => {
          e.preventDefault();
          handleSend(input);
        }}
      >
        <Textarea
          className="w-full border-gray-200 border-[1.5px] rounded-md h-[5rem] p-2 text-sm resize-none"
          placeholder="Ask anything here"
          value={input}
          disabled={loading}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend(input);
            }
          }}
        />
      </form>
    </Card>
  );
};

export default Chat;
