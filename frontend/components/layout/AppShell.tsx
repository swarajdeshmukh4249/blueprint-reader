"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { OrganizationSwitcher, UserButton, useOrganization } from "@clerk/nextjs";

const PERSONAL_NAV = [
  { href: "/dashboard", label: "New Analysis", icon: "＋" },
  { href: "/analyses", label: "Project History", icon: "◎" },
];

const ORG_NAV = [
  { href: "/org/dashboard", label: "New Analysis", icon: "＋" },
  { href: "/org/analyses", label: "Project History", icon: "◎" },
];

const SOON_LINKS = [
  "Blueprint Chat",
  "Revision Compare",
  "Vastu Check",
  "3D Preview",
];

export default function AppShell({
  children,
  title,
  subtitle,
}: {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
}) {
  const pathname = usePathname();
  const { organization } = useOrganization();
  const base = organization ? "/org" : "";
  const nav = organization ? ORG_NAV : PERSONAL_NAV;
  const home = `${base}/dashboard`;

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <Link href={home} className="nav-brand">
          <span className="nav-brand-mark">BR</span>
          <span>
            <div className="nav-brand-title">Blueprint Reader</div>
            <div className="nav-brand-sub">Indian BOQ Platform</div>
          </span>
        </Link>

        <nav style={{ flex: 1, paddingTop: 8 }}>
          <div className="nav-section-label">Workspace</div>
          {nav.map((item) => {
            const active =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-link ${active ? "active" : ""}`}
              >
                <span style={{ opacity: 0.7 }}>{item.icon}</span>
                {item.label}
              </Link>
            );
          })}

          <div className="nav-section-label">Coming soon</div>
          {SOON_LINKS.map((label) => (
            <div
              key={label}
              className="nav-link"
              style={{ opacity: 0.45, cursor: "default", pointerEvents: "none" }}
            >
              {label}
              <span className="badge badge-muted" style={{ marginLeft: "auto", fontSize: 9 }}>
                Soon
              </span>
            </div>
          ))}
        </nav>

        <div style={{ padding: 12, borderTop: "1px solid var(--border)" }}>
          <OrganizationSwitcher
            hidePersonal={false}
            afterCreateOrganizationUrl="/org/dashboard"
            afterSelectOrganizationUrl="/org/dashboard"
            afterSelectPersonalUrl="/dashboard"
            afterLeaveOrganizationUrl="/dashboard"
          />
        </div>
      </aside>

      <div className="app-main">
        <header className="app-header">
          <div>
            {title && <h1 style={{ fontSize: 18, fontWeight: 700 }}>{title}</h1>}
            {subtitle && (
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                {subtitle}
              </p>
            )}
          </div>
          <UserButton afterSignOutUrl="/" />
        </header>
        <main className="app-content">{children}</main>
      </div>
    </div>
  );
}
