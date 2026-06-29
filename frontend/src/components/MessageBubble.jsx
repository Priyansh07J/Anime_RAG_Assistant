import AnimeCard from "./AnimeCard";

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";
  const isPending = message.streaming && !message.content;

  return (
    <div className={`message-row ${isUser ? "message-row-user" : ""}`}>
      <div className={`message-bubble ${isUser ? "message-bubble-user" : "message-bubble-assistant"}`}>
        {isPending ? (
          <span className="thinking-dots" aria-label="Thinking">
            <span className="thinking-dot" />
            <span className="thinking-dot" />
            <span className="thinking-dot" />
          </span>
        ) : message.error ? (
          <p className="message-error">{message.content}</p>
        ) : (
          <p>
            {message.content}
            {message.streaming && <span className="caret" aria-hidden="true" />}
          </p>
        )}
      </div>

      {!isUser && message.sources?.length > 0 && (
        <div className="sources-block">
          <div className="sources-label">
            grounded in {message.sources.length} source{message.sources.length > 1 ? "s" : ""}
          </div>
          <div className="sources-scroll">
            {message.sources.map((s) => (
              <AnimeCard key={s.mal_id ?? s.title} source={s} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
