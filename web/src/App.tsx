import { useState } from "react";
import { Header } from "./components/Header.tsx";
import { Downloader } from "./components/Downloader.tsx";
import { FilesPanel } from "./components/FilesPanel.tsx";
import { AboutPanel } from "./components/AboutPanel.tsx";

export type Tab = "youtube" | "tiktok" | "files" | "about";

export default function App(): React.JSX.Element {
  const [tab, setTab] = useState<Tab>("youtube");

  return (
    <>
      <Header tab={tab} onChange={setTab} />
      <main className="page">
        {(tab === "youtube" || tab === "tiktok") && (
          <Downloader key={tab} source={tab} />
        )}
        {tab === "files" && <FilesPanel />}
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
