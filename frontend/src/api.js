// Thin fetch wrapper around the FastAPI backend.
// In production this is served from the same origin (FastAPI serves the
// React build), so a relative base works for both local dev (via Vite
// proxy) and production.

const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const message = body.detail
      ? typeof body.detail === "string"
        ? body.detail
        : "Something about that request wasn't quite right."
      : `Request failed (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}

export function checkHealth() {
  return request("/health");
}

export function getSuggestions() {
  return request("/suggestions");
}

export async function sendChat(query, { onToken, onSources } = {}) {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, history: [] }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const message =
      typeof body.detail === "string" ? body.detail : `Request failed (${res.status})`;
    throw new Error(message);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  const MARKER = "__SOURCES__";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const markerIndex = buffer.indexOf(MARKER);
    if (markerIndex !== -1) {
      const textPart = buffer.slice(0, markerIndex);
      if (textPart) onToken?.(textPart);
      buffer = buffer.slice(markerIndex + MARKER.length);
      continue;
    }

    // No complete marker yet — but the buffer's tail might be the start
    // of one split across two chunks (e.g. ends in "__SOUR"). Hold back
    // a tail at least as long as the marker before flushing, so a split
    // marker can never be mistaken for answer text.
    const safeLength = Math.max(0, buffer.length - MARKER.length);
    if (onToken && safeLength > 0) {
      onToken(buffer.slice(0, safeLength));
      buffer = buffer.slice(safeLength);
    }
  }

  // Whatever's left in buffer after the stream closes is the sources JSON.
  if (buffer) {
    try {
      const parsed = JSON.parse(buffer);
      onSources?.(parsed.sources || []);
    } catch {
      onSources?.([]);
    }
  } else {
    onSources?.([]);
  }
}

export function animeImageUrl(malId) {
  // Returned as a fetch-able JSON endpoint, not a direct image URL,
  // since the backend resolves it live and caches per mal_id.
  return request(`/anime-image/${malId}`);
}
