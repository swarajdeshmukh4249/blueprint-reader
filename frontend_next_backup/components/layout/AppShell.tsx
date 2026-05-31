"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { OrganizationSwitcher, UserButton, useOrganization } from "@clerk/nextjs";
import BlueprintGrid from "@/components/graphics/BlueprintGrid";

const PERSONAL_NAV = [
  { href: "/dashboard", label: "New Analysis", icon: "◇" },
  { href: "/analyses", label: "Project History", icon: "◎" },
];

const ORG_NAV = [
  { href: "/org/dashboard", label: "New Analysis", icon: "◇" },
  { href: "/org/analyses", label: "Project History", icon: "◎" },
];

const PHASE3_NAV = [
  { href: "/dashboard/chat", label: "Blueprint Chat", icon: "◈", orgHref: "/org/dashboard/chat" },
  { href: "/dashboard/revisions", label: "Revision Compare", icon: "⇄", orgHref: "/org/dashboard/revisions" },
];

const SOON_LINKS = ["Vastu Check", "3D Preview"];

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
        <div className="sidebar-grid-deco">
          <BlueprintGrid opacity={0.5} />
        </div>

        <Link href={home} className="nav-brand">
          <span className="nav-brand-mark">BR</span>
          <span>
            <div className="nav-brand-title">Blueprint Reader</div>
            <div className="nav-brand-sub">Quant · DSR · India</div>
          </span>
        </Link>

        <div className="sidebar-status">
          <strong>Analysis engine</strong>
          <br />
          CAD-first extraction · GST-ready BOQ
        </div>

        <nav style={{ flex: 1, paddingTop: 4 }}>
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
                <span style={{ fontFamily: "var(--font-mono)", opacity: 0.85 }}>{item.icon}</span>
                {item.label}
              </Link>
            );
          })}

          <div className="nav-section-label">Phase 3</div>
          {PHASE3_NAV.map((item) => {
            const href = organization ? item.orgHref : item.href;
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                key={href}
                href={href}
                className={`nav-link ${active ? "active" : ""}`}
              >
                <span style={{ fontFamily: "var(--font-mono)", opacity: 0.85 }}>{item.icon}</span>
                {item.label}
                <span className="badge badge-coral" style={{ marginLeft: "auto", fontSize: 8 }}>
                  Beta
                </span>
              </Link>
            );
          })}

          <div className="nav-section-label">Roadmap</div>
          {SOON_LINKS.map((label) => (
            <div
              key={label}
              className="nav-link"
              style={{ opacity: 0.35, cursor: "default", pointerEvents: "none" }}
            >
              {label}
              <span className="badge badge-muted" style={{ marginLeft: "auto", fontSize: 8, opacity: 0.7 }}>
                Soon
              </span>
            </div>
          ))}
        </nav>

        <div style={{ padding: 14, borderTop: "1px solid rgba(255,255,255,0.08)", position: "relative", zIndex: 1 }}>
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
            {title && (
              <h1 style={{ fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 700, letterSpacing: "-0.02em" }}>
                {title}
              </h1>
            )}
            {subtitle && (
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>{subtitle}</p>
            )}
          </div>
          <UserButton afterSignOutUrl="/" />
        </header>
        <main className="app-content">{children}</main>
      </div>
    </div>
  );
}
