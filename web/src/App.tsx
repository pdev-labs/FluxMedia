import { useEffect, useState } from "react";
import { Header } from "./components/Header.tsx";
import { Downloader } from "./components/Downloader.tsx";
import { FilesPanel } from "./components/FilesPanel.tsx";
import { LogsPanel } from "./components/LogsPanel.tsx";
import { AboutPanel } from "./components/AboutPanel.tsx";
import { tabUrl } from "./lib/session.ts";

export type Tab = "youtube" | "tiktok" | "files" | "logs" | "about";

const TABS: Tab[] = ["youtube", "tiktok", "files", "logs", "about"];

interface Route {
  tab: Tab;
  sid: string | null;
}

function parseHash(): Route {
  // Supported shapes: #/youtube, #/tiktok/s/<sid>, #/files, ...
  const parts = window.location.hash.replace(/^#\/?/, "").split("/");
  const tab = (parts[0] || "youtube") as Tab;
  const sid = parts[1] === "s" && parts[2] ? parts[2] : null;
  return { tab: TABS.includes(tab) ? tab : "youtube", sid };
}

export default function App(): React.JSX.Element {
  const [route, setRoute] = useState<Route>(() => parseHash());

  useEffect(() => {
    const onChange = (): void => setRoute(parseHash());
    window.addEventListener("hashchange", onChange);
    if (!window.location.hash) window.location.hash = tabUrl("youtube");
    return () => window.removeEventListener("hashchange", onChange);
  }, []);

  function go(tab: Tab): void {
    if (tab === route.tab && !route.sid) return;
    // Switching tabs keeps downloaders mounted (hidden), so running
    // jobs and their sessions continue untouched in the background.
    window.location.hash = tabUrl(tab);
  }

  const { tab, sid } = route;

  return (
    <>
      <Header tab={tab} onChange={go} />
      <main className="page">
        {/* Downloaders stay mounted while hidden: nav switches never
            stop a running analyze/download, and each paste keeps its
            own temporary session URL. */}
        <div hidden={tab !== "youtube"}>
          <Downloader
            source="youtube"
            initialSid={tab === "youtube" ? sid : undefined}
          />
        </div>
        <div hidden={tab !== "tiktok"}>
          <Downloader
            source="tiktok"
            initialSid={tab === "tiktok" ? sid : undefined}
          />
        </div>
        {tab === "files" && <FilesPanel />}
        {tab === "logs" && <LogsPanel />}
        {tab === "about" && <AboutPanel />}
      </main>
      <footer className="site-footer">
        <div className="site-footer-inner">
          <span>FluxMedia — local video downloader</span>
          <span>Files are saved on your machine, not uploaded anywhere.</span>
        </div>
      </footer>
    </>
  );
}
