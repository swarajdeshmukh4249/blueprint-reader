"use client";

import { UserButton, OrganizationSwitcher, useOrganization, useUser } from "@clerk/nextjs";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const { organization } = useOrganization();
  const { user } = useUser();
  const pathname = usePathname();

  const base = organization ? "/org" : "";
  const navLinks = [
    { href: `${base}/dashboard`, label: "Workspace" },
    { href: `${base}/analyses`, label: "Project Manager" },
  ];

  const isActive = (href: string) => pathname === href;

  return (
    <header className="cad-titlebar" style={{ position: "sticky", top: 0, zIndex: 50 }}>
      <Link
        href={organization ? "/org/dashboard" : "/dashboard"}
        className="cad-titlebar-app"
        style={{ textDecoration: "none", color: "inherit" }}
      >
        <span
          style={{
            width: 16,
            height: 16,
            background: "var(--cad-accent)",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 9,
            fontWeight: 800,
            color: "#fff",
          }}
        >
          B
        </span>
        Blueprint<span className="accent">Reader</span>
        <span style={{ color: "var(--cad-text-dim)", fontWeight: 400, marginLeft: 4 }}>2026</span>
      </Link>

      <nav style={{ display: "flex", gap: 2, flex: 1 }}>
        {navLinks.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            style={{
              padding: "2px 12px",
              fontSize: 12,
              textDecoration: "none",
              color: isActive(link.href) ? "var(--cad-text-bright)" : "var(--cad-text-dim)",
              background: isActive(link.href) ? "var(--cad-bg-hover)" : "transparent",
              borderRadius: 2,
            }}
          >
            {link.label}
          </Link>
        ))}
      </nav>

      <div style={{ display: "flex", alignItems: "center", gap: 10, marginLeft: "auto" }}>
        <span
          style={{
            fontSize: 11,
            fontFamily: "var(--font-mono-cad)",
            color: "var(--cad-text-dim)",
            padding: "0 8px",
            borderRight: "1px solid var(--cad-border)",
          }}
        >
          {organization ? organization.name : user?.firstName ?? "Personal"}
        </span>
        <OrganizationSwitcher
          hidePersonal={false}
          afterCreateOrganizationUrl="/org/dashboard"
          afterSelectOrganizationUrl="/org/dashboard"
          afterSelectPersonalUrl="/dashboard"
          afterLeaveOrganizationUrl="/dashboard"
        />
        <UserButton afterSignOutUrl="/" />
      </div>
    </header>
  );
}
