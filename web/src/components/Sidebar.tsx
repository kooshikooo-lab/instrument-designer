import type { Tab } from "../App";
import { isTauri } from "../utils/tauri";

interface SidebarProps {
  active: Tab;
  onNavigate: (tab: Tab) => void;
  collapsed: boolean;
  onToggleCollapsed: () => void;
}

const NAV: { id: Tab; label: string; icon: string }[] = [
  { id: "library", label: "Library", icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" },
  { id: "design", label: "Design", icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z" },
  { id: "resources", label: "Resources", icon: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" },
  { id: "wiki", label: "Wiki", icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" },
];

/**
 * Left navigation sidebar with Library, Design, and Resources tabs.
 */
export function Sidebar({ active, onNavigate, collapsed, onToggleCollapsed }: SidebarProps) {
  const desktop = isTauri();

  return (
    <aside className={`${collapsed ? "w-16" : "w-56"} bg-neutral-900 border-r border-neutral-800 flex flex-col transition-[width] duration-200`}>
      <div className="p-4 border-b border-neutral-800">
        <div className="flex items-start justify-between gap-2">
          <div className={collapsed ? "sr-only" : ""}>
            <div className="text-brand-400 font-bold text-sm tracking-wider uppercase">Instrument Designer</div>
            <div className="text-neutral-500 text-xs mt-0.5">
              {desktop ? "Desktop App" : "Pure Web App"}
            </div>
          </div>
          <button
            type="button"
            onClick={onToggleCollapsed}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-neutral-400 hover:bg-neutral-800 hover:text-neutral-200 transition-colors"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <svg className={`h-4 w-4 transition-transform ${collapsed ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        </div>
      </div>
      <nav className="flex-1 p-2 space-y-0.5">
        {NAV.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`w-full flex items-center ${collapsed ? "justify-center" : "gap-3"} px-3 py-2.5 rounded-lg text-sm transition-colors ${
              active === item.id
                ? "bg-brand-600/20 text-brand-400"
                : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800"
            }`}
            aria-label={item.label}
            title={item.label}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
            </svg>
            {!collapsed && item.label}
          </button>
        ))}
      </nav>
      <div className="p-3 border-t border-neutral-800">
        <div className={`text-xs text-neutral-600 ${collapsed ? "hidden" : ""}`}>
          {desktop ? "Tauri + React + Three.js" : "Built with React + Three.js + JSCAD"}
        </div>
      </div>
    </aside>
  );
}
