/** Minimal line icons — AutoCAD-style 16–20px glyphs */

import type { ReactNode } from "react";

type IconProps = { size?: number; className?: string };

const S = ({ size = 20, children }: { size?: number; children: ReactNode }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    {children}
  </svg>
);

export function IconOpen({ size }: IconProps) {
  return (
    <S size={size}>
      <path d="M4 4h16v16H4z" /><path d="M8 12h8M12 8v8" />
    </S>
  );
}

export function IconAnalyze({ size }: IconProps) {
  return (
    <S size={size}>
      <circle cx="11" cy="11" r="7" /><path d="M16 16l5 5" />
    </S>
  );
}

export function IconExport({ size }: IconProps) {
  return (
    <S size={size}>
      <path d="M12 3v12M8 11l4 4 4-4" /><path d="M4 19h16" />
    </S>
  );
}

export function IconRoom({ size }: IconProps) {
  return (
    <S size={size}>
      <rect x="3" y="3" width="18" height="18" rx="1" /><path d="M3 12h18M12 3v18" />
    </S>
  );
}

export function IconWall({ size }: IconProps) {
  return (
    <S size={size}>
      <path d="M4 20V8l8-5 8 5v12" /><path d="M4 12h16" />
    </S>
  );
}

export function IconLayer({ size }: IconProps) {
  return (
    <S size={size}>
      <path d="M12 2L2 7l10 5 10-5-10-5z" /><path d="M2 12l10 5 10-5M2 17l10 5 10-5" />
    </S>
  );
}

export function IconChat({ size }: IconProps) {
  return (
    <S size={size}>
      <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" />
    </S>
  );
}

export function Icon3D({ size }: IconProps) {
  return (
    <S size={size}>
      <path d="M12 2l9 5v10l-9 5-9-5V7l9-5z" /><path d="M12 12l9-5M12 12v10M12 12L3 7" />
    </S>
  );
}

export function IconGrid({ size }: IconProps) {
  return (
    <S size={size}>
      <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" />
    </S>
  );
}

export function IconDxf({ size }: IconProps) {
  return (
    <S size={size}>
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
      <path d="M14 2v6h6" /><path d="M8 13h8M8 17h5" />
    </S>
  );
}
