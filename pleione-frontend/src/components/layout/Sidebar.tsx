"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  {
    name: "Command Center",
    href: "/",
    icon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
      >
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </svg>
    ),
  },
  {
    name: "Components",
    href: "/components",
    icon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
      >
        <path d="M12 3 4.5 7.2v9.6L12 21l7.5-4.2V7.2L12 3Z" />
        <path d="m4.8 7.4 7.2 4 7.2-4" />
        <path d="M12 11.4V21" />
      </svg>
    ),
  },
  {
    name: "Anomalies",
    href: "/anomalies",
    icon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
      >
        <path d="M12 3 21 20H3L12 3Z" />
        <path d="M12 9v5" />
        <path d="M12 17h.01" />
      </svg>
    ),
  },
  {
    name: "Lots",
    href: "/lots",
    icon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
      >
        <path d="M4 6h16" />
        <path d="M4 12h16" />
        <path d="M4 18h16" />
        <circle cx="8" cy="6" r="1.5" />
        <circle cx="16" cy="12" r="1.5" />
        <circle cx="10" cy="18" r="1.5" />
      </svg>
    ),
  },
  {
    name: "Screening Run",
    href: "/screening-runs",
    icon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
      >
        <path d="M6 4h12v16H6z" />
        <path d="M9 8h6" />
        <path d="M9 12h6" />
        <path d="M9 16h3" />
      </svg>
    ),
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-50 flex w-[248px] flex-col border-r border-slate-200 bg-white text-slate-900 transition-colors duration-200 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100">
      {/* Brand */}
      <div className="flex h-16 shrink-0 items-center border-b border-slate-200 px-6 dark:border-slate-800">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md border border-slate-300 bg-slate-100 dark:border-slate-700 dark:bg-slate-900">
            <span className="text-sm font-semibold tracking-tight text-slate-900 dark:text-slate-100">
              P
            </span>
          </div>

          <div>
            <p className="text-[15px] font-semibold tracking-tight text-slate-950 dark:text-white">
              PLEIONE
            </p>
            <p className="mt-0.5 text-[10px] uppercase tracking-[0.18em] text-slate-500 dark:text-slate-500">
              Reliability Intelligence
            </p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <div className="flex-1 px-3 py-6">
        <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">
          Workspace
        </p>

        <nav className="space-y-1">
          {navigation.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`group flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors ${
                  isActive
                    ? "bg-slate-100 font-medium text-slate-950 dark:bg-slate-900 dark:text-white"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-950 dark:text-slate-400 dark:hover:bg-slate-900/70 dark:hover:text-slate-100"
                }`}
              >
                <span
                  className={`h-[17px] w-[17px] shrink-0 ${
                    isActive
                      ? "text-slate-900 dark:text-slate-100"
                      : "text-slate-400 group-hover:text-slate-700 dark:text-slate-500 dark:group-hover:text-slate-300"
                  }`}
                >
                  {item.icon}
                </span>

                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Backend status */}
      <div className="shrink-0 border-t border-slate-200 p-4 dark:border-slate-800">
        <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-3 dark:border-slate-800 dark:bg-slate-900/50">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-50" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
            </span>

            <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
              Screening Engine
            </span>
          </div>

          <p className="mt-1.5 pl-4 text-[11px] text-slate-500 dark:text-slate-500">
            FastAPI screening services
          </p>
        </div>
      </div>
    </aside>
  );
}
