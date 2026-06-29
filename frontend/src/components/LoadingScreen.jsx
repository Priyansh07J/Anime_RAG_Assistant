import { useEffect, useState, useRef } from "react";

// The signature moment: instead of a generic spinner, an ink stamp
// "presses" onto parchment while honest status lines rotate underneath.
// Render's free tier sleeps after inactivity, so a cold visit can take
// 30-60s to wake up — rather than hide that, we name it directly.

const STATUS_LINES = [
  "Waking the retrieval engine…",
  "Loading 600 titles into memory…",
  "Warming up the language model…",
  "Free tier, so this takes a minute or two 😅",
  "Almost there — vector search is spinning up…",
];

export default function LoadingScreen({ onReady }) {
  const [lineIndex, setLineIndex] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const pollRef = useRef(null);
  const tickRef = useRef(null);

  useEffect(() => {
    tickRef.current = setInterval(() => {
      setElapsed((s) => s + 1);
    }, 1000);

    const rotateLines = setInterval(() => {
      setLineIndex((i) => (i + 1) % STATUS_LINES.length);
    }, 2600);

    let cancelled = false;

    async function poll() {
      try {
        const res = await fetch("/api/health", { cache: "no-store" });
        if (res.ok && !cancelled) {
          onReady();
          return;
        }
      } catch {
        // server still asleep / connection refused — keep polling
      }
      if (!cancelled) {
        pollRef.current = setTimeout(poll, 2000);
      }
    }
    poll();

    return () => {
      cancelled = true;
      clearInterval(rotateLines);
      clearInterval(tickRef.current);
      clearTimeout(pollRef.current);
    };
  }, [onReady]);

  return (
    <div className="loading-screen" role="status" aria-live="polite">
      <div className="stamp-wrap">
        <svg
          className="stamp-seal"
          viewBox="0 0 160 160"
          width="120"
          height="120"
          aria-hidden="true"
        >
          <circle cx="80" cy="80" r="70" className="stamp-ring" />
          <circle cx="80" cy="80" r="58" className="stamp-ring-inner" />
          <text x="80" y="72" textAnchor="middle" className="stamp-glyph">
            鑑
          </text>
          <text x="80" y="98" textAnchor="middle" className="stamp-subtext">
            ANIME ORACLE
          </text>
        </svg>
      </div>

      <p className="loading-line" key={lineIndex}>
        {STATUS_LINES[lineIndex]}
      </p>

      <p className="loading-elapsed">{elapsed}s elapsed</p>
    </div>
  );
}
