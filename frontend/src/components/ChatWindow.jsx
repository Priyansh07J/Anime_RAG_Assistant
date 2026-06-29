import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import SuggestedPrompts from "./SuggestedPrompts";
import { sendChat, getSuggestions } from "../api";

export default function ChatWindow() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [prompts, setPrompts] = useState([]);
  const scrollRef = useRef(null);

  useEffect(() => {
    getSuggestions()
      .then((data) => setPrompts(data.prompts || []))
      .catch(() => setPrompts([]));
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isThinking]);

  async function handleSend(rawQuery) {
    const query = (rawQuery ?? input).trim();
    if (!query || isThinking) return;

    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setInput("");
    setIsThinking(true);

    // Add a placeholder assistant message that we'll fill in as tokens
    // stream in, rather than waiting for the full answer to render.
    let assistantIndex;
    setMessages((prev) => {
      assistantIndex = prev.length;
      return [...prev, { role: "assistant", content: "", sources: [], streaming: true }];
    });

    try {
      await sendChat(query, {
        onToken: (chunk) => {
          setMessages((prev) => {
            const next = [...prev];
            next[assistantIndex] = {
              ...next[assistantIndex],
              content: next[assistantIndex].content + chunk,
            };
            return next;
          });
        },
        onSources: (sources) => {
          setMessages((prev) => {
            const next = [...prev];
            next[assistantIndex] = {
              ...next[assistantIndex],
              sources,
              streaming: false,
            };
            return next;
          });
        },
      });
    } catch (err) {
      setMessages((prev) => {
        const next = [...prev];
        next[assistantIndex] = {
          role: "assistant",
          error: true,
          streaming: false,
          content:
            err.message || "Something went wrong reaching the recommendation engine. Try again.",
        };
        return next;
      });
    } finally {
      setIsThinking(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    handleSend();
  }

  return (
    <div className="chat-window">
      <div className="chat-thread" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="empty-state">
            <p className="empty-state-title">Ask for a recommendation in plain English.</p>
            <p className="empty-state-sub">
              The answer is grounded in real entries retrieved from a 600-title database —
              not guessed from memory.
            </p>
            <SuggestedPrompts prompts={prompts} onPick={(p) => handleSend(p)} />
          </div>
        )}

        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}
      </div>

      <form className="chat-input-bar" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="e.g. something like Death Note but less dark"
          aria-label="Ask for an anime recommendation"
          disabled={isThinking}
        />
        <button type="submit" disabled={isThinking || !input.trim()} aria-label="Send">
          →
        </button>
      </form>
    </div>
  );
}
