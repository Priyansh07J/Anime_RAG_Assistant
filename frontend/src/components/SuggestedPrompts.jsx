// Clickable example queries shown on the empty state, so a first-time
// visitor isn't staring at a blank input box.

export default function SuggestedPrompts({ prompts, onPick }) {
  if (!prompts?.length) return null;

  return (
    <div className="suggested-prompts">
      {prompts.map((p) => (
        <button
          key={p}
          type="button"
          className="prompt-chip"
          onClick={() => onPick(p)}
        >
          {p}
        </button>
      ))}
    </div>
  );
}
