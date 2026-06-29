import { useState } from "react";
import LoadingScreen from "./components/LoadingScreen";
import ChatWindow from "./components/ChatWindow";
import InkFigure from "./components/InkFigure";

export default function App() {
  const [ready, setReady] = useState(false);

  return (
    <div className="app-viewport">
      <div className="side-art side-art-left" aria-hidden="true">
        <InkFigure />
      </div>

      <div className="app-shell">
        <header className="app-header">
          <div className="app-wordmark">
            <span className="app-wordmark-glyph">鑑</span>
            <span className="app-wordmark-text">Anime Oracle</span>
          </div>
          <div className={`status-dot ${ready ? "status-dot-live" : "status-dot-waking"}`}>
            <span className="status-dot-light" />
            {ready ? "live" : "waking"}
          </div>
        </header>

        <main className="app-main">
          {ready ? <ChatWindow /> : <LoadingScreen onReady={() => setReady(true)} />}
        </main>
      </div>

      <div className="side-art side-art-right" aria-hidden="true">
        <InkFigure flip />
      </div>
    </div>
  );
}
