"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLanguage } from "@/components/LanguageContext";

const NAV_ITEMS = [
  { href: "/papers", icon: "📱", labelKey: "nav.papers" },
  { href: "/favorites", icon: "⭐", labelKey: "nav.favorites" },
  { href: "/settings", icon: "⚙️", labelKey: "nav.settings" },
];

export default function NavBar() {
  const pathname = usePathname();
  const { t } = useLanguage();

  return (
    <nav className="flex-shrink-0 flex border-t border-[var(--border)] bg-[var(--bg-secondary)]">
      {NAV_ITEMS.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex-1 flex flex-col items-center py-2 lg:py-3 text-xs lg:text-sm transition-colors ${
              isActive
                ? "text-[var(--accent-blue)]"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
          >
            <span className="text-base lg:text-lg">{item.icon}</span>
            <span className="mt-0.5">{t(item.labelKey)}</span>
          </Link>
        );
      })}
    </nav>
  );
}
