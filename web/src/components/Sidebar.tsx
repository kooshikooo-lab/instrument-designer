import { useState } from "react";

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const NAV_ITEMS = [
  {
    id: "library",
    label: "Library",
    icon: (
      <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
      </svg>
    ),
  },
  {
    id: "design",
    label: "Design",
    icon: (
      <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 2L2 7l10 5 10-5-10-5z" />
        <path d="M2 17l10 5 10-5" />
        <path d="M2 12l10 5 10-5" />
      </svg>
    ),
  },
  {
    id: "resources",
    label: "Resources",
    icon: (
      <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
        <path d="M12 17h.01" />
      </svg>
    ),
  },
];

export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`flex flex-col border-r border-neutral-800 bg-neutral-900/50 transition-all duration-200 ${
        collapsed ? "w-16" : "w-48"
      }`}
    >
      <div className="flex items-center gap-2 px-4 py-4 border-b border-neutral-800">
        <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white font-bold text-sm">
          ID
        </div>
        {!collapsed && (
          <span className="text-sm font-semibold text-neutral-200">
            Instrument Designer
          </span>
        )}
      </div>

      <nav className="flex-1 py-3">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => onTabChange(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
              activeTab === item.id
                ? "text-brand-400 bg-brand-950/50 border-r-2 border-brand-500"
                : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/50"
            }`}
          >
            {item.icon}
            {!collapsed && <span>{item.label}</span>}
          </button>
        ))}
      </nav>

      <button
        onClick={() => setCollapsed(!collapsed)}
        className="px-4 py-3 border-t border-neutral-800 text-neutral-500 hover:text-neutral-300 text-xs"
      >
        {collapsed ? "»" : "«"}
      </button>
    </aside>
  );
}
