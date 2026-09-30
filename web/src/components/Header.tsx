import type { Tab } from "../App.tsx";

const TABS: { id: Tab; label: string }[] = [
  { id: "youtube", label: "Youtube" },
  { id: "tiktok", label: "Tiktok" },
  { id: "files", label: "Files" },
  { id: "about", label: "About" },
];

export function Header({
  tab,
  onChange,
}: {
  tab: Tab;
  onChange: (t: Tab) => void;
}): React.JSX.Element {
  return (
    <header className="site-header">
      <div className="site-header-inner">
        <a className="brand" href="#" onClick={(e) => e.preventDefault()}>
          Flux <span>Media</span>
        </a>
        <nav className="nav">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={tab === t.id ? "active" : ""}
              onClick={() => onChange(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </div>
    </header>
  );
}
